import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Terminal, RefreshCw, Trash2, Search, Wifi, WifiOff,
  AlertCircle, AlertTriangle, Info, Bug, Server, Globe,
  ChevronDown, ChevronRight, Wrench,
} from 'lucide-react';
import { getBackendLogs, getFrontendLogs, clearLogs } from '../api';
import type { LogEntry, LogFormat } from '../api';

// ── Types ────────────────────────────────────────────────────────────────────

type LogSource  = 'backend' | 'frontend';
type LevelFilter = 'ALL' | 'ERROR' | 'WARNING' | 'INFO' | 'DEBUG';

// ── Level styles ─────────────────────────────────────────────────────────────

const LEVEL_STYLE = {
  ERROR:    { badge: 'bg-red-500/20 text-red-400 border-red-500/40',    row: 'bg-red-500/5 border-l-2 border-l-red-500', icon: AlertCircle,   ic: 'text-red-400',    txt: 'text-red-300/90' },
  CRITICAL: { badge: 'bg-red-600/30 text-red-300 border-red-600/50',    row: 'bg-red-600/8 border-l-2 border-l-red-600', icon: AlertCircle,   ic: 'text-red-300',    txt: 'text-red-200' },
  WARNING:  { badge: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40', row: 'bg-yellow-500/5 border-l-2 border-l-yellow-500', icon: AlertTriangle, ic: 'text-yellow-400', txt: 'text-yellow-300/80' },
  INFO:     { badge: 'bg-blue-500/15 text-blue-400 border-blue-500/30', row: 'border-l-2 border-l-transparent', icon: Info,          ic: 'text-blue-400',   txt: 'text-white/70' },
  DEBUG:    { badge: 'bg-white/5 text-white/20 border-white/8',          row: 'border-l-2 border-l-transparent', icon: Bug,           ic: 'text-white/20',   txt: 'text-white/25' },
  SUCCESS:  { badge: 'bg-green-500/15 text-green-400 border-green-500/30', row: 'border-l-2 border-l-transparent', icon: Info,          ic: 'text-green-400',  txt: 'text-green-300/80' },
} as const;

function s(level: string) {
  return LEVEL_STYLE[level as keyof typeof LEVEL_STYLE] ?? LEVEL_STYLE.INFO;
}

function fmtTime(iso: string): string {
  try { return new Date(iso).toTimeString().slice(0, 8); }
  catch { return '--:--:--'; }
}

// ── Human row  (compact, one-liner) ──────────────────────────────────────────

function HumanRow({ entry, expanded, onToggle }: { entry: LogEntry; expanded: boolean; onToggle: () => void }) {
  const c = s(entry.level);
  const Icon = c.icon;
  const component = entry.component ?? entry.module.split('.').pop() ?? entry.module;
  const timeLabel = entry.time_ago ?? fmtTime(entry.timestamp);

  return (
    <div
      onClick={onToggle}
      className={`${c.row} px-4 py-2 cursor-pointer hover:bg-white/3 transition-colors`}
    >
      <div className="flex items-start gap-3 min-w-0">
        <span className="text-white/25 text-xs font-mono shrink-0 mt-0.5 w-[68px]">{fmtTime(entry.timestamp)}</span>
        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${c.badge} shrink-0 mt-0.5 w-[62px] text-center uppercase`}>{entry.level}</span>
        <span className="text-[11px] px-2 py-0.5 rounded bg-white/5 text-white/35 shrink-0 mt-0.5 max-w-[120px] truncate" title={entry.module}>{component}</span>
        <span className={`text-sm font-mono flex-1 min-w-0 ${c.txt} ${expanded ? 'whitespace-pre-wrap break-all' : 'truncate'}`}>
          {entry.message}
        </span>
        <span className="text-white/15 shrink-0 mt-1">{expanded ? <ChevronDown size={11}/> : <ChevronRight size={11}/>}</span>
      </div>
      {expanded && (
        <div className="mt-2 ml-[167px] text-xs text-white/30 font-mono bg-white/3 rounded p-2.5 space-y-1">
          <div><span className="text-white/15 w-20 inline-block">module</span>{entry.module}</div>
          <div><span className="text-white/15 w-20 inline-block">location</span>{entry.function}:{entry.line}</div>
          <div><span className="text-white/15 w-20 inline-block">time</span>{entry.timestamp}</div>
          <div><span className="text-white/15 w-20 inline-block">id</span>#{entry.id}</div>
          {'stack' in entry && entry.stack && (
            <div><span className="text-white/15 w-20 inline-block align-top">stack</span><span className="whitespace-pre-wrap">{entry.stack}</span></div>
          )}
        </div>
      )}
    </div>
  );
}

// ── AI card  (rich explanation with cause + fix) ─────────────────────────────

function AICard({ entry, expanded, onToggle }: { entry: LogEntry; expanded: boolean; onToggle: () => void }) {
  const c = s(entry.level);
  const Icon = c.icon;
  const component = entry.component ?? entry.module.split('.').pop() ?? entry.module;
  const isError = entry.level === 'ERROR' || entry.level === 'CRITICAL' || entry.level === 'WARNING';

  // Non-actionable INFO in AI mode → compact info row
  if (!isError && !entry.is_actionable) {
    return (
      <div className="px-4 py-1.5 flex items-center gap-3 hover:bg-white/2 cursor-pointer transition-colors border-l-2 border-l-transparent" onClick={onToggle}>
        <span className="text-white/15 text-xs font-mono w-[68px] shrink-0">{fmtTime(entry.timestamp)}</span>
        <Icon size={12} className={`${c.ic} shrink-0`} />
        <span className="text-xs text-white/25 font-mono truncate">{entry.summary ?? entry.message}</span>
        <span className="text-white/10 text-xs shrink-0 ml-auto">{entry.time_ago}</span>
      </div>
    );
  }

  return (
    <div
      onClick={onToggle}
      className={`mx-3 my-1.5 rounded-xl border cursor-pointer transition-all ${
        entry.level === 'ERROR' || entry.level === 'CRITICAL'
          ? 'border-red-500/20 bg-red-500/5 hover:bg-red-500/8'
          : entry.level === 'WARNING'
          ? 'border-yellow-500/20 bg-yellow-500/5 hover:bg-yellow-500/8'
          : 'border-white/8 bg-white/3 hover:bg-white/5'
      }`}
    >
      {/* Card header */}
      <div className="px-4 py-3 flex items-start gap-3">
        <Icon size={16} className={`${c.ic} mt-0.5 shrink-0`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs font-semibold uppercase tracking-wide ${c.ic}`}>{component}</span>
            {entry.is_actionable && (
              <span className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-aria-600/20 text-aria-400 border border-aria-500/30">
                <Wrench size={9}/> Fixable
              </span>
            )}
            <span className="text-white/20 text-xs ml-auto shrink-0">{entry.time_ago}</span>
          </div>
          <p className={`mt-1 text-sm font-medium leading-snug ${c.txt}`}>
            {entry.summary ?? entry.message}
          </p>
        </div>
        <span className="text-white/20 shrink-0">{expanded ? <ChevronDown size={13}/> : <ChevronRight size={13}/>}</span>
      </div>

      {/* Expandable detail */}
      {expanded && (
        <div className="border-t border-white/5 px-4 py-3 space-y-3">
          {entry.likely_cause && (
            <div>
              <p className="text-[11px] text-white/30 uppercase tracking-wider mb-1">Likely cause</p>
              <p className="text-sm text-white/60">{entry.likely_cause}</p>
            </div>
          )}
          {entry.suggested_action && (
            <div>
              <p className="text-[11px] text-white/30 uppercase tracking-wider mb-1">How to fix</p>
              <p className="text-sm font-mono text-green-300/80 bg-green-500/5 rounded px-3 py-2 border border-green-500/10">
                {entry.suggested_action}
              </p>
            </div>
          )}
          {entry.technical_detail && (
            <div>
              <p className="text-[11px] text-white/30 uppercase tracking-wider mb-1">Technical detail</p>
              <p className="text-xs font-mono text-white/25 whitespace-pre-wrap break-all">{entry.technical_detail}</p>
            </div>
          )}
          <p className="text-[10px] text-white/15">#{entry.id} · {entry.module}:{entry.line}</p>
        </div>
      )}
    </div>
  );
}

