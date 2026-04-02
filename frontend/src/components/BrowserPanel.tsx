/**
 * BrowserPanel — in-app browser view powered by AI.
 *
 * Shows a live screenshot of the Playwright browser on the backend.
 * The user can click on the screenshot (coordinates are mapped and sent
 * to the backend) and type via a floating input bar.
 *
 * During login flows the panel is "interactive" — clicks and keystrokes
 * go straight to the browser.  Once the AI takes over it becomes a
 * spectator view with narrated status messages.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Globe, Loader2, MousePointer2, Keyboard, ArrowLeft,
  RefreshCw, X, CheckCircle, AlertCircle, Bot, ChevronRight,
  Monitor, Send, Hand, Sparkles,
} from 'lucide-react';

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
  const [phase, setPhase] = useState<Phase>('connecting');
  const [manualMode, setManualMode] = useState(false); // User control vs AI control
  const [screenshot, setScreenshot] = useState<string>('');
  const [statusMsg, setStatusMsg] = useState('Connecting to browser...');
  const [pageUrl, setPageUrl] = useState('');
  const [pageTitle, setPageTitle] = useState('');
  const [typingInput, setTypingInput] = useState('');
  const [actionLog, setActionLog] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  // ── WebSocket connection ─────────────────────────────
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.host}/api/browser/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      // Send task/plan so the backend knows what to do (fallback if global state wasn't set)
      ws.send(JSON.stringify({ task, plan }));
      setPhase('browsing');
      setStatusMsg('Browser connected. Starting task...');
    };

    ws.onmessage = (ev) => {
      try {
        const event: BrowserEvent = JSON.parse(ev.data);
        handleEvent(event);
      } catch { /* ignore parse errors */ }
    };

    ws.onerror = () => {
      setPhase('error');
      setStatusMsg('Failed to connect to browser.');
    };

    ws.onclose = () => {
      if (phase !== 'complete' && phase !== 'error') {
        setStatusMsg('Browser connection closed.');
      }
    };

    return () => {
      ws.close();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Event handler ────────────────────────────────────
  const handleEvent = useCallback((event: BrowserEvent) => {
    if (event.screenshot) {
      setScreenshot(event.screenshot);
    }
    if (event.url) setPageUrl(event.url);
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
        if (event.data) {
          onResult(event.data);
        }
        break;
      case 'error':
        setPhase('error');
        setStatusMsg(event.message || 'Something went wrong.');
        break;
    }
  }, [onResult]);

  // ── User interactions ────────────────────────────────
  const sendWs = (data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  };

  const handleScreenshotClick = (e: React.MouseEvent<HTMLImageElement>) => {
    // Allow clicks in interactive phase OR manual mode
    if (phase !== 'interactive' && !manualMode) return;
    const img = imgRef.current;
    if (!img) return;

    const rect = img.getBoundingClientRect();
    // Map click position to 1280×720 viewport coordinates
    const scaleX = 1280 / rect.width;
    const scaleY = 720 / rect.height;
    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    sendWs({ type: 'click', x, y });
    setActionLog(prev => [...prev.slice(-20), `[You] Clicked at (${x}, ${y})`]);
  };

  const handleType = () => {
    if (!typingInput.trim()) return;
    sendWs({ type: 'type', text: typingInput });
    setActionLog(prev => [...prev.slice(-20), `[You] Typed: "${typingInput}"`]);
    setTypingInput('');
  };

  const handleKey = (key: string) => {
    sendWs({ type: 'key', key });
    setActionLog(prev => [...prev.slice(-20), `[You] Pressed: ${key}`]);
  };

  const handleResume = () => {
    sendWs({ type: 'resume' });
    setPhase('browsing');
    setStatusMsg('Resuming task...');
  };

  // ── Phase indicator ──────────────────────────────────
  const phaseIcon = () => {
    switch (phase) {
      case 'connecting': return <Loader2 size={14} className="animate-spin text-white/40" />;
      case 'browsing':   return <Bot size={14} className="text-aria-400 animate-pulse" />;
      case 'interactive':return <MousePointer2 size={14} className="text-amber-400" />;
      case 'extracting': return <Loader2 size={14} className="animate-spin text-emerald-400" />;
      case 'complete':   return <CheckCircle size={14} className="text-emerald-400" />;
      case 'error':      return <AlertCircle size={14} className="text-red-400" />;
    }
  };

  const phaseLabel = () => {
    switch (phase) {
      case 'connecting': return 'Connecting';
      case 'browsing':   return 'AI Browsing';
      case 'interactive':return 'Your Turn';
      case 'extracting': return 'Extracting';
      case 'complete':   return 'Complete';
      case 'error':      return 'Error';
    }
  };

  return (
    <div className="flex flex-col h-full bg-[var(--bg-secondary)]">
      {/* ── Top toolbar ───────────────────────────── */}
      <div className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-primary)] border-b border-white/5">
        <Monitor size={16} className="text-aria-400" />
        <span className="text-xs text-white/50 truncate flex-1">
          {pageUrl || 'Browser'}
        </span>
        
        {/* Manual/AI mode toggle */}
        <button
          onClick={() => setManualMode(!manualMode)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            manualMode
              ? 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30'
              : 'bg-aria-500/20 text-aria-400 hover:bg-aria-500/30'
          }`}
        >
          {manualMode ? (
            <>
              <Hand size={13} />
              Manual
            </>
          ) : (
            <>
              <Sparkles size={13} />
              AI
            </>
          )}
        </button>

        <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-white/5">
          {phaseIcon()}
          <span className="text-[11px] text-white/50">{phaseLabel()}</span>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 hover:bg-white/5 rounded-lg text-white/30 hover:text-white/60 transition-all"
        >
          <X size={14} />
        </button>
      </div>

      {/* ── Screenshot viewport ───────────────────── */}
      <div className="flex-1 relative overflow-hidden bg-black/30">
        {screenshot ? (
          <img
            ref={imgRef}
            src={`data:image/jpeg;base64,${screenshot}`}
            alt="Browser view"
            onClick={handleScreenshotClick}
            className={`w-full h-full object-contain ${
              (phase === 'interactive' || manualMode) ? 'cursor-pointer' : 'cursor-default'
            }`}
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

        {/* Interactive mode badge */}
        {phase === 'interactive' && !manualMode && (
          <div className="absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 bg-amber-500/90 text-black rounded-full text-xs font-semibold shadow-lg">
            <MousePointer2 size={14} />
            Click on the page to interact — sign in, then click "I'm done"
          </div>
        )}

        {/* Manual mode badge */}
        {manualMode && (
          <div className="absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 bg-amber-500/90 text-black rounded-full text-xs font-semibold shadow-lg">
            <Hand size={14} />
            Manual Mode — Browse freely, click "Let AI Drive" when done
          </div>
        )}
      </div>

      {/* ── Interactive controls (login flow OR manual mode) ─────── */}
      {(phase === 'interactive' || manualMode) && (
        <div className="px-4 py-3 bg-[var(--bg-tertiary)] border-t border-white/5 space-y-2">
          {/* Typing input */}
          <div className="flex gap-2">
            <div className="flex items-center gap-1.5 px-3 py-2 bg-white/5 rounded-lg flex-1">
              <Keyboard size={14} className="text-white/30" />
              <input
                type="text"
                value={typingInput}
                onChange={(e) => setTypingInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleType();
                }}
                placeholder="Type here to enter text in the browser..."
                className="bg-transparent text-sm text-white placeholder:text-white/30 outline-none flex-1"
              />
              <button onClick={handleType} className="p-1 hover:bg-white/10 rounded transition-all">
                <Send size={13} className="text-aria-400" />
              </button>
            </div>
          </div>

          {/* Quick keys + resume */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleKey('Enter')}
              className="px-3 py-1.5 text-xs bg-white/5 hover:bg-white/10 rounded-lg text-white/60 transition-all"
            >
              Enter ↵
            </button>
            <button
              onClick={() => handleKey('Tab')}
              className="px-3 py-1.5 text-xs bg-white/5 hover:bg-white/10 rounded-lg text-white/60 transition-all"
            >
              Tab ⇥
            </button>
            <button
              onClick={() => handleKey('Escape')}
              className="px-3 py-1.5 text-xs bg-white/5 hover:bg-white/10 rounded-lg text-white/60 transition-all"
            >
              Esc
            </button>
            <button
              onClick={() => handleKey('Backspace')}
              className="px-3 py-1.5 text-xs bg-white/5 hover:bg-white/10 rounded-lg text-white/60 transition-all"
            >
              ⌫
            </button>
            <div className="flex-1" />
            
            {/* Show "I'm done" button only during AI-triggered interactive mode, not manual mode */}
            {phase === 'interactive' && !manualMode && (
              <button
                onClick={handleResume}
                className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded-lg transition-all"
              >
                <CheckCircle size={14} /> I'm done, continue
              </button>
            )}
          </div>
        </div>
      )}

      {/* ── Action log (collapsible) ──────────────── */}
      <details className="bg-[var(--bg-primary)] border-t border-white/5">
        <summary className="px-4 py-2 text-[11px] text-white/30 cursor-pointer hover:text-white/50 select-none">
          Action log ({actionLog.length} actions)
        </summary>
        <div className="max-h-32 overflow-y-auto px-4 pb-2">
          {actionLog.map((entry, i) => (
            <div key={i} className="text-[11px] text-white/30 py-0.5 font-mono">
              {entry}
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}
