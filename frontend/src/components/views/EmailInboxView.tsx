import { useState } from 'react';
import {
  Mail, MailOpen, ArrowLeft, Send, Star, Clock, User,
  Search, Inbox, Archive, Trash2,
} from 'lucide-react';

interface EmailItem {
  id: string;
  thread_id?: string;
  subject: string;
  from: string;
  to?: string;
  date: string;
  snippet: string;
  body?: string;
  is_unread: boolean;
  labels?: string[];
}

interface Props {
  data: {
    emails?: EmailItem[];
    total?: number;
    query?: string;
    ai_summary?: string;
  };
  title?: string;
}

function formatSender(from: string): { name: string; email: string } {
  const match = from.match(/^(.+?)\s*<(.+?)>$/);
  if (match) return { name: match[1].trim(), email: match[2] };
  return { name: from, email: from };
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const days = Math.floor(diff / 86400000);

    if (days === 0) {
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    if (days === 1) return 'Yesterday';
    if (days < 7) return d.toLocaleDateString([], { weekday: 'short' });
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
}

function senderInitial(name: string): string {
  return name.charAt(0).toUpperCase();
}

const LABEL_COLORS: Record<string, string> = {
  INBOX: 'bg-blue-500/20 text-blue-300',
  IMPORTANT: 'bg-amber-500/20 text-amber-300',
  STARRED: 'bg-yellow-500/20 text-yellow-300',
  SENT: 'bg-emerald-500/20 text-emerald-300',
  DRAFT: 'bg-gray-500/20 text-gray-300',
  SPAM: 'bg-red-500/20 text-red-300',
  TRASH: 'bg-red-500/20 text-red-300',
  CATEGORY_SOCIAL: 'bg-purple-500/20 text-purple-300',
  CATEGORY_PROMOTIONS: 'bg-green-500/20 text-green-300',
  CATEGORY_UPDATES: 'bg-cyan-500/20 text-cyan-300',
};

export function EmailInboxView({ data, title }: Props) {
  const [selectedEmail, setSelectedEmail] = useState<EmailItem | null>(null);
  const emails = data.emails || [];

  if (selectedEmail) {
    return <EmailDetailView email={selectedEmail} onBack={() => setSelectedEmail(null)} />;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <Mail size={20} className="text-aria-400" />
          <h2 className="text-lg font-semibold text-white/90">{title || 'Email'}</h2>
          {data.total != null && (
            <span className="text-xs text-white/40 bg-white/5 px-2 py-0.5 rounded-full">
              {data.total}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-white/50 hover:text-white/80 bg-white/5 hover:bg-white/10 rounded-lg transition-all">
            <Inbox size={13} /> Inbox
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-white/50 hover:text-white/80 bg-white/5 hover:bg-white/10 rounded-lg transition-all">
            <Send size={13} /> Sent
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-white/50 hover:text-white/80 bg-white/5 hover:bg-white/10 rounded-lg transition-all">
            <Archive size={13} /> Archive
          </button>
        </div>
      </div>

      {/* AI Summary */}
      {data.ai_summary && (
        <div className="mx-6 mt-4 p-4 bg-aria-500/5 border border-aria-500/20 rounded-xl">
          <p className="text-sm text-white/70 leading-relaxed">{data.ai_summary}</p>
        </div>
      )}

      {/* Email List */}
      <div className="flex-1 overflow-y-auto">
        {emails.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-white/30">
            <MailOpen size={40} className="mb-3" />
            <p className="text-sm">No emails found</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {emails.map((email) => {
              const sender = formatSender(email.from);
              return (
                <button
                  key={email.id}
                  onClick={() => setSelectedEmail(email)}
                  className={`w-full text-left px-6 py-4 hover:bg-white/[0.03] transition-all group
                    ${email.is_unread ? 'bg-aria-500/[0.03]' : ''}`}
                >
                  <div className="flex items-start gap-4">
                    {/* Avatar */}
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 text-sm font-medium
                      ${email.is_unread ? 'bg-aria-500/20 text-aria-300' : 'bg-white/5 text-white/40'}`}>
                      {senderInitial(sender.name)}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-3">
                        <span className={`text-sm truncate ${email.is_unread ? 'font-semibold text-white' : 'text-white/70'}`}>
                          {sender.name}
                        </span>
                        <span className="text-xs text-white/30 shrink-0 flex items-center gap-1">
                          <Clock size={10} />
                          {formatDate(email.date)}
                        </span>
                      </div>
                      <p className={`text-sm mt-0.5 truncate ${email.is_unread ? 'text-white/80 font-medium' : 'text-white/50'}`}>
                        {email.subject}
                      </p>
                      <p className="text-xs text-white/30 mt-1 line-clamp-1">
                        {email.snippet}
                      </p>
                    </div>

                    {/* Unread indicator */}
                    {email.is_unread && (
                      <div className="w-2.5 h-2.5 rounded-full bg-aria-400 shrink-0 mt-1.5" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function EmailDetailView({ email, onBack }: { email: EmailItem; onBack: () => void }) {
  const sender = formatSender(email.from);
  const visibleLabels = (email.labels || []).filter(
    l => !['UNREAD', 'INBOX'].includes(l) && !l.startsWith('Label_'),
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5">
        <button
          onClick={onBack}
          className="p-1.5 hover:bg-white/5 rounded-lg transition-all text-white/50 hover:text-white/80"
        >
          <ArrowLeft size={18} />
        </button>
        <h2 className="text-lg font-semibold text-white/90 truncate flex-1">{email.subject}</h2>
      </div>

      {/* Email content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Sender info */}
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-full bg-aria-500/20 flex items-center justify-center text-lg font-medium text-aria-300">
            {senderInitial(sender.name)}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">{sender.name}</span>
              {visibleLabels.map(label => (
                <span
                  key={label}
                  className={`text-[10px] px-1.5 py-0.5 rounded ${LABEL_COLORS[label] || 'bg-white/5 text-white/40'}`}
                >
                  {label.replace('CATEGORY_', '').toLowerCase()}
                </span>
              ))}
            </div>
            <div className="flex items-center gap-2 mt-0.5 text-xs text-white/40">
              <User size={11} />
              <span>{sender.email}</span>
              <span>·</span>
              <Clock size={11} />
              <span>{email.date}</span>
            </div>
            {email.to && (
              <p className="text-xs text-white/30 mt-1">
                To: {email.to}
              </p>
            )}
          </div>
        </div>

        {/* Body */}
        <div className="prose prose-invert max-w-none">
          <div
            className="text-sm text-white/70 leading-relaxed whitespace-pre-wrap"
            // Render plain text safely — HTML is stripped by the backend
          >
            {email.body || email.snippet}
          </div>
        </div>
      </div>
    </div>
  );
}
