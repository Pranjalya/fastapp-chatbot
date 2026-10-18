import React, { useEffect, useRef } from 'react';
import { Sparkles, Bookmark } from 'lucide-react';
import type { Message } from '../../types/chat';
import { MessageItem } from './MessageItem';

interface Props {
  messages: Message[];
  summary?: string;
  isStreaming: boolean;
  streamingMessage?: string;
  activeToolCalls?: Array<{ tool: string; input?: any; output_preview?: string }>;
}

export const MessageList: React.FC<Props> = ({
  messages,
  summary,
  isStreaming,
  streamingMessage,
  activeToolCalls,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage, activeToolCalls]);

  if (messages.length === 0 && !streamingMessage) {
    return (
      <div className="empty-state">
        <div className="empty-icon">
          <Sparkles size={32} />
        </div>
        <h2 className="empty-title">How can I assist you today?</h2>
        <p className="empty-subtitle">
          Attach PDFs, DOCX, CSVs or code files, ask complex questions, or test long multi-turn conversations with automatic rolling summarization.
        </p>
      </div>
    );
  }

  return (
    <div className="messages-container" id="chat-messages-scroll-area">
      {summary && (
        <div className="summary-banner" id="rolling-summary-banner">
          <div className="summary-banner-title">
            <Bookmark size={15} />
            <span>Active Rolling Conversation Summary (Older Turns)</span>
          </div>
          <div>{summary}</div>
        </div>
      )}

      {messages.map((msg) => (
        <MessageItem key={msg.id} message={msg} />
      ))}

      {isStreaming && (
        <MessageItem
          message={{
            id: 'streaming-assistant-msg',
            role: 'assistant',
            content: streamingMessage || '',
            tool_calls: activeToolCalls,
          }}
          isStreaming={true}
        />
      )}

      <div ref={bottomRef} style={{ height: '1px' }} />
    </div>
  );
};
