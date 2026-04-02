/**
 * DashboardRenderer — the core adaptive UI component.
 * 
 * Takes a layout directive from the AI and renders the appropriate
 * view component. This is what makes the dashboard "morph" based
 * on what the user is asking about.
 */

import { X, Maximize2, Minimize2 } from 'lucide-react';
import { useState } from 'react';
import type { LayoutDirective, LayoutType } from '../api';
import { NewsArticleView } from './views/NewsArticleView';
import { CalendarView } from './views/CalendarView';
import { FinanceView } from './views/FinanceView';
import { SearchResultsView } from './views/SearchResultsView';
import { KanbanView } from './views/KanbanView';
import { CodeView } from './views/CodeView';
import { DocumentView } from './views/DocumentView';
import { TimelineView } from './views/TimelineView';
import { DataTableView } from './views/DataTableView';
import { ComparisonView } from './views/ComparisonView';
import { DashboardOverview } from './views/DashboardOverview';
import { EmailInboxView } from './views/EmailInboxView';

interface Props {
  layout: LayoutDirective;
  onClose: () => void;
}

/**
 * Map of layout types to their view components.
 * New views can be added here without touching anything else.
 */
const VIEW_REGISTRY: Record<
  string,
  React.ComponentType<{ data: any; title?: string }>
> = {
  news_article: NewsArticleView,
  email_inbox: EmailInboxView,
  calendar: CalendarView,
  finance: FinanceView,
  search_results: SearchResultsView,
  kanban: KanbanView,
  code: CodeView,
  document: DocumentView,
  timeline: TimelineView,
  data_table: DataTableView,
  comparison: ComparisonView,
  dashboard: DashboardOverview,
};

export function DashboardRenderer({ layout, onClose }: Props) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const ViewComponent = VIEW_REGISTRY[layout.layout];

  if (!ViewComponent) return null;

  return (
    <div
      className={`
        flex flex-col bg-[var(--bg-secondary)] border-l border-white/5
        transition-all duration-300 ease-in-out
        ${isFullscreen ? 'fixed inset-0 z-50' : 'h-full'}
      `}
    >
      {/* Panel toolbar */}
      <div className="flex items-center justify-between px-3 py-2 bg-[var(--bg-primary)] border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <div className="w-2.5 h-2.5 rounded-full bg-rose-500/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/60" />
          </div>
          <span className="text-xs text-white/40 ml-2">{layout.title || layout.layout}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 hover:bg-white/5 rounded transition-all text-white/30 hover:text-white/60"
          >
            {isFullscreen ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
          </button>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-white/5 rounded transition-all text-white/30 hover:text-white/60"
          >
            <X size={12} />
          </button>
        </div>
      </div>

      {/* View content */}
      <div className="flex-1 overflow-hidden">
        <ViewComponent data={layout.data || {}} title={layout.title} />
      </div>
    </div>
  );
}

/**
 * Check if a layout type should trigger the adaptive panel.
 */
export function isAdaptiveLayout(layout?: LayoutDirective): boolean {
  if (!layout) return false;
  return layout.layout !== 'chat' && layout.layout in VIEW_REGISTRY;
}
