import { useState, useEffect } from 'react';
import { VoiceOrb } from './VoiceOrb';
import {
  Send, Newspaper, Calendar, CheckSquare, Search, Mail,
  DollarSign, Code, BookOpen, Plane, Bot, Link, Check, ExternalLink, Globe,
} from 'lucide-react';
import { getProfile, getIntegrationStatus, connectGmail, disconnectGmail } from '../api';

interface Props {
  onStartChat: (message: string) => void;
  initialMessage: string;
}

const QUICK_ACTIONS = [
  { icon: Newspaper, label: 'News', prompt: "Show me today's top news", color: 'from-blue-500/20 to-blue-600/10', iconColor: 'text-blue-400' },
  { icon: Calendar, label: 'Schedule', prompt: "What's my schedule this week?", color: 'from-emerald-500/20 to-emerald-600/10', iconColor: 'text-emerald-400' },
  { icon: CheckSquare, label: 'Tasks', prompt: 'Show me my tasks', color: 'from-amber-500/20 to-amber-600/10', iconColor: 'text-amber-400' },
  { icon: Search, label: 'Search', prompt: 'Search the web for ', color: 'from-purple-500/20 to-purple-600/10', iconColor: 'text-purple-400' },
  { icon: Mail, label: 'Email', prompt: 'Show me my unread emails', color: 'from-rose-500/20 to-rose-600/10', iconColor: 'text-rose-400' },
  { icon: DollarSign, label: 'Finance', prompt: "How's my budget this month?", color: 'from-green-500/20 to-green-600/10', iconColor: 'text-green-400' },
  { icon: Code, label: 'Code', prompt: 'Help me write code for ', color: 'from-cyan-500/20 to-cyan-600/10', iconColor: 'text-cyan-400' },
  { icon: BookOpen, label: 'Learn', prompt: 'Teach me about ', color: 'from-indigo-500/20 to-indigo-600/10', iconColor: 'text-indigo-400' },
  { icon: Plane, label: 'Travel', prompt: 'Find flights to ', color: 'from-orange-500/20 to-orange-600/10', iconColor: 'text-orange-400' },
  { icon: Globe, label: 'Browser', prompt: 'Open google.com in the browser', color: 'from-sky-500/20 to-sky-600/10', iconColor: 'text-sky-400' },
];

