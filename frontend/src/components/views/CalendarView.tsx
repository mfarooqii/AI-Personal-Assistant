import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  Bell,
  RotateCcw,
} from 'lucide-react';
import { useState } from 'react';

interface CalendarEvent {
  title: string;
  time?: string;
  type?: string;
  recurring?: boolean;
  date?: string;
}

interface Props {
  data: {
    events?: CalendarEvent[];
    view_mode?: 'day' | 'week' | 'month';
    today?: string;
  };
  title?: string;
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const HOURS = Array.from({ length: 14 }, (_, i) => i + 7); // 7am to 8pm

export function CalendarView({ data, title }: Props) {
  const [viewMode, setViewMode] = useState<'day' | 'week' | 'month'>(
    data.view_mode || 'week'
  );
  const events = data.events || [];
  const today = data.today || new Date().toISOString().split('T')[0];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <Calendar size={20} className="text-aria-400" />
          <h2 className="text-lg font-semibold text-white/90">{title || 'Schedule'}</h2>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-1.5 hover:bg-white/5 rounded-lg transition-all">
            <ChevronLeft size={16} className="text-white/50" />
          </button>
          <span className="text-sm text-white/60 min-w-[120px] text-center">{today}</span>
          <button className="p-1.5 hover:bg-white/5 rounded-lg transition-all">
            <ChevronRight size={16} className="text-white/50" />
          </button>
          <div className="ml-4 flex bg-white/5 rounded-lg p-0.5">
            {(['day', 'week', 'month'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setViewMode(m)}
                className={`px-3 py-1 rounded-md text-xs transition-all ${
                  viewMode === m
                    ? 'bg-aria-600 text-white'
                    : 'text-white/40 hover:text-white/70'
                }`}
              >
                {m.charAt(0).toUpperCase() + m.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="flex-1 overflow-auto">
        {viewMode === 'week' && (
          <div className="grid grid-cols-8 h-full">
            {/* Time column */}
            <div className="border-r border-white/5">
              {HOURS.map((h) => (
                <div
                  key={h}
                  className="h-16 flex items-start justify-end pr-3 pt-1 text-xs text-white/30"
                >
                  {h > 12 ? h - 12 : h} {h >= 12 ? 'PM' : 'AM'}
                </div>
              ))}
            </div>
            {/* Day columns */}
            {DAYS.map((day, di) => (
              <div key={day} className="border-r border-white/5 relative">
                <div className="text-center py-2 text-xs text-white/40 border-b border-white/5 sticky top-0 bg-[var(--bg-secondary)] z-10">
                  {day}
                </div>
                {HOURS.map((h) => (
                  <div
                    key={h}
                    className="h-16 border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                  />
                ))}
                {/* Overlay events for this day */}
                {events
                  .filter((_, i) => i % 7 === di)
                  .map((evt, i) => (
                    <div
                      key={i}
                      className="absolute left-1 right-1 bg-aria-600/20 border border-aria-500/30 rounded-lg px-2 py-1 text-xs"
                      style={{ top: `${44 + (i * 64) + 32}px`, minHeight: '48px' }}
                    >
                      <div className="font-medium text-aria-300 truncate">{evt.title}</div>
                      {evt.time && (
                        <div className="text-white/40 flex items-center gap-1 mt-0.5">
                          <Clock size={10} /> {evt.time}
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            ))}
          </div>
        )}

        {viewMode === 'day' && (
          <div className="max-w-2xl mx-auto">
            {HOURS.map((h) => (
              <div key={h} className="flex border-b border-white/[0.03]">
                <div className="w-20 text-right pr-4 py-3 text-xs text-white/30">
                  {h > 12 ? h - 12 : h}:00 {h >= 12 ? 'PM' : 'AM'}
                </div>
                <div className="flex-1 py-2 pl-4 min-h-[64px] hover:bg-white/[0.02] transition-colors">
                  {events
                    .filter((e) => {
                      if (!e.time) return false;
                      const match = e.time.match(/(\d+)/);
                      return match && parseInt(match[1]) === (h > 12 ? h - 12 : h);
                    })
                    .map((evt, i) => (
                      <div
                        key={i}
                        className="bg-aria-600/20 border border-aria-500/30 rounded-lg px-3 py-2 mb-1"
                      >
                        <div className="flex items-center gap-2">
                          {evt.type === 'reminder' ? (
                            <Bell size={12} className="text-yellow-400" />
                          ) : (
                            <Calendar size={12} className="text-aria-400" />
                          )}
                          <span className="text-sm text-white/90">{evt.title}</span>
                          {evt.recurring && <RotateCcw size={10} className="text-white/30" />}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {viewMode === 'month' && (
          <div className="grid grid-cols-7 gap-px bg-white/5 p-px">
            {DAYS.map((day) => (
              <div
                key={day}
                className="text-center py-2 text-xs text-white/40 bg-[var(--bg-secondary)]"
              >
                {day}
              </div>
            ))}
            {Array.from({ length: 35 }, (_, i) => {
              const dayNum = i - 2; // offset for month start
              const dayEvents = events.filter((_, ei) => ei % 35 === i);
              return (
                <div
                  key={i}
                  className="bg-[var(--bg-secondary)] min-h-[80px] p-1.5 hover:bg-white/[0.02] transition-colors"
                >
                  <span
                    className={`text-xs ${
                      dayNum >= 1 && dayNum <= 31 ? 'text-white/50' : 'text-white/10'
                    }`}
                  >
                    {dayNum >= 1 && dayNum <= 31 ? dayNum : ''}
                  </span>
                  {dayEvents.map((evt, ei) => (
                    <div
                      key={ei}
                      className="mt-0.5 text-[10px] bg-aria-600/20 text-aria-300 rounded px-1 py-0.5 truncate"
                    >
                      {evt.title}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Events list */}
      {events.length > 0 && (
        <div className="border-t border-white/5 px-6 py-3 max-h-[200px] overflow-y-auto">
          <p className="text-xs text-white/30 uppercase tracking-wider mb-2">Events</p>
          <div className="space-y-1.5">
            {events.map((evt, i) => (
              <div
                key={i}
                className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] transition-all"
              >
                {evt.type === 'reminder' ? (
                  <Bell size={14} className="text-yellow-400 flex-shrink-0" />
                ) : (
                  <Calendar size={14} className="text-aria-400 flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <span className="text-sm text-white/80 truncate block">{evt.title}</span>
                </div>
                {evt.time && (
                  <span className="text-xs text-white/30 flex-shrink-0">{evt.time}</span>
                )}
                {evt.recurring && <RotateCcw size={12} className="text-white/20 flex-shrink-0" />}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
