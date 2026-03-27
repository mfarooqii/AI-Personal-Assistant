import { useState, useEffect } from 'react';
import { Plus, MessageSquare, Home, Settings, Brain } from 'lucide-react';
import { getConversations, type Conversation } from '../api';

interface Props {
  onNewChat: () => void;
  onOpenConversation: (id: string) => void;
  onGoHome: () => void;
  activeConversationId?: string;
}

export function Sidebar({ onNewChat, onOpenConversation, onGoHome, activeConversationId }: Props) {
  const [conversations, setConversations] = useState<Conversation[]>([]);

  useEffect(() => {
    getConversations().then(setConversations).catch(() => {});
    // Refresh every 30s
    const interval = setInterval(() => {
      getConversations().then(setConversations).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-full flex flex-col bg-[var(--bg-secondary)] border-r border-white/5">
      {/* Header */}
      <div className="p-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-aria-600/20 flex items-center justify-center">
          <Brain size={16} className="text-aria-400" />
        </div>
        <span className="font-semibold text-aria-400">Aria</span>
      </div>

      {/* Actions */}
      <div className="px-3 space-y-1">
        <button
          onClick={onGoHome}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/5
                     text-white/60 hover:text-white/90 transition-all text-sm"
        >
          <Home size={16} />
          Home
        </button>
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl
                     bg-aria-600/10 hover:bg-aria-600/20 text-aria-400 transition-all text-sm"
        >
          <Plus size={16} />
          New Chat
        </button>
      </div>

      {/* Conversations */}
      <div className="mt-4 px-3 flex-1 overflow-y-auto">
        <p className="text-xs text-white/20 uppercase tracking-wider px-3 mb-2">Recent</p>
        <div className="space-y-0.5">
          {conversations.map((convo) => (
            <button
              key={convo.id}
              onClick={() => onOpenConversation(convo.id)}
              className={`
                w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-left truncate
                transition-all
                ${activeConversationId === convo.id
                  ? 'bg-white/10 text-white'
                  : 'text-white/50 hover:bg-white/5 hover:text-white/80'
                }
              `}
            >
              <MessageSquare size={14} className="flex-shrink-0" />
              <span className="truncate">{convo.title}</span>
            </button>
          ))}
          {conversations.length === 0 && (
            <p className="text-xs text-white/15 px-3 py-4 text-center">No conversations yet</p>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-white/5">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm
                           text-white/40 hover:text-white/70 hover:bg-white/5 transition-all">
          <Settings size={14} />
          Settings
        </button>
      </div>
    </div>
  );
}
