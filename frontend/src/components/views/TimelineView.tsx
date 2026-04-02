import { Clock, Milestone, Circle } from 'lucide-react';

interface TimelineEvent {
  date: string;
  title: string;
  description?: string;
  status?: 'completed' | 'current' | 'upcoming';
}

interface Props {
  data: {
    events?: TimelineEvent[];
  };
  title?: string;
}

export function TimelineView({ data, title }: Props) {
  const events = data.events || [];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5">
        <Clock size={20} className="text-aria-400" />
        <h2 className="text-lg font-semibold text-white/90">{title || 'Timeline'}</h2>
        <span className="text-xs text-white/30 ml-auto">{events.length} milestones</span>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-auto px-6 py-6">
        <div className="max-w-2xl mx-auto relative">
          {/* Vertical line */}
          <div className="absolute left-6 top-0 bottom-0 w-px bg-white/10" />

          <div className="space-y-1">
            {events.map((event, i) => {
              const status = event.status || (i === 0 ? 'current' : 'upcoming');
              return (
                <div key={i} className="flex gap-4 group">
                  {/* Dot */}
                  <div className="relative flex-shrink-0 w-12 flex justify-center pt-1.5">
                    <div
                      className={`w-3 h-3 rounded-full z-10 transition-all ${
                        status === 'completed'
                          ? 'bg-emerald-400 ring-4 ring-emerald-400/20'
                          : status === 'current'
                          ? 'bg-aria-400 ring-4 ring-aria-400/20 animate-pulse'
                          : 'bg-white/20 ring-4 ring-white/5'
                      }`}
                    />
                  </div>

                  {/* Content */}
                  <div
                    className={`flex-1 pb-8 border-b border-white/[0.03] group-last:border-0 ${
                      status === 'current' ? '' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-1">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          status === 'completed'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : status === 'current'
                            ? 'bg-aria-600/20 text-aria-400'
                            : 'bg-white/5 text-white/30'
                        }`}
                      >
                        {event.date}
                      </span>
                      {status === 'current' && (
                        <span className="text-[10px] text-aria-400 uppercase tracking-wider">Current</span>
                      )}
                    </div>
                    <h3
                      className={`text-sm font-medium ${
                        status === 'completed'
                          ? 'text-white/50 line-through'
                          : status === 'current'
                          ? 'text-white/90'
                          : 'text-white/60'
                      }`}
                    >
                      {event.title}
                    </h3>
                    {event.description && (
                      <p className="text-xs text-white/30 mt-1 leading-relaxed">
                        {event.description}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}

            {events.length === 0 && (
              <div className="text-center py-12">
                <Milestone size={40} className="mx-auto text-white/10 mb-3" />
                <p className="text-white/30">No timeline events</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
