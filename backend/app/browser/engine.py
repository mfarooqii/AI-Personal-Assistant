"""
Browser Engine — stealth Chromium automation via patchright (or Playwright).

Two operating modes — auto-detected at first launch:

  1. Electron mode  →  Aria is running as a desktop app.
     All browser commands are forwarded to the Electron IPC bridge which
     executes them on the *real*, user-visible BrowserView.  Zero headless
     footprint, zero bot detection, user watches every action live.

  2. Standalone mode  →  Aria is running as a plain web app.
     Uses patchright (a stealth-patched Playwright fork) with a persistent
     Chromium profile so sessions/cookies survive restarts.

Both modes expose the same public API so the BrowserAgent never needs to
know which mode is active.
"""

import asyncio
import base64
import logging
from pathlib import Path
from typing import Optional

from app.config import settings

log = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────

BROWSER_DATA_DIR = settings.DATA_DIR / "browser_data"
VIEWPORT = {"width": 1280, "height": 720}
SCREENSHOT_QUALITY = 50            # JPEG quality (lower = smaller)
NAV_TIMEOUT = 30_000               # ms
DEFAULT_WAIT = 1_000               # ms after an action


# ── JS snippet injected into pages to extract interactive elements ──

_EXTRACT_ELEMENTS_JS = """
() => {
    const items = [];
    const sel = 'a, button, input, textarea, select, [role="button"], '
              + '[role="link"], [role="tab"], [role="menuitem"], '
              + '[role="option"], [role="checkbox"], [role="radio"], '
              + '[contenteditable="true"]';
    const nodes = document.querySelectorAll(sel);
    let idx = 1;
    for (const n of nodes) {
        const r = n.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) continue;
        if (r.bottom < 0 || r.top > window.innerHeight) continue;
        const style = window.getComputedStyle(n);
        if (style.display === 'none' || style.visibility === 'hidden') continue;

        const text = (n.innerText || n.textContent || '').trim().substring(0, 120);
        const tag  = n.tagName.toLowerCase();
        const role = n.getAttribute('role') || tag;
        items.push({
            id:   idx++,
            tag,
            role,
            text: text || n.getAttribute('aria-label')
                       || n.getAttribute('placeholder')
                       || n.getAttribute('title')
                       || n.getAttribute('name')
                       || '',
            x: Math.round(r.x + r.width  / 2),
            y: Math.round(r.y + r.height / 2),
            href:        n.getAttribute('href'),
            input_type:  n.getAttribute('type'),
            value:       n.value || '',
            placeholder: n.getAttribute('placeholder') || '',
            checked:     !!n.checked,
            disabled:    !!n.disabled,
        });
    }
    return {
        elements: items,
        url:   location.href,
        title: document.title,
        text:  document.body?.innerText?.substring(0, 4000) || '',
    };
}
"""