// ── Raw row  (full technical detail, developer mode) ─────────────────────────

function RawRow({ entry, expanded, onToggle }: { entry: LogEntry; expanded: boolean; onToggle: () => void }) {
  const c = s(entry.level);
  return (
    <div onClick={onToggle} className={`${c.row} px-4 py-1.5 cursor-pointer hover:bg-white/3 transition-colors`}>
      <div className="flex items-start gap-2 min-w-0 font-mono text-xs">
        <span className="text-white/20 shrink-0 w-[50px]">#{entry.id}</span>
        <span className="text-white/20 shrink-0 w-[72px]">{fmtTime(entry.timestamp)}</span>
        <span className={`font-bold shrink-0 w-[64px] ${c.ic}`}>{entry.level}</span>
        <span className="text-white/30 shrink-0 max-w-[180px] truncate">{entry.module}:{entry.line}</span>
        <span className={`flex-1 min-w-0 ${expanded ? 'whitespace-pre-wrap break-all' : 'truncate'} ${c.txt}`}>{entry.message}</span>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

const LEVELS: LevelFilter[] = ['ALL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'];

export function LogsView() {
  const [source,   setSource]   = useState<LogSource>('backend');
  const [format,   setFormat]   = useState<LogFormat>('human');
  const [level,    setLevel]    = useState<LevelFilter>('ALL');
  const [search,   setSearch]   = useState('');
  const [liveMode, setLiveMode] = useState(true);
  const [loading,  setLoading]  = useState(false);
  const [logs,     setLogs]     = useState<LogEntry[]>([]);
  const [lastFetch, setLastFetch] = useState('');
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const bottomRef  = useRef<HTMLDivElement>(null);
  const listRef    = useRef<HTMLDivElement>(null);
  const autoScroll = useRef(true);

  // When switching to AI format default to showing errors/warnings only (more useful)
  const effectiveLevel = (format === 'ai' && level === 'ALL') ? 'ALL' : level;

  const fetchLogs = useCallback(async (showSpinner = false) => {
    if (showSpinner) setLoading(true);
    try {
      const fn = source === 'backend' ? getBackendLogs : getFrontendLogs;
      const data = await fn({ format, limit: 400, level: effectiveLevel, search: search || undefined });
      // backend returns newest-first; reverse → terminal-style oldest-at-top
      setLogs([...data.logs].reverse());
      setLastFetch(new Date().toLocaleTimeString());
    } catch { /* backend may not be ready */ }
    finally { if (showSpinner) setLoading(false); }
  }, [source, format, effectiveLevel, search]);

  useEffect(() => { fetchLogs(true); setExpanded(new Set()); }, [fetchLogs]);

  useEffect(() => {
    if (!liveMode) return;
    const id = setInterval(() => fetchLogs(false), 2000);
    return () => clearInterval(id);
  }, [liveMode, fetchLogs]);

  useEffect(() => {
    if (autoScroll.current) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs.length]);

  const onScroll = () => {
    if (!listRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = listRef.current;
    autoScroll.current = scrollHeight - scrollTop - clientHeight < 100;
  };

  const toggleExpand = (id: number) =>
    setExpanded(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });

  const errorCount = logs.filter(l => l.level === 'ERROR' || l.level === 'CRITICAL').length;
  const warnCount  = logs.filter(l => l.level === 'WARNING').length;

  return (
    <div className="h-full flex flex-col bg-[var(--bg-primary)] overflow-hidden">

      {/* ── Header ── */}
      <div className="border-b border-white/5 px-5 py-3.5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-aria-600/20 flex items-center justify-center">
            <Terminal size={15} className="text-aria-400" />
          </div>
          <div>
            <h1 className="font-semibold text-white/90 text-sm">System Logs</h1>
            <p className="text-xs text-white/30 mt-0.5">
              {logs.length} entries
              {errorCount > 0 && <span className="ml-2 text-red-400">{errorCount} error{errorCount !== 1 ? 's' : ''}</span>}
              {warnCount  > 0 && <span className="ml-2 text-yellow-400">{warnCount} warning{warnCount !== 1 ? 's' : ''}</span>}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {liveMode && <span className="flex items-center gap-1.5 text-xs text-green-400/70 mr-1"><span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"/>Live</span>}
          <button onClick={() => setLiveMode(v => !v)} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all ${liveMode ? 'bg-green-500/10 text-green-400 hover:bg-green-500/20' : 'bg-white/5 text-white/40 hover:bg-white/10'}`}>
            {liveMode ? <Wifi size={13}/> : <WifiOff size={13}/>}{liveMode ? 'Live' : 'Paused'}
          </button>
          <button onClick={() => fetchLogs(true)} disabled={loading} className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/50 hover:text-white/80 transition-all disabled:opacity-40">
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''}/>
          </button>
          <button onClick={async () => { await clearLogs(); setLogs([]); }} className="p-2 rounded-lg bg-white/5 hover:bg-red-500/10 text-white/50 hover:text-red-400 transition-all">
            <Trash2 size={13}/>
          </button>
        </div>
      </div>

      {/* ── Source + Format Bar ── */}
      <div className="border-b border-white/5 px-5 py-2.5 flex items-center gap-4 shrink-0 flex-wrap gap-y-2">

        {/* Source tabs */}
        <div className="flex items-center gap-0.5 bg-white/3 rounded-lg p-1">
          {([['backend', Server], ['frontend', Globe]] as const).map(([src, Icon]) => (
            <button key={src} onClick={() => setSource(src)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-all ${source === src ? 'bg-aria-600/30 text-aria-300' : 'text-white/30 hover:text-white/60'}`}>
              <Icon size={11}/>{src === 'backend' ? 'Backend (Python)' : 'Frontend (Browser)'}
            </button>
          ))}
        </div>

        {/* Format tabs */}
        <div className="flex items-center gap-0.5 bg-white/3 rounded-lg p-1">
          {(['human', 'ai', 'raw'] as LogFormat[]).map(f => (
            <button key={f} onClick={() => setFormat(f)}
              className={`px-3 py-1 rounded text-xs font-medium transition-all ${format === f ? 'bg-white/10 text-white/90' : 'text-white/30 hover:text-white/60'}`}>
              {f === 'human' ? '👁 Human' : f === 'ai' ? '🤖 AI Explained' : '⚙ Raw'}
            </button>
          ))}
        </div>

        {/* Level filter */}
        <div className="flex items-center gap-0.5 bg-white/3 rounded-lg p-1">
          {LEVELS.map(l => (
            <button key={l} onClick={() => setLevel(l)}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${level === l ? 'bg-aria-600/25 text-aria-300' : 'text-white/25 hover:text-white/55'}`}>
              {l}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative flex-1 max-w-xs">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-white/20"/>
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search…"
            className="w-full pl-8 pr-3 py-1.5 bg-white/5 border border-white/5 rounded-lg text-xs text-white/70 placeholder-white/20 focus:outline-none focus:border-aria-500/40 transition-all"/>
        </div>

        {lastFetch && <span className="text-xs text-white/15 ml-auto shrink-0">Updated {lastFetch}</span>}
      </div>

      {/* ── Format description bar ── */}
      {format !== 'raw' && (
        <div className="px-5 py-2 bg-white/[0.02] border-b border-white/5 shrink-0">
          <p className="text-[11px] text-white/25">
            {format === 'human'
              ? 'Human format — technical module paths and HTTP codes translated to plain English'
              : 'AI format — each entry explains what happened, why it happened, and how to fix it'}
          </p>
        </div>
      )}

      {/* ── Log list ── */}
      <div ref={listRef} onScroll={onScroll} className="flex-1 overflow-y-auto">
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-white/20 gap-3">
            <Terminal size={32}/>
            <p className="text-sm">No {source} log entries yet</p>
            <p className="text-xs text-white/12 text-center max-w-xs">
              {source === 'backend'
                ? 'Send a chat message or make an API call — every request is logged here'
                : 'Any console.error, console.warn, or React crash from the browser appears here'}
            </p>
          </div>
        ) : (
          <div className={format === 'ai' ? 'py-2' : 'divide-y divide-white/[0.03]'}>
            {logs.map(entry => {
              const exp = expanded.has(entry.id);
              const toggle = () => toggleExpand(entry.id);
              if (format === 'ai')    return <AICard   key={entry.id} entry={entry} expanded={exp} onToggle={toggle}/>;
              if (format === 'raw')   return <RawRow   key={entry.id} entry={entry} expanded={exp} onToggle={toggle}/>;
              return                         <HumanRow key={entry.id} entry={entry} expanded={exp} onToggle={toggle}/>;
            })}
          </div>
        )}
        <div ref={bottomRef} className="h-4"/>
      </div>
    </div>
  );
}
