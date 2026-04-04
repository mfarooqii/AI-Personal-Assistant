/**
 * BrowserPanel — in-app browser view powered by AI.
 *
 * TWO MODES (auto-detected):
 *
 * 1. Electron mode (desktop app)
 *    The Electron main process embeds a real Chromium BrowserView behind
 *    this React component.  This component renders only the toolbar and
 *    status overlay — the actual browser content is the native BrowserView
 *    sitting behind it.  User sees the real browser, agent controls it live.
 *
 * 2. Web mode (browser-based)
 *    Falls back to the original screenshot-over-WebSocket approach.
 *    Shows base64 JPEG frames streamed from the Playwright backend.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Globe, Loader2, MousePointer2, Keyboard, ArrowLeft, ArrowRight,
  RefreshCw, X, CheckCircle, AlertCircle, Bot, ChevronRight,
  Monitor, Send, Hand, Sparkles, ExternalLink,
} from 'lucide-react';

// Electron bridge injected by preload.js (undefined when running as web app)
const eb = (window as any).electronBridge as {
  isElectron: boolean
  navigate:      (url: string) => void
  goBack:        () => void
  goForward:     () => void
  reload:        () => void
  showBrowser:   (bounds: DOMRect | { x: number; y: number; width: number; height: number }) => void
  hideBrowser:   () => void
  onUrlChanged:     (cb: (d: { url: string; title: string }) => void) => void
  onTitleChanged:   (cb: (d: { title: string }) => void) => void
  onAgentStatus:    (cb: (d: { message: string; action?: string }) => void) => void
  onBrowserActivated:   (cb: () => void) => void
  onBrowserDeactivated: (cb: () => void) => void
  removeListeners: (ch: string) => void
} | undefined

const IS_ELECTRON = !!eb?.isElectron

interface BrowserEvent {
  type: 'screenshot' | 'status' | 'action' | 'interactive' | 'result' | 'complete' | 'error';
  message?: string;
  screenshot?: string;
  url?: string;
  title?: string;
  data?: any;
}

interface Props {
  task: string;
  plan: any;
  onResult: (data: any) => void;
  onClose: () => void;
}

type Phase = 'connecting' | 'browsing' | 'interactive' | 'extracting' | 'complete' | 'error';

export function BrowserPanel({ task, plan, onResult, onClose }: Props) {
  const [phase, setPhase]         = useState<Phase>('connecting');
  const [manualMode, setManualMode] = useState(false);
  const [screenshot, setScreenshot] = useState<string>('');
  const [statusMsg, setStatusMsg] = useState(IS_ELECTRON ? 'Browser ready — AI is working...' : 'Connecting to browser...');
  const [pageUrl, setPageUrl]     = useState('');
  const [pageTitle, setPageTitle] = useState('');
  const [typingInput, setTypingInput] = useState('');
  const [actionLog, setActionLog] = useState<string[]>([]);
  const [urlBarInput, setUrlBarInput] = useState('');

  const wsRef      = useRef<WebSocket | null>(null);
  const imgRef     = useRef<HTMLImageElement>(null);
  const panelRef   = useRef<HTMLDivElement>(null);
  const resizeObserver = useRef<ResizeObserver | null>(null);

  // ── Electron mode setup ─────────────────────────────────────────────────
  useEffect(() => {
    if (!IS_ELECTRON) return;

    // Subscribe to events from the Electron main process
    eb!.onUrlChanged(({ url, title }) => {
      setPageUrl(url);
      setPageTitle(title);
      setUrlBarInput(url);
    });
    eb!.onTitleChanged(({ title }) => setPageTitle(title));
    eb!.onAgentStatus(({ message, action }) => {
      setStatusMsg(message);
      if (action) {
        setPhase('browsing');
        setActionLog(prev => [...prev.slice(-20), `[AI] ${message}`]);
      }
    });
    eb!.onBrowserActivated(() => setPhase('browsing'));
    eb!.onBrowserDeactivated(() => setPhase('connecting'));

    // Show the BrowserView aligned to this component's position
    const showWithBounds = () => {
      if (panelRef.current) {
        const rect = panelRef.current.getBoundingClientRect();
        // Only the content area (below the toolbar ~40px)
        eb!.showBrowser({ x: rect.left, y: rect.top + 40, width: rect.width, height: rect.height - 40 });
      }
    };

    // Use a ResizeObserver to keep BrowserView in sync with panel size
    resizeObserver.current = new ResizeObserver(showWithBounds);
    if (panelRef.current) resizeObserver.current.observe(panelRef.current);

    showWithBounds();
    setPhase('browsing');

    return () => {
      resizeObserver.current?.disconnect();
      eb!.hideBrowser();
      eb!.removeListeners('BROWSER_URL_CHANGED');
      eb!.removeListeners('BROWSER_TITLE_CHANGED');
      eb!.removeListeners('BROWSER_AGENT_STATUS');
      eb!.removeListeners('BROWSER_ACTIVATED');
      eb!.removeListeners('BROWSER_DEACTIVATED');
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Web mode: WebSocket screenshot stream ─────────────────────────────────
  useEffect(() => {
    if (IS_ELECTRON) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.host}/api/browser/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ task, plan }));
      setPhase('browsing');
      setStatusMsg('Browser connected. Starting task...');
    };

    ws.onmessage = (ev) => {
      try {
        const event: BrowserEvent = JSON.parse(ev.data);
        handleWebEvent(event);
      } catch { /* ignore parse errors */ }
    };

    ws.onerror   = () => { setPhase('error');  setStatusMsg('Failed to connect to browser.'); };
    ws.onclose   = () => { if (phase !== 'complete' && phase !== 'error') setStatusMsg('Connection closed.'); };

    return () => { ws.close(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleWebEvent = useCallback((event: BrowserEvent) => {
    if (event.screenshot) setScreenshot(event.screenshot);
    if (event.url)   setPageUrl(event.url);
    if (event.title) setPageTitle(event.title);

    switch (event.type) {
      case 'status':
        setStatusMsg(event.message || '');
        setActionLog(prev => [...prev.slice(-20), `[AI] ${event.message}`]);
        break;
      case 'action':
        setPhase('browsing');
        setStatusMsg(event.message || 'Taking action...');
        setActionLog(prev => [...prev.slice(-20), `[Action] ${event.message}`]);
        break;
      case 'interactive':
        setPhase('interactive');
        setStatusMsg(event.message || 'Your turn — interact with the page.');
        setActionLog(prev => [...prev.slice(-20), `[Waiting] ${event.message}`]);
        break;
      case 'result':
        setPhase('extracting');
        setStatusMsg('Extracting data...');
        break;
      case 'complete':
        setPhase('complete');
        setStatusMsg(event.message || 'Task complete!');
        if (event.data) onResult(event.data);
        break;
      case 'error':
        setPhase('error');
        setStatusMsg(event.message || 'Something went wrong.');
        break;
    }
  }, [onResult]);

  // ── Shared user interactions ──────────────────────────────────────────────

  const sendWs = (data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  };

  const handleScreenshotClick = (e: React.MouseEvent<HTMLImageElement>) => {
    if (phase !== 'interactive' && !manualMode) return;
    const img = imgRef.current;
    if (!img) return;
    const rect = img.getBoundingClientRect();
    const x = Math.round((e.clientX - rect.left) * (1280 / rect.width));
    const y = Math.round((e.clientY - rect.top)  * (720  / rect.height));
    sendWs({ type: 'click', x, y });
    setActionLog(prev => [...prev.slice(-20), `[You] Clicked at (${x}, ${y})`]);
  };

  const handleType = () => {
    if (!typingInput.trim()) return;
    if (IS_ELECTRON) {
      // In Electron mode the user types directly in the live browser
    } else {
      sendWs({ type: 'type', text: typingInput });
    }
    setActionLog(prev => [...prev.slice(-20), `[You] Typed: "${typingInput}"`]);
    setTypingInput('');
  };

  const handleKey = (key: string) => {
    if (!IS_ELECTRON) sendWs({ type: 'key', key });
    setActionLog(prev => [...prev.slice(-20), `[You] Pressed: ${key}`]);
  };

  const handleResume = () => {
    sendWs({ type: 'resume' });
    setPhase('browsing');
    setStatusMsg('Resuming task...');
  };

  const handleUrlBarNavigate = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && IS_ELECTRON) {
      eb!.navigate(urlBarInput);
    }
  };

  // ── Phase indicators ──────────────────────────────────────────────────────

  const phaseIcon = () => {
    switch (phase) {
      case 'connecting':  return <Loader2 size={14} className="animate-spin text-white/40" />;
      case 'browsing':    return <Bot size={14} className="text-aria-400 animate-pulse" />;
      case 'interactive': return <MousePointer2 size={14} className="text-amber-400" />;
      case 'extracting':  return <Loader2 size={14} className="animate-spin text-emerald-400" />;
      case 'complete':    return <CheckCircle size={14} className="text-emerald-400" />;
      case 'error':       return <AlertCircle size={14} className="text-red-400" />;
    }
  };

  const phaseLabel = () => ({
    connecting:  'Connecting',
    browsing:    'AI Browsing',
    interactive: 'Your Turn',
    extracting:  'Extracting',
    complete:    'Complete',
    error:       'Error',
  }[phase]);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div ref={panelRef} className="flex flex-col h-full bg-[var(--bg-secondary)]">

      {/* ── Toolbar ──────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 px-3 py-2 bg-[var(--bg-primary)] border-b border-white/5 shrink-0">
        <Monitor size={15} className="text-aria-400 shrink-0" />

        {/* Back / Forward / Reload (Electron only) */}
        {IS_ELECTRON && (
          <div className="flex items-center gap-0.5">
            <button onClick={() => eb!.goBack()}    className="p-1.5 hover:bg-white/5 rounded text-white/40 hover:text-white/70 transition-all"><ArrowLeft  size={13} /></button>
            <button onClick={() => eb!.goForward()} className="p-1.5 hover:bg-white/5 rounded text-white/40 hover:text-white/70 transition-all"><ArrowRight size={13} /></button>
            <button onClick={() => eb!.reload()}    className="p-1.5 hover:bg-white/5 rounded text-white/40 hover:text-white/70 transition-all"><RefreshCw  size={13} /></button>
          </div>
        )}

        {/* URL bar */}
        <div className="flex-1 flex items-center gap-1.5 px-2.5 py-1 bg-white/5 rounded-lg">
          <Globe size={12} className="text-white/30 shrink-0" />
          {IS_ELECTRON ? (
            <input
              value={urlBarInput}
              onChange={(e) => setUrlBarInput(e.target.value)}
              onKeyDown={handleUrlBarNavigate}
              placeholder="Navigate to a URL..."
              className="bg-transparent text-xs text-white/70 placeholder:text-white/25 outline-none flex-1 min-w-0"
            />
          ) : (
            <span className="text-xs text-white/50 truncate">{pageUrl || 'Browser'}</span>
          )}
        </div>

        {/* Manual/AI mode toggle (web mode only) */}
        {!IS_ELECTRON && (
          <button
            onClick={() => setManualMode(!manualMode)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              manualMode
                ? 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30'
                : 'bg-aria-500/20 text-aria-400 hover:bg-aria-500/30'
            }`}
          >
            {manualMode ? <><Hand size={12} /> Manual</> : <><Sparkles size={12} /> AI</>}
          </button>
        )}

        {/* Phase badge */}
        <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-white/5 shrink-0">
          {phaseIcon()}
          <span className="text-[11px] text-white/50">{phaseLabel()}</span>
        </div>

        <button onClick={onClose} className="p-1.5 hover:bg-white/5 rounded-lg text-white/30 hover:text-white/60 transition-all">
          <X size={14} />
        </button>
      </div>

      {/* ── Content area ─────────────────────────────────────────────────── */}
      <div className="flex-1 relative overflow-hidden">

        {IS_ELECTRON ? (
          // In Electron, the BrowserView sits BEHIND this transparent area.
          // We only render a status bar overlay on top.
          <div className="w-full h-full bg-transparent">
            {/* Status overlay at bottom */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent px-4 py-3 pointer-events-none">
              <div className="flex items-center gap-2">
                {phaseIcon()}
                <span className="text-xs text-white/70">{statusMsg}</span>
              </div>
            </div>
          </div>
        ) : (
          // Web mode: show screenshot frames from Playwright
          <>
            {screenshot ? (
              <img
                ref={imgRef}
                src={`data:image/jpeg;base64,${screenshot}`}
                alt="Browser view"
                onClick={handleScreenshotClick}
                className={`w-full h-full object-contain ${(phase === 'interactive' || manualMode) ? 'cursor-pointer' : 'cursor-default'}`}
                draggable={false}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Globe size={40} className="mx-auto text-white/10 mb-3" />
                  <p className="text-sm text-white/30">{statusMsg}</p>
                </div>
              </div>
            )}

            {/* Status overlay */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent px-4 py-3">
              <div className="flex items-center gap-2">
                {phaseIcon()}
                <span className="text-xs text-white/70">{statusMsg}</span>
              </div>
            </div>

            {phase === 'interactive' && !manualMode && (
              <div className="absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 bg-amber-500/90 text-black rounded-full text-xs font-semibold shadow-lg">
                <MousePointer2 size={14} />
                Click on the page to interact — sign in, then click "I'm done"
              </div>
            )}
          </>
        )}
      </div>

      {/* ── Interactive controls (web mode only — in Electron the user types directly) ── */}
      {!IS_ELECTRON && (phase === 'interactive' || manualMode) && (
        <div className="px-4 py-3 bg-[var(--bg-tertiary)] border-t border-white/5 space-y-2 shrink-0">
          <div className="flex gap-2">
            <div className="flex items-center gap-1.5 px-3 py-2 bg-white/5 rounded-lg flex-1">
              <Keyboard size={14} className="text-white/30" />
              <input
                type="text"
                value={typingInput}
                onChange={(e) => setTypingInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleType(); }}
                placeholder="Type to enter text in the browser..."
                className="bg-transparent text-sm text-white placeholder:text-white/30 outline-none flex-1"
              />
              <button onClick={handleType} className="p-1 hover:bg-white/10 rounded transition-all">
                <Send size={13} className="text-aria-400" />
              </button>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {['Enter ↵', 'Tab ⇥', 'Esc', '⌫'].map((label, i) => (
              <button key={i} onClick={() => handleKey(['Enter','Tab','Escape','Backspace'][i])}
                className="px-3 py-1.5 text-xs bg-white/5 hover:bg-white/10 rounded-lg text-white/60 transition-all"
              >{label}</button>
            ))}
            <div className="flex-1" />
            {phase === 'interactive' && !manualMode && (
              <button onClick={handleResume}
                className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded-lg transition-all"
              ><CheckCircle size={14} /> I'm done, continue</button>
            )}
          </div>
        </div>
      )}

      {/* ── Action log ───────────────────────────────────────────────────── */}
      <details className="bg-[var(--bg-primary)] border-t border-white/5 shrink-0">
        <summary className="px-4 py-2 text-[11px] text-white/30 cursor-pointer hover:text-white/50 select-none">
          Action log ({actionLog.length})
        </summary>
        <div className="max-h-32 overflow-y-auto px-4 pb-2">
          {actionLog.map((entry, i) => (
            <div key={i} className="text-[11px] text-white/30 py-0.5 font-mono">{entry}</div>
          ))}
        </div>
      </details>
    </div>
  );
}
