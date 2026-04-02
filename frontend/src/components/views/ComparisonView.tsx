import { Columns, ArrowLeftRight } from 'lucide-react';

interface ComparisonItem {
  name: string;
  features: Record<string, string>;
  price?: string;
  rating?: string;
  image?: string;
}

interface Props {
  data: {
    items?: ComparisonItem[];
    raw_content?: string;
  };
  title?: string;
}

export function ComparisonView({ data, title }: Props) {
  const items = data.items || [];

  // If we have raw_content but no structured items, show it as a document
  if (items.length === 0 && data.raw_content) {
    const allFeatures = new Set<string>();
    items.forEach((item) => Object.keys(item.features || {}).forEach((f) => allFeatures.add(f)));

    return (
      <div className="flex flex-col h-full">
        <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5">
          <Columns size={20} className="text-aria-400" />
          <h2 className="text-lg font-semibold text-white/90">{title || 'Comparison'}</h2>
        </div>
        <div className="flex-1 overflow-auto p-6">
          <pre className="text-sm text-white/60 whitespace-pre-wrap leading-relaxed">{data.raw_content}</pre>
        </div>
      </div>
    );
  }

  const allFeatures = [...new Set(items.flatMap((item) => Object.keys(item.features || {})))];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5">
        <Columns size={20} className="text-aria-400" />
        <h2 className="text-lg font-semibold text-white/90">{title || 'Comparison'}</h2>
        <ArrowLeftRight size={14} className="text-white/30 ml-auto" />
        <span className="text-xs text-white/30">{items.length} items</span>
      </div>

      {/* Comparison Table */}
      <div className="flex-1 overflow-auto">
        {items.length > 0 ? (
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="px-4 py-3 text-left text-xs text-white/30 uppercase tracking-wider w-40">
                  Feature
                </th>
                {items.map((item, i) => (
                  <th key={i} className="px-4 py-3 text-center">
                    <div className="text-sm font-medium text-white/90">{item.name}</div>
                    {item.price && (
                      <span className="text-xs text-emerald-400 mt-1 block">{item.price}</span>
                    )}
                    {item.rating && (
                      <span className="text-xs text-amber-400 mt-0.5 block">★ {item.rating}</span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allFeatures.map((feature, fi) => (
                <tr
                  key={fi}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                >
                  <td className="px-4 py-3 text-sm text-white/50">{feature}</td>
                  {items.map((item, ii) => (
                    <td key={ii} className="px-4 py-3 text-sm text-white/70 text-center">
                      {item.features?.[feature] || '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-12 text-white/20">
            <Columns size={40} className="mx-auto mb-3" />
            <p>No comparison data</p>
          </div>
        )}
      </div>
    </div>
  );
}
