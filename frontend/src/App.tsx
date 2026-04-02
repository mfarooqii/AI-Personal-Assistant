import { useState, useEffect } from 'react'
import { ChatView } from './components/ChatView'
import { Sidebar } from './components/Sidebar'
import { HomeView } from './components/HomeView'
import { OnboardingView } from './components/OnboardingView'
import { DashboardRenderer, isAdaptiveLayout } from './components/DashboardRenderer'
import { BrowserPanel } from './components/BrowserPanel'
import { Menu } from 'lucide-react'
import { getOnboardingStatus, closeBrowser } from './api'
import type { LayoutDirective } from './api'

export type View = 'loading' | 'onboarding' | 'home' | 'chat';

export default function App() {
  const [view, setView] = useState<View>('loading');
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeLayout, setActiveLayout] = useState<LayoutDirective | null>(null);
  const [browserSession, setBrowserSession] = useState<{ task: string; plan: any } | null>(null);
  const [userName, setUserName] = useState<string>('');
  const [initialMessage, setInitialMessage] = useState<string>('');

  // Check onboarding status on mount
  useEffect(() => {
    (async () => {
      try {
        const status = await getOnboardingStatus();
        if (status.completed) {
          setView('home');
        } else {
          setView('onboarding');
        }
      } catch {
        // Backend not ready — show home anyway
        setView('home');
      }
    })();
  }, []);

  const startNewChat = () => {
    setConversationId(undefined);
    setActiveLayout(null);
    setView('chat');
  };

  const openConversation = (id: string) => {
    setConversationId(id);
    setActiveLayout(null);
    setView('chat');
    setSidebarOpen(false);
  };

  const handleLayoutChange = (layout: LayoutDirective) => {
    if (layout.layout === 'browser' && layout.data) {
      setBrowserSession({ task: layout.data.task, plan: layout.data.plan });
      return;
    }
    if (isAdaptiveLayout(layout)) {
      setActiveLayout(layout);
    }
  };

  const handleBrowserResult = (data: any) => {
    // When the browser agent extracts data, show it in the dashboard
    if (data.emails) {
      setActiveLayout({ layout: 'email_inbox', title: 'Email', data });
    } else if (data.products) {
      setActiveLayout({ layout: 'search_results', title: 'Results', data });
    } else if (data.summary || data.content) {
      setActiveLayout({ layout: 'document', title: 'Results', data: { raw_content: data.summary || data.content } });
    }
    setBrowserSession(null);
  };

  const handleBrowserClose = async () => {
    setBrowserSession(null);
    try { await closeBrowser(); } catch { /* ignore */ }
  };

  const handleOnboardingComplete = () => {
    setView('home');
  };

  // Loading state
  if (view === 'loading') {
    return (
      <div className="h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <div className="w-12 h-12 rounded-full bg-aria-600/20 animate-pulse" />
      </div>
    );
  }

  // Onboarding — full screen, no sidebar
  if (view === 'onboarding') {
    return (
      <div className="h-screen flex flex-col bg-[var(--bg-primary)]">
        <OnboardingView onComplete={handleOnboardingComplete} />
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-[var(--bg-primary)]">
      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-72 transform transition-transform duration-300 md:relative md:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <Sidebar
          onNewChat={startNewChat}
          onOpenConversation={openConversation}
          onGoHome={() => { setView('home'); setActiveLayout(null); setSidebarOpen(false); }}
          activeConversationId={conversationId}
        />
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Main content area — adapts between chat and split panel */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile header */}
        <div className="md:hidden flex items-center p-3 border-b border-white/5">
          <button onClick={() => setSidebarOpen(true)} className="p-2 hover:bg-white/5 rounded-lg">
            <Menu size={20} />
          </button>
          <span className="ml-3 font-semibold text-aria-400">Aria</span>
        </div>

        {view === 'home' ? (
          <HomeView
            onStartChat={(msg) => {
              setConversationId(undefined);
              setActiveLayout(null);
              setInitialMessage(msg);
              setView('chat');
            }}
            initialMessage=""
          />
        ) : (
          /* Split panel: Chat + Adaptive Dashboard / Browser */
          <div className="flex-1 flex min-h-0">
            {/* Chat panel — shrinks when dashboard or browser is open */}
            <div className={`
              flex flex-col transition-all duration-300 ease-in-out
              ${(activeLayout || browserSession) ? 'w-[45%] min-w-[360px] border-r border-white/5' : 'flex-1'}
            `}>
              <ChatView
                conversationId={conversationId}
                onConversationCreated={setConversationId}
                onLayoutChange={handleLayoutChange}
                initialMessage={initialMessage}
              />
            </div>

            {/* Browser panel (takes precedence over dashboard) */}
            {browserSession && (
              <div className="flex-1 min-w-[400px] animate-slide-in">
                <BrowserPanel
                  task={browserSession.task}
                  plan={browserSession.plan}
                  onResult={handleBrowserResult}
                  onClose={handleBrowserClose}
                />
              </div>
            )}

            {/* Adaptive dashboard panel */}
            {activeLayout && !browserSession && (
              <div className="flex-1 min-w-[400px] animate-slide-in">
                <DashboardRenderer
                  layout={activeLayout}
                  onClose={() => setActiveLayout(null)}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
