import { FileText, Bookmark, Share2, Printer } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Props {
  data: {
    raw_content?: string;
    content?: string;
    sections?: { title: string; content: string }[];
  };
  title?: string;
}

export function DocumentView({ data, title }: Props) {
  const content = data.raw_content || data.content || '';
  const sections = data.sections || [];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <FileText size={20} className="text-aria-400" />
          <h2 className="text-lg font-semibold text-white/90">{title || 'Document'}</h2>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-white/5 rounded-lg transition-all text-white/30 hover:text-white/60">
            <Bookmark size={16} />
          </button>
          <button className="p-2 hover:bg-white/5 rounded-lg transition-all text-white/30 hover:text-white/60">
            <Share2 size={16} />
          </button>
          <button className="p-2 hover:bg-white/5 rounded-lg transition-all text-white/30 hover:text-white/60">
            <Printer size={16} />
          </button>
        </div>
      </div>

      {/* Document Content */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-3xl mx-auto px-8 py-6">
          {sections.length > 0 ? (
            <div className="space-y-8">
              {sections.map((section, i) => (
                <div key={i}>
                  <h2 className="text-xl font-semibold text-white/90 mb-3 pb-2 border-b border-white/5">
                    {section.title}
                  </h2>
                  <div className="markdown-content text-white/70 leading-relaxed">
                    <ReactMarkdown>{section.content}</ReactMarkdown>
                  </div>
                </div>
              ))}
            </div>
          ) : content ? (
            <div className="markdown-content text-white/70 leading-relaxed">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          ) : (
            <div className="text-center py-12 text-white/20">
              <FileText size={40} className="mx-auto mb-3" />
              <p>No content to display</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
