import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Mic, Bot, User, Loader2 } from 'lucide-react';
import { sendMessage, getMessages, type ChatMessage } from '../api';

interface Props {
  conversationId?: string;
  onConversationCreated: (id: string) => void;
}

export function ChatView({ conversationId, onConversationCreated }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<string>('');
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load existing messages when conversation changes
  useEffect(() => {
    if (conversationId) {
      getMessages(conversationId).then(setMessages).catch(() => {});
    } else {
      setMessages([]);
    }
  }, [conversationId]);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setLoading(true);

    try {
      const resp = await sendMessage(text, conversationId);
      if (!conversationId) {
        onConversationCreated(resp.conversation_id);
      }
      setCurrentAgent(resp.agent);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: resp.content,
          agent: resp.agent,
          model: resp.model,
          tool_calls: resp.tool_calls,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Is the backend running?' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center text-white/20 mt-20">
              <Bot size={48} className="mx-auto mb-4 text-aria-500/30" />
              <p className="text-lg">Start a conversation with Aria</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-aria-600/20 flex items-center justify-center mt-1">
                  <Bot size={16} className="text-aria-400" />
                </div>
              )}

              <div className={`
                max-w-[80%] rounded-2xl px-5 py-3
                ${msg.role === 'user'
                  ? 'bg-aria-600 text-white'
                  : 'bg-[var(--bg-tertiary)] border border-white/5'
                }
              `}>
                {msg.role === 'assistant' && msg.agent && (
                  <span className="text-xs text-aria-400/60 block mb-1">{msg.agent} agent</span>
                )}

                {msg.role === 'assistant' ? (
                  <div className="markdown-content">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p>{msg.content}</p>
                )}

                {msg.tool_calls && msg.tool_calls.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-white/5">
                    <span className="text-xs text-white/30">
                      Tools used: {msg.tool_calls.map((tc: any) => tc.tool).join(', ')}
                    </span>
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white/10 flex items-center justify-center mt-1">
                  <User size={16} className="text-white/60" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-aria-600/20 flex items-center justify-center">
                <Bot size={16} className="text-aria-400" />
              </div>
              <div className="bg-[var(--bg-tertiary)] border border-white/5 rounded-2xl px-5 py-3">
                <Loader2 size={18} className="animate-spin text-aria-400" />
              </div>
            </div>
          )}

          <div ref={scrollRef} />
        </div>
      </div>

      {/* Input bar */}
      <div className="border-t border-white/5 p-4">
        <div className="max-w-3xl mx-auto relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Message Aria..."
            disabled={loading}
            className="w-full bg-[var(--bg-tertiary)] border border-white/10 rounded-2xl px-5 py-3.5 pr-24
                       text-white placeholder:text-white/30 focus:outline-none focus:border-aria-500/50
                       focus:ring-2 focus:ring-aria-500/20 transition-all disabled:opacity-50"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-1">
            <button className="p-2 rounded-xl hover:bg-white/5 text-white/40 hover:text-white/70 transition-all">
              <Mic size={18} />
            </button>
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="p-2 rounded-xl bg-aria-600 hover:bg-aria-500 disabled:opacity-30
                         disabled:hover:bg-aria-600 transition-all"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
        {currentAgent && (
          <p className="text-center text-xs text-white/20 mt-2">
            Handled by <span className="text-aria-400/50">{currentAgent}</span> agent
          </p>
        )}
      </div>
    </div>
  );
}
