/**
 * Electron Main Process — Aria Desktop App
 *
 * Responsibilities:
 *  1. Spawn the FastAPI backend (uvicorn) as a child process
 *  2. Wait for the backend health check before showing the window
 *  3. Create the main BrowserWindow loaded with the React UI
 *  4. Manage the embedded BrowserView for the live browser panel
 *  5. Run a local HTTP IPC server (port 8001) so the Python backend
 *     can send browser commands (navigate, click, type, etc.) to the
 *     visible Electron BrowserView — no bot detection, real Chrome
 *  6. System tray integration
 */

'use strict'

const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage } = require('electron')
const path   = require('path')
const { spawn } = require('child_process')
const http   = require('http')
const os     = require('os')

const BrowserViewManager = require('./browser-view')

// ── Config ──────────────────────────────────────────────────────────────────

const BACKEND_PORT   = 8000
const IPC_PORT       = 8001          // Python backend → Electron browser control
const CDP_PORT       = 9222          // Chrome DevTools Protocol for browser-use
const FRONTEND_URL   = 'http://localhost:3000'
const IS_DEV         = process.env.NODE_ENV !== 'production'

// Enable CDP so browser-use (Python) can connect to the real visible BrowserView
// and drive it directly — user watches every action live, zero bot detection.
app.commandLine.appendSwitch('remote-debugging-port', String(CDP_PORT))
app.commandLine.appendSwitch('remote-debugging-address', '127.0.0.1')

// ── State ────────────────────────────────────────────────────────────────────

let mainWindow      = null
let tray            = null
let backendProcess  = null
let browserManager  = null
let ipcServer       = null

// ── App lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  startBackend()
  await waitForBackend()
  createMainWindow()
  createTray()
  startIpcServer()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (!mainWindow) createMainWindow()
})

app.on('before-quit', cleanup)

// ── Backend ───────────────────────────────────────────────────────────────────

function startBackend() {
  // Use .venv/bin/uvicorn — the active virtual environment for this project.
  // Using the uvicorn binary directly ensures all venv packages are on sys.path.
  const uvicornBin = IS_DEV
    ? path.join(__dirname, '..', 'backend', '.venv', 'bin', 'uvicorn')
    : path.join(process.resourcesPath, 'backend', '.venv', 'bin', 'uvicorn')

  const backendCwd = IS_DEV
    ? path.join(__dirname, '..', 'backend')
    : path.join(process.resourcesPath, 'backend')

  backendProcess = spawn(
    uvicornBin,
    ['app.main:app', '--host', '0.0.0.0', '--port', String(BACKEND_PORT)],
    {
      cwd: backendCwd,
      env: { ...process.env },
    }
  )

  backendProcess.stdout.on('data', d => process.stdout.write(`[backend] ${d}`))
  backendProcess.stderr.on('data', d => process.stderr.write(`[backend] ${d}`))
  backendProcess.on('error', e => console.error('[backend] Spawn error:', e.message))
  backendProcess.on('exit', code => console.log(`[backend] Exited with code ${code}`))

  console.log('[electron] Backend process started')
}

async function waitForBackend(maxAttempts = 40) {
  console.log('[electron] Waiting for backend...')
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetch(`http://localhost:${BACKEND_PORT}/api/health`)
      if (res.ok) {
        console.log('[electron] Backend ready ✓')
        return
      }
    } catch { /* not ready yet */ }
    await new Promise(r => setTimeout(r, 1000))
  }
  console.error('[electron] Backend failed to start within timeout')
}

// ── Main Window ───────────────────────────────────────────────────────────────

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width:           1440,
    height:          900,
    minWidth:        900,
    minHeight:       600,
    backgroundColor: '#0a0a0f',
    title:           'Aria',
    titleBarStyle:   process.platform === 'darwin' ? 'hiddenInset' : 'default',
    webPreferences: {
      preload:          path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration:  false,
    },
  })

  if (IS_DEV) {
    mainWindow.loadURL(FRONTEND_URL)
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'dist', 'index.html'))
  }

  browserManager = new BrowserViewManager(mainWindow)

  mainWindow.on('resize', () => browserManager.onWindowResize())
  mainWindow.on('closed', () => { mainWindow = null })
}

