import React from 'react';
import { Plus, MessageSquare, Trash2, Settings as SettingsIcon, LogOut, Sparkles } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import type { Thread } from '../../types/chat';

interface Props {
  threads: Thread[];
  activeThreadId: string | null;
  onSelectThread: (id: string) => void;
  onNewThread: () => void;
  onDeleteThread: (id: string) => void;
  onOpenSettings: () => void;
}

export const SessionList: React.FC<Props> = ({
  threads,
  activeThreadId,
  onSelectThread,
  onNewThread,
  onDeleteThread,
  onOpenSettings,
}) => {
  const { username, logout } = useAuth();

  return (
    <aside className="sidebar" id="sidebar-container">
      <div className="sidebar-header">
        <div className="brand-badge">
          <div className="brand-icon">
            <Sparkles size={18} />
          </div>
          <span className="brand-title">AuraChat</span>
        </div>
        <button
          className="icon-btn"
          onClick={onOpenSettings}
          title="Model & System Settings"
          id="btn-sidebar-settings"
        >
          <SettingsIcon size={18} />
        </button>
      </div>

      <button className="btn-new-chat" onClick={onNewThread} id="btn-new-chat">
        <Plus size={18} />
        <span>New Conversation</span>
      </button>

      <div className="thread-list" id="thread-list-container">
        {threads.map((thread) => {
          const isActive = thread.id === activeThreadId;
          return (
            <div
              key={thread.id}
              className={`thread-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelectThread(thread.id)}
              id={`thread-item-${thread.id}`}
            >
              <div className="thread-item-content">
                <MessageSquare size={16} />
                <span className="thread-item-title">{thread.title || 'Conversation'}</span>
              </div>
              <button
                className="thread-delete-btn"
                title="Delete thread"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteThread(thread.id);
                }}
              >
                <Trash2 size={14} />
              </button>
            </div>
          );
        })}
      </div>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">
            {username ? username.charAt(0).toUpperCase() : 'U'}
          </div>
          <span className="user-name">{username}</span>
        </div>
        <button
          className="icon-btn"
          onClick={logout}
          title="Sign Out"
          id="btn-logout"
        >
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
};
