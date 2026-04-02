import { LayoutDashboard, GripVertical, Circle, CheckCircle2, Clock } from 'lucide-react';

interface KanbanCard {
  title: string;
  priority?: string;
  assignee?: string;
  labels?: string[];
}

interface Props {
  data: {
    columns?: {
      todo?: KanbanCard[];
      in_progress?: KanbanCard[];
      done?: KanbanCard[];
    };
  };
  title?: string;
}

const COLUMN_CONFIG = [
  { key: 'todo', label: 'To Do', icon: Circle, color: 'text-white/40', accent: 'bg-white/10' },
  { key: 'in_progress', label: 'In Progress', icon: Clock, color: 'text-amber-400', accent: 'bg-amber-500/10' },
  { key: 'done', label: 'Done', icon: CheckCircle2, color: 'text-emerald-400', accent: 'bg-emerald-500/10' },
] as const;

const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-rose-500/20 text-rose-400',
  medium: 'bg-amber-500/20 text-amber-400',
  normal: 'bg-white/10 text-white/40',
  low: 'bg-white/5 text-white/30',
};

export function KanbanView({ data, title }: Props) {
  const columns = data.columns || { todo: [], in_progress: [], done: [] };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5">
        <LayoutDashboard size={20} className="text-aria-400" />
        <h2 className="text-lg font-semibold text-white/90">{title || 'Task Board'}</h2>
        <span className="text-xs text-white/30 ml-auto">
          {Object.values(columns).flat().length} tasks
        </span>
      </div>

      {/* Kanban Board */}
      <div className="flex-1 overflow-x-auto">
        <div className="flex gap-4 p-6 min-w-max h-full">
          {COLUMN_CONFIG.map(({ key, label, icon: Icon, color, accent }) => {
            const cards = columns[key] || [];
            return (
              <div
                key={key}
                className="w-72 flex flex-col bg-white/[0.02] rounded-xl border border-white/5 flex-shrink-0"
              >
                {/* Column Header */}
                <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
                  <Icon size={14} className={color} />
                  <span className="text-sm font-medium text-white/70">{label}</span>
                  <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${accent} ${color}`}>
                    {cards.length}
                  </span>
                </div>

                {/* Cards */}
                <div className="flex-1 p-2 space-y-2 overflow-y-auto">
                  {cards.map((card, i) => (
                    <div
                      key={i}
                      className="group bg-[var(--bg-secondary)] rounded-lg border border-white/5 
                                 p-3 hover:border-white/10 transition-all cursor-pointer"
                    >
                      <div className="flex items-start gap-2">
                        <GripVertical
                          size={12}
                          className="text-white/10 group-hover:text-white/30 mt-1 flex-shrink-0 transition-colors"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white/80 leading-snug">{card.title}</p>
                          <div className="flex items-center gap-2 mt-2">
                            {card.priority && (
                              <span
                                className={`text-[10px] px-1.5 py-0.5 rounded ${
                                  PRIORITY_COLORS[card.priority] || PRIORITY_COLORS.normal
                                }`}
                              >
                                {card.priority}
                              </span>
                            )}
                            {card.labels?.map((label, li) => (
                              <span
                                key={li}
                                className="text-[10px] px-1.5 py-0.5 rounded bg-aria-600/20 text-aria-400"
                              >
                                {label}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {cards.length === 0 && (
                    <div className="text-center py-8 text-xs text-white/15">
                      No tasks
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
