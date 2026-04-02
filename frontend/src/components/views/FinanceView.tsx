import { DollarSign, TrendingUp, TrendingDown, PieChart, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface FinanceCategory {
  name: string;
  amount: number;
}

interface Props {
  data: {
    categories?: FinanceCategory[];
    total_amounts?: string[];
    summary?: string;
  };
  title?: string;
}

const COLORS = [
  'bg-aria-500', 'bg-emerald-500', 'bg-amber-500', 'bg-rose-500',
  'bg-violet-500', 'bg-cyan-500', 'bg-orange-500', 'bg-pink-500',
];

export function FinanceView({ data, title }: Props) {
  const categories = data.categories || [];
  const totalSpend = categories.reduce((sum, c) => sum + c.amount, 0);
  const maxAmount = Math.max(...categories.map((c) => c.amount), 1);

  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5">
        <DollarSign size={20} className="text-emerald-400" />
        <h2 className="text-lg font-semibold text-white/90">{title || 'Finances'}</h2>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4 px-6 py-4">
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-white/40">Total Spending</span>
            <TrendingDown size={14} className="text-rose-400" />
          </div>
          <p className="text-2xl font-bold text-white/90">
            ${totalSpend.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </p>
          <span className="text-xs text-rose-400 flex items-center gap-1 mt-1">
            <ArrowDownRight size={10} /> vs last month
          </span>
        </div>

        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-white/40">Categories</span>
            <PieChart size={14} className="text-aria-400" />
          </div>
          <p className="text-2xl font-bold text-white/90">{categories.length}</p>
          <span className="text-xs text-white/30 mt-1 block">tracked items</span>
        </div>

        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-white/40">Largest Expense</span>
            <TrendingUp size={14} className="text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-white/90">
            {categories.length > 0
              ? `$${Math.max(...categories.map((c) => c.amount)).toLocaleString()}`
              : '$0'}
          </p>
          <span className="text-xs text-white/30 mt-1 block">
            {categories.length > 0
              ? categories.reduce((a, b) => (a.amount > b.amount ? a : b)).name
              : 'N/A'}
          </span>
        </div>
      </div>

      {/* Bar Chart */}
      {categories.length > 0 && (
        <div className="px-6 py-4">
          <h3 className="text-sm text-white/50 mb-4">Breakdown</h3>
          <div className="space-y-3">
            {categories.map((cat, i) => (
              <div key={i} className="group">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-white/70 group-hover:text-white/90 transition-colors">
                    {cat.name}
                  </span>
                  <span className="text-white/50">
                    ${cat.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="h-6 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${COLORS[i % COLORS.length]} rounded-full transition-all duration-500 opacity-70 group-hover:opacity-100`}
                    style={{ width: `${(cat.amount / maxAmount) * 100}%` }}
                  />
                </div>
                <div className="text-right text-xs text-white/20 mt-0.5">
                  {((cat.amount / totalSpend) * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      {data.summary && (
        <div className="px-6 py-4 border-t border-white/5">
          <h3 className="text-sm text-white/50 mb-2">Summary</h3>
          <p className="text-sm text-white/60 leading-relaxed">{data.summary}</p>
        </div>
      )}
    </div>
  );
}
