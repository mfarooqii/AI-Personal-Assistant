import { useState } from 'react'
import { ChatView } from './components/ChatView'
import { Sidebar } from './components/Sidebar'
import { HomeView } from './components/HomeView'
import { Menu } from 'lucide-react'

export type View = 'home' | 'chat';

export default function App() {
  const [view, setView] = useState<View>('home');
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const startNewChat = () => {
    setConversationId(undefined);
    setView('chat');
  };

  const openConversation = (id: string) => {
    setConversationId(id);
    setView('chat');
    setSidebarOpen(false);
  };

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
          onGoHome={() => { setView('home'); setSidebarOpen(false); }}
          activeConversationId={conversationId}
        />
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Main content */}
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
              setView('chat');
            }}
            initialMessage=""
          />
        ) : (
          <ChatView
            conversationId={conversationId}
            onConversationCreated={setConversationId}
          />
        )}
      </div>
    </div>
  );
}
