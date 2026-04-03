/**
 * frontendLogger — captures browser errors and forwards them to the backend.
 *
 * Intercepts:
 *   - console.error / console.warn
 *   - window.onerror  (uncaught JS exceptions)
 *   - unhandledrejection  (unhandled Promise rejections)
 *   - visibility-change flush on tab close
 *
 * Batches log entries and POSTs them to /api/logs/frontend every 2 seconds
 * to avoid hammering the backend on rapid error bursts.
 */

interface FrontendLogEntry {
  level: 'error' | 'warn' | 'info';
  message: string;
  source?: string;
  line?: number;
  col?: number;
  stack?: string;
  url?: string;
  timestamp?: string;
}

const ENDPOINT = '/api/logs/frontend';
const BATCH_MS  = 2000;

let _queue: FrontendLogEntry[] = [];
let _timer: ReturnType<typeof setTimeout> | null = null;
let _initialized = false;

function enqueue(entry: FrontendLogEntry): void {
  _queue.push({
    ...entry,
    timestamp: new Date().toISOString(),
    url: window.location.pathname,
  });
  if (!_timer) {
    _timer = setTimeout(flush, BATCH_MS);
  }
}

async function flush(): Promise<void> {
  _timer = null;
  if (_queue.length === 0) return;
  const batch = _queue.splice(0, _queue.length);
  try {
    await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(batch),
    });
  } catch {
    // Silently discard — never cause infinite console.error loops from the logger itself
  }
}

/** Shorten a full filename URL to just the component name, e.g. "ChatView.tsx" */
function trimSource(filename?: string): string | undefined {
  if (!filename) return undefined;
  const parts = filename.split('/');
  return parts[parts.length - 1] || filename;
}

export function initFrontendLogger(): void {
  if (_initialized) return;
  _initialized = true;

  // ── intercept console.error ──────────────────────────────────────────────
  const _origError = console.error.bind(console);
  console.error = (...args: unknown[]) => {
    _origError(...args);
    enqueue({ level: 'error', message: args.map(String).join(' ') });
  };

  // ── intercept console.warn ───────────────────────────────────────────────
  const _origWarn = console.warn.bind(console);
  console.warn = (...args: unknown[]) => {
    _origWarn(...args);
    enqueue({ level: 'warn', message: args.map(String).join(' ') });
  };

  // ── uncaught JS exceptions ───────────────────────────────────────────────
  window.addEventListener('error', (e: ErrorEvent) => {
    enqueue({
      level:   'error',
      message: e.message || 'Uncaught JavaScript error',
      source:  trimSource(e.filename),
      line:    e.lineno  || undefined,
      col:     e.colno   || undefined,
      stack:   e.error?.stack,
    });
  });

  // ── unhandled Promise rejections ─────────────────────────────────────────
  window.addEventListener('unhandledrejection', (e: PromiseRejectionEvent) => {
    const msg = e.reason instanceof Error
      ? e.reason.message
      : String(e.reason ?? 'Unknown rejection');
    enqueue({
      level:   'error',
      message: `Unhandled Promise: ${msg}`,
      stack:   e.reason instanceof Error ? e.reason.stack : undefined,
    });
  });

  // ── flush when user leaves / hides tab ──────────────────────────────────
  window.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') void flush();
  });
}
