import { Search, ExternalLink, Globe, Image } from 'lucide-react';

interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  source?: string;
  image?: string;
  price?: string;
}

interface Props {
  data: {
    results?: SearchResult[];
    query?: string;
  };
  title?: string;
}

export function SearchResultsView({ data, title }: Props) {
  const results = data.results || [];

  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Search Header */}
      <div className="px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-3 mb-3">
          <Search size={20} className="text-aria-400" />
          <h2 className="text-lg font-semibold text-white/90">{title || 'Search Results'}</h2>
        </div>
        {data.query && (
          <div className="flex items-center gap-2 px-4 py-2 bg-white/[0.03] rounded-xl border border-white/5">
            <Search size={14} className="text-white/30" />
            <span className="text-sm text-white/60">{data.query}</span>
          </div>
        )}
        <p className="text-xs text-white/30 mt-2">{results.length} results found</p>
      </div>

      {/* Results Grid */}
      <div className="flex-1 px-6 py-4">
        {results.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {results.map((result, i) => (
              <a
                key={i}
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group block bg-white/[0.03] rounded-xl border border-white/5 p-4 
                           hover:border-aria-500/30 hover:bg-white/[0.05] transition-all"
              >
                {/* Source URL */}
                <div className="flex items-center gap-2 mb-2">
                  <Globe size={12} className="text-white/30" />
                  <span className="text-xs text-white/30 truncate">
                    {result.source || new URL(result.url || 'https://example.com').hostname}
                  </span>
                  <ExternalLink
                    size={10}
                    className="text-white/20 group-hover:text-aria-400 transition-colors ml-auto flex-shrink-0"
                  />
                </div>

                {/* Title */}
                <h3 className="text-sm font-medium text-aria-400 group-hover:text-aria-300 transition-colors mb-1.5 line-clamp-2">
                  {result.title}
                </h3>

                {/* Price tag if available */}
                {result.price && (
                  <span className="inline-block bg-emerald-500/20 text-emerald-400 text-xs px-2 py-0.5 rounded-full mb-2">
                    {result.price}
                  </span>
                )}

                {/* Snippet */}
                <p className="text-xs text-white/40 leading-relaxed line-clamp-3">
                  {result.snippet}
                </p>
              </a>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Search size={40} className="mx-auto text-white/10 mb-3" />
            <p className="text-white/30">No results to display</p>
          </div>
        )}
      </div>
    </div>
  );
}
