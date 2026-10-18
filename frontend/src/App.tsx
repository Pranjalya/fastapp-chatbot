import React, { useEffect, useState } from 'react';
import { api } from './services/api';
import { useAuth } from './context/AuthContext';
import type { ModelProvider, Thread } from './types/chat';
import { LoginModal } from './components/Auth/LoginModal';
import { SessionList } from './components/Sidebar/SessionList';
import { ChatView } from './components/Chat/ChatView';
import { SettingsModal } from './components/Modals/SettingsModal';

export const AppContent: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [activeThread, setActiveThread] = useState<Thread | null>(null);
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const [settings, setSettings] = useState({
    provider: 'gemini',
    model: 'gemini-3.5-flash',
    nTurns: 5,
    apiKey: '',
    temperature: 0.3,
  });

  // Load providers and threads on authentication
  useEffect(() => {
    if (!isAuthenticated) return;

    const loadInitialData = async () => {
      try {
        const provData = await api.getProviders();
        setProviders(provData.providers || []);
        if (provData.default_provider) {
          setSettings((prev) => ({
            ...prev,
            provider: provData.default_provider,
            model: provData.default_model,
            nTurns: provData.default_n_turns,
          }));
        }

        const threadList = await api.getThreads();
        setThreads(threadList);
        if (threadList.length > 0) {
          setActiveThreadId(threadList[0].id);
        } else {
          // Auto-create initial thread
          const initialThread = await api.createThread({
            title: 'New Conversation',
            provider: provData.default_provider,
            model_name: provData.default_model,
            n_turns: provData.default_n_turns,
          });
          setThreads([initialThread]);
          setActiveThreadId(initialThread.id);
        }
      } catch (err) {
        console.error('Failed to load initial data:', err);
      }
    };

    loadInitialData();
  }, [isAuthenticated]);

  // Load active thread details
  useEffect(() => {
    if (!activeThreadId) {
      setActiveThread(null);
      return;
    }
    const fetchActiveThread = async () => {
      try {
        const fullThread = await api.getThread(activeThreadId);
        setActiveThread(fullThread);
      } catch (err) {
        console.error('Failed to fetch thread detail:', err);
      }
    };
    fetchActiveThread();
  }, [activeThreadId]);

  const handleNewThread = async () => {
    try {
      const newThread = await api.createThread({
        title: 'New Conversation',
        provider: settings.provider,
        model_name: settings.model,
        n_turns: settings.nTurns,
      });
      setThreads((prev) => [newThread, ...prev]);
      setActiveThreadId(newThread.id);
    } catch (err) {
      console.error('Failed to create new thread:', err);
    }
  };

  const handleDeleteThread = async (id: string) => {
    try {
      await api.deleteThread(id);
      const remaining = threads.filter((t) => t.id !== id);
      setThreads(remaining);
      if (activeThreadId === id) {
        setActiveThreadId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (err) {
      console.error('Failed to delete thread:', err);
    }
  };

  const handleThreadUpdated = (updated: Thread) => {
    setActiveThread(updated);
    setThreads((prev) =>
      prev.map((t) => (t.id === updated.id ? { ...t, title: updated.title, updated_at: updated.updated_at } : t))
    );
  };

  if (!isAuthenticated) {
    return <LoginModal />;
  }

  return (
    <div className="app-container" id="app-root-container">
      <SessionList
        threads={threads}
        activeThreadId={activeThreadId}
        onSelectThread={setActiveThreadId}
        onNewThread={handleNewThread}
        onDeleteThread={handleDeleteThread}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <ChatView
        thread={activeThread}
        onThreadUpdated={handleThreadUpdated}
        onOpenSettings={() => setIsSettingsOpen(true)}
        settings={settings}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        providers={providers}
        currentProvider={settings.provider}
        currentModel={settings.model}
        nTurns={settings.nTurns}
        apiKey={settings.apiKey}
        temperature={settings.temperature}
        onSave={(newSettings) => setSettings((prev) => ({ ...prev, ...newSettings }))}
      />
    </div>
  );
};

export default function App() {
  return <AppContent />;
}
