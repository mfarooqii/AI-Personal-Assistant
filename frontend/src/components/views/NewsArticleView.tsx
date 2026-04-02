/**
 * NewsArticleView — Perplexity-style news article layout.
 *
 * Sections:
 *  1. AI Summary     — the model's synthesized takeaways with inline citations
 *  2. Source chips   — clickable citation pills ([1] Source, [2] Source …)
 *  3. Hero article   — hero image, headline, author/date, full body
 *  4. Related        — secondary search result cards
 */

import ReactMarkdown from 'react-markdown';
import { ExternalLink, Globe, Clock, User } from 'lucide-react';

interface Citation {
  title: string;
  url: string;
  source: string;
  published_date?: string;
  snippet?: string;
}

interface Article {
  title?: string;
  url?: string;
  author?: string;
  published_date?: string;
  image?: string;
  description?: string;
  content?: string;
  hostname?: string;
}

interface NewsArticleData {
  ai_summary: string;
  article?: Article;
  citations?: Citation[];
  related?: Citation[];
}

interface Props {
  data: NewsArticleData;
  title?: string;
}

// ── Citation chip ──────────────────────────────────────────────────────────

function CitationChip({ citation, index }: { citation: Citation; index: number }) {
  return (
    <a
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      className="
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
        bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20
        text-xs text-white/60 hover:text-white/90 transition-all no-underline
        cursor-pointer
      "
    >
      <span className="
        inline-flex items-center justify-center w-4 h-4 rounded-full
        bg-blue-500/30 text-blue-300 text-[10px] font-bold shrink-0
      ">
        {index + 1}
      </span>
      <Globe size={10} className="shrink-0 text-white/30" />
      <span className="max-w-[120px] truncate">{citation.source || new URL(citation.url).hostname}</span>
    </a>
  );
}

// ── Related result card ────────────────────────────────────────────────────

function RelatedCard({ item }: { item: Citation }) {
  let hostname = item.source || '';
  try {
    hostname = hostname || new URL(item.url).hostname.replace('www.', '');
  } catch { /* ignore */ }

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="
        flex flex-col gap-1.5 p-3 rounded-xl
        bg-white/4 hover:bg-white/7 border border-white/8 hover:border-white/14
        transition-all no-underline group cursor-pointer
      "
    >
      <p className="text-xs font-medium text-white/80 group-hover:text-white line-clamp-2 leading-snug">
        {item.title}
      </p>
      <div className="flex items-center gap-1.5 text-[10px] text-white/35">
        <Globe size={9} />
        <span>{hostname}</span>
        {item.published_date && (
          <>
            <span>·</span>
            <Clock size={9} />
            <span>{item.published_date}</span>
          </>
        )}
      </div>
      {item.snippet && (
        <p className="text-[11px] text-white/45 line-clamp-2 leading-relaxed">{item.snippet}</p>
      )}
    </a>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export function NewsArticleView({ data, title }: Props) {
  const { ai_summary, article, citations = [], related = [] } = data;

  let articleHostname = '';
  try {
    articleHostname = article?.hostname || (article?.url ? new URL(article.url).hostname.replace('www.', '') : '');
  } catch { /* ignore */ }

  return (
    <div className="h-full overflow-y-auto px-4 py-5 space-y-6 text-sm">

      {/* ── AI Summary ── */}
      <section>
        <div className="flex items-center gap-2 mb-3">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
          <span className="text-xs font-semibold text-blue-400/80 uppercase tracking-widest">AI Summary</span>
        </div>
        <div className="
          prose prose-invert prose-sm max-w-none
          prose-p:text-white/80 prose-p:leading-relaxed
          prose-h2:text-white/90 prose-h2:text-sm prose-h2:font-semibold prose-h2:mt-4 prose-h2:mb-1
          prose-h3:text-white/80 prose-h3:text-xs prose-h3:font-semibold
          prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
          prose-strong:text-white/95
          prose-li:text-white/75
          prose-code:bg-white/8 prose-code:px-1 prose-code:rounded prose-code:text-xs
          [&_p]:mb-3
        ">
          <ReactMarkdown>{ai_summary}</ReactMarkdown>
        </div>
      </section>

      {/* ── Citation chips ── */}
      {citations.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-2.5">
            <div className="w-1.5 h-1.5 rounded-full bg-white/20" />
            <span className="text-xs font-semibold text-white/40 uppercase tracking-widest">Sources</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {citations.map((c, i) => (
              <CitationChip key={c.url || i} citation={c} index={i} />
            ))}
          </div>
        </section>
      )}

      {/* ── Full article (hero layout) ── */}
      {article && (
        <section className="rounded-2xl overflow-hidden bg-white/3 border border-white/8">
          {/* Hero image */}
          {article.image && (
            <div className="relative w-full h-44 overflow-hidden bg-black/20">
              <img
                src={article.image}
                alt={article.title || 'Article image'}
                className="w-full h-full object-cover opacity-80"
                onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
            </div>
          )}

          <div className="p-4 space-y-3">
            {/* Headline */}
            {article.title && (
              <h2 className="text-base font-bold text-white/95 leading-snug">
                {article.title}
              </h2>
            )}

            {/* Meta row */}
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-white/40">
              {articleHostname && (
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-blue-400/70 hover:text-blue-400 no-underline transition-colors"
                >
                  <Globe size={10} />
                  {articleHostname}
                  <ExternalLink size={9} />
                </a>
              )}
              {article.author && (
                <span className="flex items-center gap-1">
                  <User size={10} />
                  {article.author}
                </span>
              )}
              {article.published_date && (
                <span className="flex items-center gap-1">
                  <Clock size={10} />
                  {article.published_date}
                </span>
              )}
            </div>

            {/* Description / lede */}
            {article.description && (
              <p className="text-sm text-white/60 leading-relaxed border-l-2 border-blue-500/40 pl-3 italic">
                {article.description}
              </p>
            )}

            {/* Divider */}
            {article.content && <div className="border-t border-white/5" />}

            {/* Article body */}
            {article.content && (
              <div className="
                prose prose-invert prose-xs max-w-none
                prose-p:text-white/65 prose-p:leading-relaxed prose-p:text-xs
                prose-h2:text-white/80 prose-h2:text-sm
                prose-a:text-blue-400/80 prose-a:no-underline hover:prose-a:underline
                [&_p]:mb-2.5
              ">
                <ReactMarkdown>{article.content.slice(0, 6000)}</ReactMarkdown>
              </div>
            )}
          </div>
        </section>
      )}

      {/* ── Related results ── */}
      {related.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-1.5 h-1.5 rounded-full bg-white/20" />
            <span className="text-xs font-semibold text-white/40 uppercase tracking-widest">Related</span>
          </div>
          <div className="grid grid-cols-1 gap-2">
            {related.map((item, i) => (
              <RelatedCard key={item.url || i} item={item} />
            ))}
          </div>
        </section>
      )}

      {/* Padding at bottom */}
      <div className="h-6" />
    </div>
  );
}
