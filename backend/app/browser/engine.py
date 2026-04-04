"""
Browser Engine — Playwright wrapper for local browser automation.

Manages a persistent Chromium instance with user sessions (cookies survive
between restarts).  Provides atomic actions that the Browser Agent calls:
navigate, click, type, scroll, screenshot, and DOM extraction.

Design choices:
  - Persistent context  →  cookies/sessions survive, user only signs in once.
  - Accessibility-tree extraction  →  gives AI a numbered element map that
    any small text model can reason about (no vision model needed).
  - JPEG screenshots at low quality  →  ~50-80 KB per frame, fast to stream.
  - Viewport fixed at 1280×720  →  predictable element coordinates.
"""

import asyncio
import base64
from pathlib import Path
from typing import Optional

from app.config import settings

# ── Constants ────────────────────────────────────────────

BROWSER_DATA_DIR = settings.DATA_DIR / "browser_data"
VIEWPORT = {"width": 1280, "height": 720}
SCREENSHOT_QUALITY = 50            # JPEG quality (lower = smaller)
NAV_TIMEOUT = 30_000               # ms
DEFAULT_WAIT = 1_000               # ms after an action


# ── JS snippet injected into pages to extract interactive elements ──

_EXTRACT_ELEMENTS_JS = """
() => {
    // Helper: find the visible label for an input element
    function getLabel(n) {
        // 1. aria-label / aria-labelledby
        if (n.getAttribute('aria-label')) return n.getAttribute('aria-label');
        const lbId = n.getAttribute('aria-labelledby');
        if (lbId) {
            const lb = document.getElementById(lbId);
            if (lb) return lb.innerText.trim();
        }
        // 2. <label for="id">
        if (n.id) {
            const lb = document.querySelector('label[for="' + n.id + '"]');
            if (lb) return lb.innerText.trim();
        }
        // 3. Wrapping <label>
        const parent = n.closest('label');
        if (parent) return parent.innerText.replace(n.value, '').trim();
        // 4. Preceding sibling text
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
        const label = (tag === 'input' || tag === 'textarea' || tag === 'select')
                      ? getLabel(n) : '';
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
            href:        n.getAttribute('href'),
            input_type:  n.getAttribute('type') || '',
            value:       n.value || '',
            placeholder: n.getAttribute('placeholder') || '',
            checked:     !!n.checked,
            disabled:    !!n.disabled,
            required:    !!n.required,
            name:        n.getAttribute('name') || '',
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

# JS to extract only form fields (inputs) for the form analysis step
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
                label:        getLabel(n),
                type:         n.type || n.tagName.toLowerCase(),
                name:         n.name || '',
                autocomplete: n.autocomplete || '',
                required:     n.required,
                current_value: n.value || '',
                placeholder:  n.placeholder || '',
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
        self._playwright = None
        self._context    = None
        self._page       = None
        self._launched   = False

    # ── lifecycle ─────────────────────────────────────────

    async def launch(self) -> None:
        """Start Chromium with a persistent user-data dir."""
        if self._launched:
            return

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
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        # Reuse the first page or create one
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()

        self._page.set_default_navigation_timeout(NAV_TIMEOUT)
        self._launched = True

    async def close(self) -> None:
        """Shut down browser and Playwright."""
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        self._context = None
        self._page = None
        self._playwright = None
        self._launched = False

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
        try:
            resp = await self._page.goto(url, wait_until="domcontentloaded")
            await self._page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass  # networkidle can timeout on heavy pages — that's fine
        return {"url": self._page.url, "title": await self._page.title()}

    async def go_back(self) -> dict:
        await self._page.go_back(wait_until="domcontentloaded")
        return {"url": self._page.url, "title": await self._page.title()}

    async def reload(self) -> dict:
        await self._page.reload(wait_until="domcontentloaded")
        return {"url": self._page.url, "title": await self._page.title()}

    # ── observation ───────────────────────────────────────

    async def screenshot(self) -> str:
        """Return a base64-encoded JPEG screenshot of the current viewport."""
        await self.launch()
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
        await self._page.mouse.click(el["x"], el["y"])
        await asyncio.sleep(DEFAULT_WAIT / 1000)
        return True

    async def click_coordinates(self, x: int, y: int) -> None:
        """Click at raw viewport coordinates (for user clicks on screenshot)."""
        await self._page.mouse.click(x, y)
        await asyncio.sleep(DEFAULT_WAIT / 1000)

    async def type_text(self, text: str, element_id: Optional[int] = None) -> bool:
        """
        Type *text* into the focused element, or into *element_id* if given.
        Simulates real keystrokes (important for login forms that watch input events).
        Always clears the field first to avoid appending to existing content.
        """
        if element_id is not None:
            clicked = await self.click_element(element_id)
            if not clicked:
                return False
            await asyncio.sleep(0.3)
        # Clear existing content first, then type
        await self._page.keyboard.press("Control+a")
        await asyncio.sleep(0.1)
        await self._page.keyboard.type(text, delay=50)
        return True

    async def analyze_forms(self) -> list[dict]:
        """
        Extract structured form information from the current page.
        Returns a list of forms with their fields, types, labels, and current values.
        Useful for the AI to understand what a page expects before filling it.
        """
        await self.launch()
        try:
            return await self._page.evaluate(_ANALYZE_FORMS_JS)
        except Exception:
            return []

    async def fill_field(self, element_id: int, text: str) -> bool:
        """
        Fill a form field by setting its value directly (clears first).
        Uses Playwright's locator.fill() which triggers input/change events.
        Falls back to type_text if the element can't be located by selector.
        Preferred over type_text for form inputs.
        """
        state = await self.get_page_state()
        el = next((e for e in state["elements"] if e["id"] == element_id), None)
        if not el:
            return False
        try:
            # Try locating by coordinates — use Playwright locator at position
            await self._page.mouse.click(el["x"], el["y"])
            await asyncio.sleep(0.2)
            await self._page.keyboard.press("Control+a")
            await asyncio.sleep(0.1)
            await self._page.keyboard.press("Delete")
            await asyncio.sleep(0.1)
            await self._page.keyboard.type(text, delay=40)
            return True
        except Exception:
            return await self.type_text(text, element_id)

    async def press_key(self, key: str) -> None:
        """Press a special key: Enter, Tab, Escape, Backspace, ArrowDown, …"""
        await self._page.keyboard.press(key)
        await asyncio.sleep(DEFAULT_WAIT / 1000)

    async def select_all_and_type(self, text: str) -> None:
        """Select all text in the focused field and replace it."""
        await self._page.keyboard.press("Control+a")
        await self._page.keyboard.type(text, delay=50)

    async def scroll(self, direction: str = "down", amount: int = 500) -> None:
        """Scroll the page. direction: 'up' | 'down'."""
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
