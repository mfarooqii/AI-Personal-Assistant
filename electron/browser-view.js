/**
 * BrowserViewManager — Manages the Electron BrowserView that acts as the
 * live, visible browser panel inside the Aria desktop app.
 *
 * When the Python backend runs a browser agent task, it sends commands to
 * the Electron IPC server → this class executes them on a REAL Chromium
 * window that is embedded in the app.  Users watch every action live and
 * can interact manually at any point.
 *
 * Key design choices:
 *  - `partition: 'persist:aria-browser'` → sessions/cookies survive restarts
 *    (user stays logged into Gmail, LinkedIn, etc. without re-authentication)
 *  - Real Chrome user-agent → zero bot detection by websites
 *  - `executeJavaScript()` for DOM extraction → same JS as the Playwright engine
 *  - `sendInputEvent()` for clicks/typing → indistinguishable from real user input
 */

'use strict'

const { BrowserView } = require('electron')

// ── Chrome user-agent string (keep up to date for best compatibility) ────────
const USER_AGENT =
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

// JS injected into the page to extract the interactive element map
// (mirrors the Playwright engine's _EXTRACT_ELEMENTS_JS for consistency)
const EXTRACT_ELEMENTS_JS = `
(() => {
  const items = []
  const sel = 'a, button, input, textarea, select, [role="button"], ' +
              '[role="link"], [role="tab"], [role="menuitem"], ' +
              '[role="option"], [role="checkbox"], [role="radio"], ' +
              '[contenteditable="true"]'
  const nodes = document.querySelectorAll(sel)
  let idx = 1
  for (const n of nodes) {
    const r = n.getBoundingClientRect()
    if (r.width === 0 || r.height === 0) continue
    if (r.bottom < 0 || r.top > window.innerHeight) continue
    const style = window.getComputedStyle(n)
    if (style.display === 'none' || style.visibility === 'hidden') continue
    const text = (n.innerText || n.textContent || '').trim().substring(0, 120)
    items.push({
      id:          idx++,
      tag:         n.tagName.toLowerCase(),
      role:        n.getAttribute('role') || n.tagName.toLowerCase(),
      text:        text || n.getAttribute('aria-label') || n.getAttribute('placeholder') || n.getAttribute('title') || '',
      x:           Math.round(r.x + r.width  / 2),
      y:           Math.round(r.y + r.height / 2),
      href:        n.getAttribute('href'),
      input_type:  n.getAttribute('type'),
      value:       n.value || '',
      placeholder: n.getAttribute('placeholder') || '',
      checked:     !!n.checked,
      disabled:    !!n.disabled,
    })
  }
  return {
    elements: items,
    url:      location.href,
    title:    document.title,
    text:     document.body?.innerText?.substring(0, 4000) || '',
  }
})()`


class BrowserViewManager {
  /**
   * @param {Electron.BrowserWindow} mainWindow
   */
  constructor(mainWindow) {
    this.mainWindow = mainWindow
    this.view       = null
    this.isVisible  = false
    this.lastBounds = null
  }

  // ── Lifecycle ──────────────────────────────────────────────────────────────

  _ensureView() {
    if (this.view) return

    this.view = new BrowserView({
      webPreferences: {
        partition:        'persist:aria-browser',   // persistent cookies/sessions
        contextIsolation: true,
        nodeIntegration:  false,
        webSecurity:      true,
      },
    })

    this.view.webContents.setUserAgent(USER_AGENT)

    // Forward navigation events to the React UI
    this.view.webContents.on('did-navigate', (_, url) => {
      this.mainWindow.webContents.send('BROWSER_URL_CHANGED', {
        url,
        title: this.view.webContents.getTitle(),
      })
    })

    this.view.webContents.on('did-navigate-in-page', (_, url) => {
      this.mainWindow.webContents.send('BROWSER_URL_CHANGED', {
        url,
        title: this.view.webContents.getTitle(),
      })
    })

    this.view.webContents.on('page-title-updated', (_, title) => {
      this.mainWindow.webContents.send('BROWSER_TITLE_CHANGED', { title })
    })
  }

  /**
   * Show the BrowserView at the given pixel bounds.
   * Called by Python backend when a browser task starts, or by React when
   * the user opens the browser panel manually.
   *
   * @param {Object|null} bounds - { x, y, width, height } in pixels, or null for default
   */
  show(bounds = null) {
    this._ensureView()

    if (!this.mainWindow.getBrowserViews().includes(this.view)) {
      this.mainWindow.addBrowserView(this.view)
    }

    this._applyBounds(bounds)
    this.isVisible = true
  }

