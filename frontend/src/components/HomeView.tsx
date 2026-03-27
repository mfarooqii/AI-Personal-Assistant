import { useState } from 'react';
import { VoiceOrb } from './VoiceOrb';
import { Send } from 'lucide-react';

interface Props {
  onStartChat: (message: string) => void;
  initialMessage: string;
}

export function HomeView({ onStartChat }: Props) {
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    if (!input.trim()) return;
    onStartChat(input.trim());
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6">
      {/* Voice Orb — the centerpiece */}
      <VoiceOrb onTranscript={(text) => setInput(text)} />

      <h1 className="mt-8 text-3xl font-light text-white/90">
        Hey, I'm <span className="font-semibold text-aria-400">Aria</span>
      </h1>
      <p className="mt-2 text-white/40 text-center max-w-md">
        Your personal AI assistant. Ask me anything, or tap the orb to talk.
      </p>

      {/* Input field */}
      <div className="mt-10 w-full max-w-xl relative">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          placeholder="What's on your mind?"
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

      {/* Quick suggestions */}
      <div className="mt-6 flex flex-wrap gap-2 justify-center max-w-xl">
        {[
          "What's the weather like?",
          "Help me plan a trip",
          "Set a reminder for 3pm",
          "Find me a recipe for dinner",
          "How's my budget this month?",
          "Summarize today's tech news",
        ].map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => { setInput(suggestion); }}
            className="px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 text-sm text-white/50
                       hover:text-white/80 transition-all border border-white/5"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
