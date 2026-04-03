/**
 * Electron Preload — context bridge between main process and React renderer.
 *
 * Exposes a safe `window.electronBridge` API to the React app so it can:
 *  - Control the embedded browser panel (navigate, show/hide)
 *  - Receive agent status updates in real time
 *  - Know it is running inside Electron (not a plain browser)
 */

'use strict'

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronBridge', {
  /** true when running in the Electron desktop app */
  isElectron: true,

  // ── Browser panel control (React → Electron) ─────────────────────────────

  /** Navigate the embedded browser to a URL */
  navigate: (url) => ipcRenderer.send('BROWSER_NAVIGATE', url),

  /** Go back in the embedded browser history */
  goBack: () => ipcRenderer.send('BROWSER_BACK'),

  /** Go forward in the embedded browser history */
  goForward: () => ipcRenderer.send('BROWSER_FORWARD'),

  /** Reload the current page in the embedded browser */
  reload: () => ipcRenderer.send('BROWSER_RELOAD'),

  /**
   * Show the BrowserView positioned to cover this pixel rect.
   * @param {Object} bounds - { x, y, width, height } in screen pixels
   */
  showBrowser: (bounds) => ipcRenderer.send('BROWSER_SHOW', bounds),

  /** Hide the BrowserView (React regains full control of the area) */
  hideBrowser: () => ipcRenderer.send('BROWSER_HIDE'),

  /** Get current page state (url, title, elements, text) from BrowserView */
  getPageState: () => ipcRenderer.invoke('BROWSER_GET_STATE'),

  // ── Events (Electron → React) ────────────────────────────────────────────

  /** Called when the BrowserView navigates to a new URL */
  onUrlChanged: (cb) => {
    ipcRenderer.on('BROWSER_URL_CHANGED', (_, data) => cb(data))
  },

  /** Called when the page title changes */
  onTitleChanged: (cb) => {
    ipcRenderer.on('BROWSER_TITLE_CHANGED', (_, data) => cb(data))
  },

  /** Called when the agent sends a status/action message */
  onAgentStatus: (cb) => {
    ipcRenderer.on('BROWSER_AGENT_STATUS', (_, data) => cb(data))
  },

  /** Called when the browser panel becomes active (agent started a task) */
  onBrowserActivated: (cb) => {
    ipcRenderer.on('BROWSER_ACTIVATED', () => cb())
  },

  /** Called when the browser panel is deactivated */
  onBrowserDeactivated: (cb) => {
    ipcRenderer.on('BROWSER_DEACTIVATED', () => cb())
  },

  /** Remove all listeners for a given channel */
  removeListeners: (channel) => ipcRenderer.removeAllListeners(channel),
})
