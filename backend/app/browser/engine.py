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


# ── JS: extract interactive elements with labels + current values ──

_EXTRACT_ELEMENTS_JS = """
() => {
    function getLabel(n) {
        if (n.getAttribute('aria-label')) return n.getAttribute('aria-label');
        const lbId = n.getAttribute('aria-labelledby');
        if (lbId) { const lb = document.getElementById(lbId); if (lb) return lb.innerText.trim(); }
        if (n.id) { const lb = document.querySelector('label[for="' + n.id + '"]'); if (lb) return lb.innerText.trim(); }
        const parent = n.closest('label');
        if (parent) return parent.innerText.replace(n.value || '', '').trim();
        const prev = n.previousElementSibling;
        if (prev && prev.tagName !== 'INPUT') return prev.innerText.trim().substring(0, 60);
        return '';
    }

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
        if (r.bottom < 0 || r.top > window.innerHeight + 200) continue;
        const style = window.getComputedStyle(n);
        if (style.display === 'none' || style.visibility === 'hidden') continue;

        const text = (n.innerText || n.textContent || '').trim().substring(0, 120);
        const tag  = n.tagName.toLowerCase();
        const role = n.getAttribute('role') || tag;
        const label = (tag === 'input' || tag === 'textarea' || tag === 'select') ? getLabel(n) : '';
        items.push({
            id:   idx++,
            tag,
            role,
            text: text || n.getAttribute('aria-label')
                       || n.getAttribute('placeholder')
                       || n.getAttribute('title')
                       || n.getAttribute('name')
                       || '',
            label,
            x: Math.round(r.x + r.width  / 2),
            y: Math.round(r.y + r.height / 2),
            href:         n.getAttribute('href'),
            input_type:   n.getAttribute('type') || '',
            value:        n.value || '',
            placeholder:  n.getAttribute('placeholder') || '',
            checked:      !!n.checked,
            disabled:     !!n.disabled,
            required:     !!n.required,
            name:         n.getAttribute('name') || '',
            autocomplete: n.getAttribute('autocomplete') || '',
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

# ── JS: extract form structure for AI planning ──

_ANALYZE_FORMS_JS = """
() => {
    function getLabel(n) {
        if (n.getAttribute('aria-label')) return n.getAttribute('aria-label');
        const lbId = n.getAttribute('aria-labelledby');
        if (lbId) { const lb = document.getElementById(lbId); if (lb) return lb.innerText.trim(); }
        if (n.id) { const lb = document.querySelector('label[for="' + n.id + '"]'); if (lb) return lb.innerText.trim(); }
        const parent = n.closest('label');
        if (parent) return parent.innerText.replace(n.value || '', '').trim();
        const prev = n.previousElementSibling;
        if (prev) return prev.innerText.trim().substring(0, 60);
        return n.getAttribute('placeholder') || n.getAttribute('name') || '';
    }
    const forms = [];
    document.querySelectorAll('form').forEach((form, fi) => {
        const fields = [];
        form.querySelectorAll('input:not([type=hidden]), textarea, select').forEach(n => {
            const r = n.getBoundingClientRect();
            if (r.width === 0 || r.height === 0) return;
            fields.push({
                label:         getLabel(n),
                type:          n.type || n.tagName.toLowerCase(),
                name:          n.name || '',
                autocomplete:  n.autocomplete || '',
                required:      n.required,
                current_value: n.value || '',
                placeholder:   n.placeholder || '',
            });
        });
        const submitBtn = form.querySelector('[type=submit], button:not([type=button])');
        forms.push({
            index: fi,
            fields,
            submit_button_text: submitBtn ? (submitBtn.innerText || submitBtn.value || 'Submit').trim() : '',
        });
    });
    return forms;
}
"""


class BrowserEngine:
    """
    Thin async wrapper around a browser context (Electron IPC or standalone patchright).

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

        from app.browser import electron_bridge
        if await electron_bridge.is_available():
            self._electron_mode = True
            self._launched = True
            log.info("BrowserEngine: Electron mode — using live BrowserView")
            return

        # Standalone mode: stealth Chromium via patchright
        self._electron_mode = False
        try:
            from patchright.async_api import async_playwright
        except ImportError:
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
        self._context    = None
        self._page       = None
        self._playwright = None
        self._launched   = False

    @property
    def is_running(self) -> bool:
        return self._launched

    @property
    def current_url(self) -> str:
        return self._page.url if self._page else ""

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
            pass
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
        what to do next.
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

    async def analyze_forms(self) -> list[dict]:
        """
        Extract structured form information from the current page.
        Returns a list of forms with fields, types, labels, and current values.
        The AI uses this to understand what a page expects before filling.
        """
        await self.launch()
        if self._electron_mode:
            # In Electron mode we don't have direct JS eval, fall back to element list
            return []
        try:
            return await self._page.evaluate(_ANALYZE_FORMS_JS)
        except Exception:
            return []

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
        """Click at raw viewport coordinates."""
        if self._electron_mode:
            from app.browser import electron_bridge
            await electron_bridge.click(x, y)
            return
        await self._page.mouse.click(x, y)
        await asyncio.sleep(DEFAULT_WAIT / 1000)

    async def fill_field(self, element_id: int, text: str) -> bool:
        """
        Fill a form field — clears existing content first, then types.
        Preferred over type_text for all form inputs.
        """
        state = await self.get_page_state()
        el = next((e for e in state["elements"] if e["id"] == element_id), None)
        if not el:
            return False
        if self._electron_mode:
            from app.browser import electron_bridge
            await electron_bridge.click(el["x"], el["y"])
            await asyncio.sleep(0.2)
            await electron_bridge.press_key("Control+a")
            await asyncio.sleep(0.1)
            await electron_bridge.press_key("Delete")
            await asyncio.sleep(0.1)
            return await electron_bridge.type_text(text)
        # Standalone: click, select-all, delete, then type
        await self._page.mouse.click(el["x"], el["y"])
        await asyncio.sleep(0.2)
        await self._page.keyboard.press("Control+a")
        await asyncio.sleep(0.1)
        await self._page.keyboard.press("Delete")
        await asyncio.sleep(0.1)
        await self._page.keyboard.type(text, delay=40)
        return True

    async def type_text(self, text: str, element_id: Optional[int] = None) -> bool:
        """
        Type into the focused element (or element_id if given).
        Clears first to prevent accumulation. Redirects to fill_field if element given.
        """
        if element_id is not None:
            return await self.fill_field(element_id, text)
        if self._electron_mode:
            from app.browser import electron_bridge
            return await electron_bridge.type_text(text)
        await self._page.keyboard.press("Control+a")
        await asyncio.sleep(0.1)
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

    async def scroll(self, direction: str = "down", amount: int = 500) -> None:
        """Scroll the page."""
        if self._electron_mode:
            from app.browser import electron_bridge
            await electron_bridge.scroll(direction)
            return
        delta = amount if direction == "down" else -amount
        await self._page.mouse.wheel(0, delta)
        await asyncio.sleep(DEFAULT_WAIT / 1000)

    async def wait_for_navigation(self, timeout: int = 10_000) -> None:
        """Wait for page navigation to complete."""
        if self._electron_mode:
            await asyncio.sleep(1.5)
            return
        try:
            await self._page.wait_for_load_state("domcontentloaded", timeout=timeout)
        except Exception:
            pass

    async def fill_and_submit(self, element_id: int, text: str) -> None:
        """Fill a field and press Enter."""
        await self.fill_field(element_id, text)
        await self.press_key("Enter")
        await self.wait_for_navigation()