  /** Hide the BrowserView (remove from window, keep state in memory) */
  hide() {
    if (this.view && this.mainWindow.getBrowserViews().includes(this.view)) {
      this.mainWindow.removeBrowserView(this.view)
    }
    this.isVisible = false
  }

  /** Called when the main window is resized — reapply stored bounds */
  onWindowResize() {
    if (this.isVisible) {
      this._applyBounds(this.lastBounds)
    }
  }

  _applyBounds(bounds) {
    if (!this.view) return

    if (bounds && bounds.width > 0 && bounds.height > 0) {
      this.lastBounds = bounds
      this.view.setBounds({
        x:      Math.round(bounds.x),
        y:      Math.round(bounds.y),
        width:  Math.round(bounds.width),
        height: Math.round(bounds.height),
      })
    } else {
      // Default: right 45% of the content area
      const [w, h] = this.mainWindow.getContentSize()
      const panelW = Math.round(w * 0.45)
      this.view.setBounds({ x: w - panelW, y: 0, width: panelW, height: h })
    }
  }

  // ── Navigation ─────────────────────────────────────────────────────────────

  async navigate(url) {
    this._ensureView()
    if (!/^https?:\/\//i.test(url)) url = 'https://' + url
    await this.view.webContents.loadURL(url)
    // Brief wait for DOM to stabilise
    await new Promise(r => setTimeout(r, 1500))
  }

  async goBack() {
    if (this.view?.webContents.canGoBack()) {
      this.view.webContents.goBack()
      await new Promise(r => setTimeout(r, 1000))
    }
  }

  async goForward() {
    if (this.view?.webContents.canGoForward()) {
      this.view.webContents.goForward()
      await new Promise(r => setTimeout(r, 1000))
    }
  }

  async reload() {
    this.view?.webContents.reload()
    await new Promise(r => setTimeout(r, 1500))
  }

  // ── Interaction ────────────────────────────────────────────────────────────

  async click(x, y) {
    if (!this.view) return
    const wc = this.view.webContents
    wc.sendInputEvent({ type: 'mouseMove',  x, y })
    wc.sendInputEvent({ type: 'mouseDown',  x, y, button: 'left', clickCount: 1 })
    wc.sendInputEvent({ type: 'mouseUp',    x, y, button: 'left', clickCount: 1 })
    await new Promise(r => setTimeout(r, 500))
  }

  async typeText(text) {
    if (!this.view) return
    const wc = this.view.webContents
    for (const char of text) {
      wc.sendInputEvent({ type: 'char', keyCode: char })
      // Small delay per character to mimic human typing
      await new Promise(r => setTimeout(r, 30 + Math.random() * 40))
    }
  }

  async pressKey(key) {
    if (!this.view) return
    // Electron keyCode names differ slightly from DOM / Playwright
    const keyMap = {
      Enter:     'Return',
      Escape:    'Escape',
      Tab:       'Tab',
      Backspace: 'BackSpace',
      Delete:    'Delete',
      ArrowDown: 'Down',
      ArrowUp:   'Up',
      ArrowLeft: 'Left',
      ArrowRight:'Right',
      Space:     'Space',
      Home:      'Home',
      End:       'End',
    }
    const keyCode = keyMap[key] || key
    const wc = this.view.webContents
    wc.sendInputEvent({ type: 'keyDown', keyCode })
    wc.sendInputEvent({ type: 'keyUp',   keyCode })
    await new Promise(r => setTimeout(r, 500))
  }

  async scroll(direction = 'down') {
    if (!this.view) return
    const delta = direction === 'up' ? 300 : -300
    this.view.webContents.sendInputEvent({
      type:        'mouseWheel',
      x:           640,
      y:           360,
      deltaX:      0,
      deltaY:      delta,
      wheelTicksX: 0,
      wheelTicksY: delta > 0 ? 3 : -3,
    })
    await new Promise(r => setTimeout(r, 300))
  }

  // ── Observation ────────────────────────────────────────────────────────────

  async getPageState() {
    if (!this.view) return { url: '', title: '', elements: [], text: '' }
    try {
      const result = await this.view.webContents.executeJavaScript(EXTRACT_ELEMENTS_JS)
      return result
    } catch {
      return {
        url:      this.view.webContents.getURL(),
        title:    this.view.webContents.getTitle(),
        elements: [],
        text:     '',
      }
    }
  }

  async captureScreenshot() {
    if (!this.view) return { screenshot: '' }
    try {
      const image  = await this.view.webContents.capturePage()
      const base64 = image.toJPEG(60).toString('base64')
      return { screenshot: base64 }
    } catch {
      return { screenshot: '' }
    }
  }
}

module.exports = BrowserViewManager
