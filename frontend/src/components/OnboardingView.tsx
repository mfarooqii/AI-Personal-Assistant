/**
 * OnboardingView — conversational setup wizard.
 *
 * First-time users see this instead of HomeView. Aria asks simple questions
 * step by step, building the user's profile through conversation.
 * No settings pages — everything through chat.
 */

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, Check } from 'lucide-react';
import {
  getOnboardingStatus,
  submitOnboardingStep,
  type OnboardingStep,
  type OnboardingOption,
} from '../api';

interface Props {
  onComplete: () => void;
}

interface BubbleMessage {
  role: 'assistant' | 'user';
  content: string;
}

export function OnboardingView({ onComplete }: Props) {
  const [messages, setMessages] = useState<BubbleMessage[]>([]);
  const [currentStep, setCurrentStep] = useState<OnboardingStep | null>(null);
  const [stepMessage, setStepMessage] = useState('');
  const [input, setInput] = useState('');
  const [selectedOptions, setSelectedOptions] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  // Load initial onboarding state
  useEffect(() => {
    (async () => {
      try {
        const status = await getOnboardingStatus();
        if (status.completed) {
          onComplete();
          return;
        }
        // Get the first step
        const resp = await submitOnboardingStep();
        simulateTyping(resp.message);
        setCurrentStep(resp.step);
      } catch {
        // Backend not ready — show fallback
        onComplete();
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const simulateTyping = (text: string) => {
    setTyping(true);
    // Brief delay to simulate Aria "thinking"
    setTimeout(() => {
      setMessages(prev => [...prev, { role: 'assistant', content: text }]);
      setStepMessage(text);
      setTyping(false);
    }, 600);
  };

  const handleTextSubmit = async () => {
    const text = input.trim();
    if (!text) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setLoading(true);

    try {
      const resp = await submitOnboardingStep(text);
      simulateTyping(resp.message);
      setCurrentStep(resp.step);

      if (resp.completed) {
        setTimeout(onComplete, 2500);
      }
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Something went wrong — let me try that again."
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleMultiSelectSubmit = async () => {
    if (selectedOptions.size === 0) return;

    const selections = Array.from(selectedOptions);
    // Show user's choice in chat
    const optionLabels = currentStep?.options
      ?.filter(o => selectedOptions.has(o.id))
      .map(o => o.label) || selections;
    setMessages(prev => [...prev, { role: 'user', content: optionLabels.join(', ') }]);
    setSelectedOptions(new Set());
    setLoading(true);

    try {
      const resp = await submitOnboardingStep(undefined, selections);
      simulateTyping(resp.message);
      setCurrentStep(resp.step);

      if (resp.completed) {
        setTimeout(onComplete, 2500);
      }
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Something went wrong — let me try that again."
      }]);
    } finally {
      setLoading(false);
    }
  };

  const toggleOption = (id: string) => {
    setSelectedOptions(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (loading && messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-aria-600/20 flex items-center justify-center animate-pulse">
            <Bot size={32} className="text-aria-400" />
          </div>
          <p className="text-white/40 text-sm">Starting up...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Logo header */}
      <div className="flex items-center justify-center py-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-aria-500 to-aria-700 flex items-center justify-center shadow-lg shadow-aria-500/20">
            <Bot size={22} className="text-white" />
          </div>
          <span className="text-xl font-semibold text-white/90">Aria</span>
        </div>
      </div>

      {/* Conversation area */}
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        <div className="max-w-2xl mx-auto space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''} animate-fade-up`}>
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
                {msg.role === 'assistant' ? (
                  <div className="markdown-content prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm">{msg.content}</p>
                )}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {typing && (
            <div className="flex gap-3 animate-fade-up">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-aria-600/20 flex items-center justify-center">
                <Bot size={16} className="text-aria-400" />
              </div>
              <div className="bg-[var(--bg-tertiary)] border border-white/5 rounded-2xl px-5 py-3">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-aria-400/50 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-aria-400/50 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-aria-400/50 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={scrollRef} />
        </div>
      </div>

      {/* Input area — changes based on step type */}
      <div className="border-t border-white/5 p-4">
        <div className="max-w-2xl mx-auto">
          {/* Multi-select options */}
          {currentStep?.type === 'multi_select' && currentStep.options && (
            <div className="mb-4">
              <div className="grid grid-cols-2 gap-2">
                {currentStep.options.map((option: OnboardingOption) => (
                  <button
                    key={option.id}
                    onClick={() => toggleOption(option.id)}
                    className={`
                      flex items-start gap-3 p-3 rounded-xl border text-left transition-all
                      ${selectedOptions.has(option.id)
                        ? 'bg-aria-600/20 border-aria-500/50 ring-1 ring-aria-500/30'
                        : 'bg-white/3 border-white/8 hover:bg-white/5 hover:border-white/15'
                      }
                    `}
                  >
                    <div className={`
                      w-5 h-5 rounded-md border flex-shrink-0 mt-0.5 flex items-center justify-center transition-all
                      ${selectedOptions.has(option.id)
                        ? 'bg-aria-600 border-aria-500'
                        : 'border-white/20'
                      }
                    `}>
                      {selectedOptions.has(option.id) && <Check size={12} className="text-white" />}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white/85">{option.label}</p>
                      <p className="text-xs text-white/40 mt-0.5">{option.description}</p>
                    </div>
                  </button>
                ))}
              </div>
              <button
                onClick={handleMultiSelectSubmit}
                disabled={selectedOptions.size === 0 || loading}
                className="
                  mt-3 w-full py-3 rounded-xl bg-aria-600 hover:bg-aria-500
                  disabled:opacity-30 disabled:hover:bg-aria-600
                  text-white font-medium text-sm transition-all
                "
              >
                Continue ({selectedOptions.size} selected)
              </button>
            </div>
          )}

          {/* Text input */}
          {(currentStep?.type === 'text' || currentStep?.type === 'complete') && (
            <div className="relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !loading && handleTextSubmit()}
                placeholder={currentStep?.placeholder || 'Type here...'}
                disabled={loading || typing}
                className="
                  w-full bg-[var(--bg-tertiary)] border border-white/10 rounded-2xl px-5 py-3.5 pr-14
                  text-white placeholder:text-white/30 focus:outline-none focus:border-aria-500/50
                  focus:ring-2 focus:ring-aria-500/20 transition-all disabled:opacity-50
                "
              />
              <button
                onClick={handleTextSubmit}
                disabled={!input.trim() || loading || typing}
                className="
                  absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-xl
                  bg-aria-600 hover:bg-aria-500 disabled:opacity-30
                  disabled:hover:bg-aria-600 transition-all
                "
              >
                <Send size={18} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
