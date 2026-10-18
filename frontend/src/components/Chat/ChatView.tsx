import React, { useEffect, useState, useRef } from 'react';
import { Send, Square, Sliders, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import { useChatStream } from '../../hooks/useChatStream';
import type { DocumentItem, Message, Thread } from '../../types/chat';
import { DocumentChip } from '../Documents/DocumentChip';
import { FileUploadZone } from '../Documents/FileUploadZone';
import { MessageList } from './MessageList';

interface Props {
  thread: Thread | null;
  onThreadUpdated: (t: Thread) => void;
  onOpenSettings: () => void;
  settings: {
    provider: string;
    model: string;
    nTurns: number;
    apiKey: string;
    temperature: number;
  };
}

export const ChatView: React.FC<Props> = ({
  thread,
  onThreadUpdated,
  onOpenSettings,
  settings,
}) => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [summary, setSummary] = useState<string>('');
  const [streamingText, setStreamingText] = useState('');
  const [activeToolCalls, setActiveToolCalls] = useState<Array<{ tool: string; input?: any; output_preview?: string }>>([]);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  const { isStreaming, startStream, stopStream } = useChatStream();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (thread) {
      setMessages(thread.messages || []);
      setDocuments(thread.documents || []);
      setSummary(thread.summary || '');
      setStreamingText('');
      setActiveToolCalls([]);
      setErrorBanner(null);
    } else {
      setMessages([]);
      setDocuments([]);
      setSummary('');
    }
  }, [thread?.id]);

  const handleDocumentUploaded = (doc: DocumentItem) => {
    setDocuments((prev) => [...prev, doc]);
    if (thread) {
      onThreadUpdated({
        ...thread,
        documents: [...documents, doc],
        document_count: (thread.document_count || 0) + 1,
      });
    }
  };

  const handleRemoveDocument = async (docId: string) => {
    if (!thread) return;
    try {
      await api.deleteDocument(thread.id, docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err: any) {
      setErrorBanner(err.message || 'Failed to remove document');
    }
  };

  const handleSendMessage = async () => {
    if (!thread || !input.trim() || isStreaming) return;

    const userText = input.trim();
    setInput('');
    setErrorBanner(null);

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setStreamingText('');
    setActiveToolCalls([]);

    let accumulatedDelta = '';
    const collectedTools: Array<{ tool: string; input?: any; output_preview?: string }> = [];

    await startStream({
      threadId: thread.id,
      message: userText,
      provider: settings.provider,
      modelName: settings.model,
      apiKey: settings.apiKey,
      temperature: settings.temperature,
      nTurns: settings.nTurns,
      onToken: (delta) => {
        accumulatedDelta += delta;
        setStreamingText((prev) => prev + delta);
      },
      onToolStart: (tool, input) => {
        collectedTools.push({ tool, input });
        setActiveToolCalls([...collectedTools]);
      },
      onToolEnd: (tool, preview) => {
        const item = collectedTools.find((t) => t.tool === tool);
        if (item) {
          item.output_preview = preview;
          setActiveToolCalls([...collectedTools]);
        }
      },
      onSummaryUpdated: (newSummary) => {
        setSummary(newSummary);
      },
      onDone: async () => {
        // Refresh full thread state from DB
        try {
          const updated = await api.getThread(thread.id);
          onThreadUpdated(updated);
          setMessages(updated.messages || []);
          setSummary(updated.summary || '');
        } catch {}
        setStreamingText('');
        setActiveToolCalls([]);
      },
      onError: (err) => {
        setErrorBanner(err.message || 'Error occurred during streaming');
        setStreamingText('');
      },
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!thread) {
    return (
      <main className="chat-main">
        <div className="empty-state">
          <p>Select an existing conversation or start a new one to begin.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="chat-main" id="chat-main-container">
      {/* Chat Header */}
      <header className="chat-header">
        <div className="chat-header-info">
          <h1 className="chat-title" id="chat-active-title">{thread.title || 'Conversation'}</h1>
          <div className="model-pill" id="badge-active-model">
            <span>{settings.provider.toUpperCase()}</span>
            <span>•</span>
            <span>{settings.model}</span>
          </div>
        </div>

        <div className="chat-header-actions">
          <button
            className="icon-btn"
            onClick={onOpenSettings}
            title="Adjust model & N-turn settings"
            id="btn-chat-settings"
          >
            <Sliders size={18} />
          </button>
        </div>
      </header>

      {/* Error notification banner if any */}
      {errorBanner && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '10px 24px',
          background: 'rgba(244, 63, 94, 0.15)',
          borderBottom: '1px solid rgba(244, 63, 94, 0.3)',
          color: '#f87171',
          fontSize: '0.88rem'
        }}>
          <AlertCircle size={16} />
          <span>{errorBanner}</span>
        </div>
      )}

      {/* Chat Messages */}
      <MessageList
        messages={messages}
        summary={summary}
        isStreaming={isStreaming}
        streamingMessage={streamingText}
        activeToolCalls={activeToolCalls}
      />

      {/* Input Area */}
      <footer className="chat-input-wrapper">
        {/* Attached documents list */}
        {documents.length > 0 && (
          <div className="attachments-bar" id="attached-documents-bar">
            {documents.map((doc) => (
              <DocumentChip
                key={doc.id}
                doc={doc}
                onRemove={handleRemoveDocument}
              />
            ))}
          </div>
        )}

        <div className="input-box">
          <FileUploadZone
            threadId={thread.id}
            onDocumentUploaded={handleDocumentUploaded}
            onError={(err) => setErrorBanner(err)}
          />

          <textarea
            ref={textareaRef}
            rows={1}
            className="chat-textarea"
            placeholder={`Message AuraChat (${settings.model})... Enter to send, Shift+Enter for new line`}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            id="chat-message-input"
          />

          <div className="input-actions">
            {isStreaming ? (
              <button
                type="button"
                className="btn-send"
                onClick={stopStream}
                title="Stop generation"
                style={{ background: '#f43f5e' }}
                id="btn-stop-streaming"
              >
                <Square size={16} />
              </button>
            ) : (
              <button
                type="button"
                className="btn-send"
                onClick={handleSendMessage}
                disabled={!input.trim()}
                title="Send message"
                id="btn-send-message"
              >
                <Send size={16} />
              </button>
            )}
          </div>
        </div>
      </footer>
    </main>
  );
};