class BrowserEngine:
    """
    Thin async wrapper around a single persistent Playwright browser context.

    Usage::

        engine = BrowserEngine()
        await engine.launch()
        await engine.navigate("https://gmail.com")
        state = await engine.get_page_state()
        shot  = await engine.screenshot()
        await engine.close()
    """

    def __init__(self) -> None:
        self._playwright    = None
        self._context       = None
        self._page          = None
        self._launched      = False
        self._electron_mode = False  # True when delegating to Electron BrowserView

    # ── lifecycle ─────────────────────────────────────────

    async def launch(self) -> None:
        """
        Start the browser.

        If the Electron IPC bridge is available (desktop app mode), the engine
        delegates all actions to the live BrowserView — no headless instance
        is started here.  Otherwise, patchright is launched with a persistent
        profile (stealth-patched Chromium, no bot-detection flags).
        """
        if self._launched:
            return

        # ── Check for Electron desktop mode first ──────────────────────────
        from app.browser import electron_bridge  # local import to avoid circular deps
        if await electron_bridge.is_available():
            self._electron_mode = True
            self._launched = True
            log.info("BrowserEngine: Electron mode — using live BrowserView")
            return

        # ── Standalone mode: stealth Chromium via patchright ───────────────
        self._electron_mode = False

        try:
            from patchright.async_api import async_playwright
        except ImportError:
            # Graceful fallback to plain playwright if patchright not installed
            log.warning("patchright not installed — falling back to playwright (may be detected as bot)")
            from playwright.async_api import async_playwright

        BROWSER_DATA_DIR.mkdir(parents=True, exist_ok=True)

        self._playwright = await async_playwright().start()
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_DATA_DIR),
            headless=True,
            viewport=VIEWPORT,
            locale="en-US",
            timezone_id="America/New_York",
            # patchright handles most stealth patches automatically;
            # these args add an extra layer of compatibility
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()

        self._page.set_default_navigation_timeout(NAV_TIMEOUT)
        self._launched = True
        log.info("BrowserEngine: standalone mode (patchright)")

    async def close(self) -> None:
        """Shut down browser and Playwright (no-op in Electron mode)."""
        if self._electron_mode:
            from app.browser import electron_bridge
            await electron_bridge.hide()
            self._launched = False
            return
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        self._context   = None
        self._page      = None
        self._playwright = None
        self._launched  = False

    @property
    def is_running(self) -> bool:
        return self._launched and self._page is not None

    @property
    def current_url(self) -> str:
        return self._page.url if self._page else ""

    @property
    def current_title(self) -> str:
        if not self._page:
            return ""
        try:
            return self._page.url  # title can be fetched at extraction time
        except Exception:
            return ""

    # ── navigation ────────────────────────────────────────

    async def navigate(self, url: str) -> dict:
        """Go to *url* and wait for the page to become interactive."""
        await self.launch()
        if self._electron_mode:
            from app.browser import electron_bridge
            await electron_bridge.navigate(url)
            state = await electron_bridge.get_page_state()
            return {"url": state.get("url", url), "title": state.get("title", "")}
        try:
            await self._page.goto(url, wait_until="domcontentloaded")
            await self._page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass  # networkidle can timeout on heavy pages — that's fine
        return {"url": self._page.url, "title": await self._page.title()}

    async def go_back(self) -> dict:
        if self._electron_mode:
            from app.browser import electron_bridge
            await electron_bridge.go_back()
            await asyncio.sleep(1.0)
            state = await electron_bridge.get_page_state()
            return {"url": state.get("url", ""), "title": state.get("title", "")}
        await self._page.go_back(wait_until="domcontentloaded")
        return {"url": self._page.url, "title": await self._page.title()}

    async def reload(self) -> dict:
        if self._electron_mode:
            from app.browser import electron_bridge
            await electron_bridge.reload()
            await asyncio.sleep(1.5)
            state = await electron_bridge.get_page_state()
            return {"url": state.get("url", ""), "title": state.get("title", "")}
        await self._page.reload(wait_until="domcontentloaded")
        return {"url": self._page.url, "title": await self._page.title()}

    # ── observation ───────────────────────────────────────

    async def screenshot(self) -> str:
        """Return a base64-encoded JPEG screenshot of the current viewport."""
        await self.launch()
        if self._electron_mode:
            from app.browser import electron_bridge
            return await electron_bridge.screenshot()
        buf = await self._page.screenshot(type="jpeg", quality=SCREENSHOT_QUALITY)
        return base64.b64encode(buf).decode()

    async def get_page_state(self) -> dict:
        """
        Extract interactive elements + visible text so the AI can decide
        what to do next.  Returns::

            {
                "url": str,
                "title": str,
                "text": str,          # first 4 000 chars of body text
                "elements": [         # numbered interactive elements
                    {"id": 1, "tag": "input", "role": "textbox",
                     "text": "Email or phone", "x": 640, "y": 360, ...},
                    ...
                ]
            }
        """
        await self.launch()
        if self._electron_mode:
            from app.browser import electron_bridge
            return await electron_bridge.get_page_state()
        try:
            state = await self._page.evaluate(_EXTRACT_ELEMENTS_JS)
        except Exception:
            state = {
                "elements": [],
                "url": self._page.url,
                "title": await self._page.title(),
                "text": "",
            }
        return state

    # ── interaction ───────────────────────────────────────

    async def click_element(self, element_id: int) -> bool:
        """Click element by its numbered id from get_page_state()."""
        state = await self.get_page_state()
        el = next((e for e in state["elements"] if e["id"] == element_id), None)
        if not el:
            return False
        if self._electron_mode:
            from app.browser import electron_bridge
            return await electron_bridge.click(el["x"], el["y"])
        await self._page.mouse.click(el["x"], el["y"])
        await asyncio.sleep(DEFAULT_WAIT / 1000)
        return True

    async def click_coordinates(self, x: int, y: int) -> None:
        """Click at raw viewport coordinates (for user clicks on screenshot)."""
        if self._electron_mode:
            from app.browser import electron_bridge
            await electron_bridge.click(x, y)
            return
        await self._page.mouse.click(x, y)
        await asyncio.sleep(DEFAULT_WAIT / 1000)

    async def type_text(self, text: str, element_id: Optional[int] = None) -> bool:
        """
        Type *text* into the focused element, or into *element_id* if given.
        Simulates real keystrokes (important for login forms that watch input events).
        """
        if element_id is not None:
            clicked = await self.click_element(element_id)
            if not clicked:
                return False
            await asyncio.sleep(0.3)
        if self._electron_mode:
            from app.browser import electron_bridge
            return await electron_bridge.type_text(text)
        await self._page.keyboard.type(text, delay=50)
        return True

    async def press_key(self, key: str) -> None:
        """Press a special key: Enter, Tab, Escape, Backspace, ArrowDown, …"""
        if self._electron_mode:
            from app.browser import electron_bridge
            await electron_bridge.press_key(key)
            return
        await self._page.keyboard.press(key)
        await asyncio.sleep(DEFAULT_WAIT / 1000)

    async def select_all_and_type(self, text: str) -> None:
        """Select all text in the focused field and replace it."""
        if self._electron_mode:
            from app.browser import electron_bridge
            await electron_bridge.press_key("Control+a")
            await electron_bridge.type_text(text)
            return
        await self._page.keyboard.press("Control+a")
        await self._page.keyboard.type(text, delay=50)

    async def scroll(self, direction: str = "down", amount: int = 500) -> None:
        """Scroll the page. direction: 'up' | 'down'."""
        if self._electron_mode:
            from app.browser import electron_bridge
            await electron_bridge.scroll(direction)
            return
        delta = amount if direction == "down" else -amount
        await self._page.mouse.wheel(0, delta)
        await asyncio.sleep(DEFAULT_WAIT / 1000)

    async def wait_for_navigation(self, timeout: int = 10_000) -> None:
        """Wait for a navigation event (useful after clicking a link/form)."""
        try:
            await self._page.wait_for_load_state("domcontentloaded", timeout=timeout)
        except Exception:
            pass

    # ── convenience ───────────────────────────────────────

    async def fill_and_submit(self, element_id: int, text: str) -> None:
        """Type into an element and press Enter."""
        await self.type_text(text, element_id)
        await self.press_key("Enter")
        await self.wait_for_navigation()
