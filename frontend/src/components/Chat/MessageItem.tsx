import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, Copy, Check } from 'lucide-react';
import type { Message } from '../../types/chat';
import { ToolCallCard } from './ToolCallCard';

interface Props {
  message: Message;
  isStreaming?: boolean;
}

export const MessageItem: React.FC<Props> = ({ message, isStreaming }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`} id={`msg-${message.id}`}>
      <div className={`message-avatar ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      <div className="message-body">
        {/* Render tool calls executed during this turn */}
        {message.tool_calls && message.tool_calls.map((t, idx) => (
          <ToolCallCard
            key={idx}
            tool={t.tool}
            input={t.input}
            outputPreview={t.output_preview}
          />
        ))}

        <div className="message-bubble" style={{ position: 'relative' }}>
          {isUser ? (
            <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
          ) : (
            <div>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
              {isStreaming && <span className="typing-cursor" />}
            </div>
          )}

          {!isStreaming && message.content && (
            <button
              onClick={handleCopy}
              className="icon-btn"
              title="Copy message"
              style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
                opacity: 0.35,
                padding: '4px',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.35')}
            >
              {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
