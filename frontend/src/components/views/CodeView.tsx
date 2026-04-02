import { Code2, Copy, Check, FileCode } from 'lucide-react';
import { useState } from 'react';

interface CodeBlock {
  language: string;
  code: string;
  filename?: string;
}

interface Props {
  data: {
    blocks?: CodeBlock[];
  };
  title?: string;
}

export function CodeView({ data, title }: Props) {
  const blocks = data.blocks || [];
  const [activeTab, setActiveTab] = useState(0);
  const [copied, setCopied] = useState<number | null>(null);

  const handleCopy = async (code: string, index: number) => {
    await navigator.clipboard.writeText(code);
    setCopied(index);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5">
        <Code2 size={20} className="text-aria-400" />
        <h2 className="text-lg font-semibold text-white/90">{title || 'Code'}</h2>
      </div>

      {/* Tabs */}
      {blocks.length > 1 && (
        <div className="flex gap-1 px-6 pt-3 border-b border-white/5">
          {blocks.map((block, i) => (
            <button
              key={i}
              onClick={() => setActiveTab(i)}
              className={`flex items-center gap-2 px-3 py-2 text-xs rounded-t-lg transition-all ${
                activeTab === i
                  ? 'bg-[#1e1e2e] text-white/90 border border-white/10 border-b-transparent'
                  : 'text-white/40 hover:text-white/60 hover:bg-white/[0.03]'
              }`}
            >
              <FileCode size={12} />
              {block.filename || `${block.language || 'code'} #${i + 1}`}
            </button>
          ))}
        </div>
      )}

      {/* Code Content */}
      <div className="flex-1 overflow-auto">
        {blocks.length > 0 ? (
          blocks.map((block, i) => (
            <div
              key={i}
              className={activeTab === i || blocks.length === 1 ? '' : 'hidden'}
            >
              <div className="relative">
                {/* Language badge + copy button */}
                <div className="flex items-center justify-between px-4 py-2 bg-black/30 border-b border-white/5">
                  <span className="text-xs text-white/30 uppercase tracking-wider">
                    {block.language || 'text'}
                  </span>
                  <button
                    onClick={() => handleCopy(block.code, i)}
                    className="flex items-center gap-1 text-xs text-white/30 hover:text-white/70 transition-colors"
                  >
                    {copied === i ? (
                      <>
                        <Check size={12} className="text-emerald-400" /> Copied
                      </>
                    ) : (
                      <>
                        <Copy size={12} /> Copy
                      </>
                    )}
                  </button>
                </div>

                {/* Code block */}
                <pre className="p-4 overflow-x-auto text-sm leading-6 font-mono">
                  <code className="text-white/80">
                    {block.code.split('\n').map((line, li) => (
                      <div key={li} className="flex hover:bg-white/[0.03]">
                        <span className="w-10 inline-block text-right pr-4 text-white/15 select-none flex-shrink-0">
                          {li + 1}
                        </span>
                        <span className="flex-1">{line}</span>
                      </div>
                    ))}
                  </code>
                </pre>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12 text-white/20">
            <Code2 size={40} className="mx-auto mb-3" />
            <p>No code to display</p>
          </div>
        )}
      </div>
    </div>
  );
}