// ── System Tray ───────────────────────────────────────────────────────────────

function createTray() {
  const icon = nativeImage.createEmpty()
  tray = new Tray(icon)
  tray.setToolTip('Aria')
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Open Aria', click: () => mainWindow?.show() },
    { type:  'separator' },
    { label: 'Quit',      click: () => app.quit() },
  ]))
  tray.on('click', () => mainWindow?.show())
}

// ── IPC Server (Python backend → Electron browser control) ───────────────────
//
// The Python browser agent sends HTTP requests here to control the
// live-visible BrowserView.  This lets users watch Aria work in real Chrome
// without any headless browser or bot-detection issues.

function startIpcServer() {
  ipcServer = http.createServer((req, res) => {
    const chunks = []
    req.on('data', chunk => chunks.push(chunk))
    req.on('end', async () => {
      const bodyStr = Buffer.concat(chunks).toString()
      const body    = bodyStr ? JSON.parse(bodyStr) : {}

      res.setHeader('Content-Type', 'application/json')

      try {
        let result = { ok: true }

        switch (req.url) {
          case '/browser/navigate':
            await browserManager.navigate(body.url)
            break
          case '/browser/click':
            await browserManager.click(body.x, body.y)
            break
          case '/browser/type':
            await browserManager.typeText(body.text)
            break
          case '/browser/key':
            await browserManager.pressKey(body.key)
            break
          case '/browser/scroll':
            await browserManager.scroll(body.direction)
            break
          case '/browser/state':
            result = await browserManager.getPageState()
            break
          case '/browser/screenshot':
            result = await browserManager.captureScreenshot()
            break
          case '/browser/show':
            browserManager.show(body.bounds || null)
            // Notify React that browser panel is now live
            mainWindow?.webContents.send('BROWSER_ACTIVATED')
            break
          case '/browser/hide':
            browserManager.hide()
            mainWindow?.webContents.send('BROWSER_DEACTIVATED')
            break
          case '/browser/cdp-url':
            result = { url: `http://127.0.0.1:${CDP_PORT}` }
            break
          case '/browser/back':
            await browserManager.goBack()
            break
          case '/browser/forward':
            await browserManager.goForward()
            break
          case '/browser/reload':
            await browserManager.reload()
            break
          case '/browser/status':
            // Agent streams a status message to the React UI
            mainWindow?.webContents.send('BROWSER_AGENT_STATUS', {
              message: body.message,
              action:  body.action,
            })
            break
          default:
            res.writeHead(404)
            res.end(JSON.stringify({ error: 'Unknown endpoint' }))
            return
        }

        res.writeHead(200)
        res.end(JSON.stringify(result))
      } catch (err) {
        console.error('[ipc-server] Error:', err.message)
        res.writeHead(500)
        res.end(JSON.stringify({ error: err.message }))
      }
    })
  })

  ipcServer.listen(IPC_PORT, '127.0.0.1', () => {
    console.log(`[electron] IPC server listening on :${IPC_PORT}`)
  })
}

// ── IPC handlers (React UI → Electron) ──────────────────────────────────────

ipcMain.on('BROWSER_NAVIGATE',  (_, url)    => browserManager?.navigate(url))
ipcMain.on('BROWSER_BACK',      ()          => browserManager?.goBack())
ipcMain.on('BROWSER_FORWARD',   ()          => browserManager?.goForward())
ipcMain.on('BROWSER_RELOAD',    ()          => browserManager?.reload())
ipcMain.on('BROWSER_SHOW',      (_, bounds) => browserManager?.show(bounds))
ipcMain.on('BROWSER_HIDE',      ()          => browserManager?.hide())
ipcMain.on('BROWSER_CLOSE',     ()          => browserManager?.hide())

ipcMain.handle('BROWSER_GET_STATE',      () => browserManager?.getPageState())
ipcMain.handle('BROWSER_IS_ELECTRON',    () => true)

// ── Cleanup ──────────────────────────────────────────────────────────────────

function cleanup() {
  if (backendProcess) {
    backendProcess.kill('SIGTERM')
  }
  if (ipcServer) {
    ipcServer.close()
  }
}
