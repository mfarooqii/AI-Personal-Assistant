import { LayoutGrid, TrendingUp, ListTodo, BarChart3, Activity } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface DashboardWidget {
  type: 'text' | 'stat' | 'list' | 'chart';
  title?: string;
  content?: string;
  value?: string;
  items?: string[];
}

interface Props {
  data: {
    widgets?: DashboardWidget[];
  };
  title?: string;
}

const WIDGET_ICONS: Record<string, typeof TrendingUp> = {
  stat: TrendingUp,
  list: ListTodo,
  chart: BarChart3,
  text: Activity,
};

export function DashboardOverview({ data, title }: Props) {
  const widgets = data.widgets || [];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5">
        <LayoutGrid size={20} className="text-aria-400" />
        <h2 className="text-lg font-semibold text-white/90">{title || 'Dashboard'}</h2>
      </div>

      {/* Widgets Grid */}
      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {widgets.map((widget, i) => {
            const Icon = WIDGET_ICONS[widget.type] || Activity;
            return (
              <div
                key={i}
                className={`bg-white/[0.03] rounded-xl border border-white/5 p-5 ${
                  widget.type === 'text' ? 'col-span-full' : ''
                }`}
              >
                <div className="flex items-center gap-2 mb-3">
                  <Icon size={14} className="text-aria-400" />
                  <h3 className="text-sm font-medium text-white/60">
                    {widget.title || widget.type}
                  </h3>
                </div>

                {widget.type === 'stat' && (
                  <p className="text-3xl font-bold text-white/90">{widget.value}</p>
                )}

                {widget.type === 'list' && widget.items && (
                  <ul className="space-y-1.5">
                    {widget.items.map((item, ii) => (
                      <li
                        key={ii}
                        className="flex items-center gap-2 text-sm text-white/60"
                      >
                        <div className="w-1.5 h-1.5 rounded-full bg-aria-500" />
                        {item}
                      </li>
                    ))}
                  </ul>
                )}

                {widget.type === 'text' && widget.content && (
                  <div className="markdown-content text-sm text-white/60 leading-relaxed">
                    <ReactMarkdown>{widget.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            );
          })}

          {widgets.length === 0 && (
            <div className="col-span-full text-center py-12 text-white/20">
              <LayoutGrid size={40} className="mx-auto mb-3" />
              <p>No dashboard data</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