export function HomeView({ onStartChat }: Props) {
  const [input, setInput] = useState('');
  const [userName, setUserName] = useState('');
  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailConfigured, setGmailConfigured] = useState(false);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    getProfile().then(p => {
      if (p.exists && p.name) setUserName(p.name);
    }).catch(() => {});
    getIntegrationStatus().then(s => {
      setGmailConnected(s.gmail?.connected ?? false);
      setGmailConfigured(s.gmail?.configured ?? false);
    }).catch(() => {});
  }, []);

  const handleGmailConnect = async () => {
    setConnecting(true);
    try {
      const result = await connectGmail();
      if ('auth_url' in result) {
        window.open(result.auth_url, '_blank', 'width=600,height=700');
        // Poll for connection status after OAuth
        const poll = setInterval(async () => {
          const s = await getIntegrationStatus();
          if (s.gmail?.connected) {
            setGmailConnected(true);
            setConnecting(false);
            clearInterval(poll);
          }
        }, 2000);
        // Stop polling after 2 minutes
        setTimeout(() => { clearInterval(poll); setConnecting(false); }, 120000);
      }
    } catch {
      setConnecting(false);
    }
  };

  const handleGmailDisconnect = async () => {
    await disconnectGmail();
    setGmailConnected(false);
  };

  useEffect(() => {
    getProfile().then(p => {
      if (p.exists && p.name) setUserName(p.name);
    }).catch(() => {});
  }, []);

  const handleSubmit = () => {
    if (!input.trim()) return;
    onStartChat(input.trim());
  };

  const handleQuickAction = (prompt: string) => {
    // If prompt ends with a space, it needs user completion — put in input
    if (prompt.endsWith(' ')) {
      setInput(prompt);
      return;
    }
    onStartChat(prompt);
  };

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 overflow-y-auto">
      {/* Voice Orb */}
      <VoiceOrb onTranscript={(text) => setInput(text)} />

      {/* Greeting */}
      <h1 className="mt-8 text-3xl font-light text-white/90">
        {greeting()}{userName ? ', ' : ''}<span className="font-semibold text-aria-400">{userName || 'there'}</span>
      </h1>
      <p className="mt-2 text-white/40 text-center max-w-md">
        What do you need? I'll turn into the right tool.
      </p>

      {/* Input field */}
      <div className="mt-8 w-full max-w-xl relative">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          placeholder="Ask anything or tap a shortcut below..."
          className="w-full bg-[var(--bg-tertiary)] border border-white/10 rounded-2xl px-6 py-4 pr-14
                     text-white placeholder:text-white/30 focus:outline-none focus:border-aria-500/50
                     focus:ring-2 focus:ring-aria-500/20 transition-all"
        />
        <button
          onClick={handleSubmit}
          disabled={!input.trim()}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-xl
                     bg-aria-600 hover:bg-aria-500 disabled:opacity-30 disabled:hover:bg-aria-600
                     transition-all"
        >
          <Send size={18} />
        </button>
      </div>

      {/* Quick actions grid */}
      <div className="mt-8 w-full max-w-2xl">
        <div className="grid grid-cols-3 sm:grid-cols-3 gap-3">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.label}
              onClick={() => handleQuickAction(action.prompt)}
              className={`
                group flex flex-col items-center gap-2 p-4 rounded-2xl
                bg-gradient-to-br ${action.color}
                border border-white/5 hover:border-white/15
                hover:scale-[1.02] active:scale-[0.98]
                transition-all duration-200
              `}
            >
              <action.icon
                size={22}
                className={`${action.iconColor} group-hover:scale-110 transition-transform`}
              />
              <span className="text-xs font-medium text-white/70 group-hover:text-white/90 transition-colors">
                {action.label}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Connected Apps */}
      <div className="mt-6 w-full max-w-2xl">
        <div className="flex items-center gap-2 mb-3">
          <Link size={14} className="text-white/30" />
          <h3 className="text-xs font-medium text-white/30 uppercase tracking-wider">Connected Apps</h3>
        </div>
        <div className="flex gap-3">
          {/* Gmail */}
          <div className="flex items-center gap-3 px-4 py-3 bg-white/[0.03] border border-white/5 rounded-xl flex-1">
            <Mail size={18} className={gmailConnected ? 'text-emerald-400' : 'text-white/30'} />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white/80">Gmail</p>
              <p className="text-xs text-white/30">
                {gmailConnected ? 'Connected' : gmailConfigured ? 'Ready to connect' : 'Not configured'}
              </p>
            </div>
            {gmailConnected ? (
              <button
                onClick={handleGmailDisconnect}
                className="flex items-center gap-1 px-3 py-1.5 text-xs text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 rounded-lg transition-all"
              >
                <Check size={12} /> Connected
              </button>
            ) : gmailConfigured ? (
              <button
                onClick={handleGmailConnect}
                disabled={connecting}
                className="flex items-center gap-1 px-3 py-1.5 text-xs text-aria-400 bg-aria-500/10 hover:bg-aria-500/20 rounded-lg transition-all disabled:opacity-50"
              >
                {connecting ? 'Connecting...' : <><ExternalLink size={12} /> Connect</>}
              </button>
            ) : (
              <span className="text-xs text-white/20 px-3 py-1.5">Setup needed</span>
            )}
          </div>
        </div>
      </div>

      {/* Footer hint */}
      <p className="mt-6 mb-8 text-xs text-white/20 text-center">
        Talk, type, or tap — the screen becomes what you need
      </p>
    </div>
  );
}
