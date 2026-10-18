import { useRef, useState } from 'react';
import { authStorage } from '../services/api';

interface StreamOptions {
  threadId: string;
  message: string;
  provider?: string;
  modelName?: string;
  apiKey?: string;
  temperature?: number;
  nTurns?: number;
  onToken?: (delta: string) => void;
  onToolStart?: (tool: string, input: any) => void;
  onToolEnd?: (tool: string, preview: string) => void;
  onSummaryUpdated?: (summary: string) => void;
  onDone?: () => void;
  onError?: (err: Error) => void;
}

export function useChatStream() {
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = async (options: StreamOptions) => {
    setIsStreaming(true);
    abortControllerRef.current = new AbortController();
    const token = authStorage.getToken();

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify({
          thread_id: options.threadId,
          message: options.message,
          provider: options.provider,
          model_name: options.modelName,
          api_key: options.apiKey,
          temperature: options.temperature,
          n_turns: options.nTurns,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Streaming failed' }));
        throw new Error(errorData.detail || `Server responded with ${response.status}`);
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported on this browser response');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE double newline chunk boundaries
        const events = buffer.split('\n\n');
        buffer = events.pop() || ''; // Keep partial last event in buffer

        for (const evt of events) {
          if (!evt.trim()) continue;

          let eventType = 'message';
          let eventData = '';

          const lines = evt.split('\n');
          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              eventData = line.slice(6).trim();
            }
          }

          if (eventType === 'token') {
            try {
              const parsed = JSON.parse(eventData);
              if (parsed.delta) {
                options.onToken?.(parsed.delta);
              }
            } catch {}
          } else if (eventType === 'tool_start') {
            try {
              const parsed = JSON.parse(eventData);
              options.onToolStart?.(parsed.tool, parsed.input);
            } catch {}
          } else if (eventType === 'tool_end') {
            try {
              const parsed = JSON.parse(eventData);
              options.onToolEnd?.(parsed.tool, parsed.output_preview);
            } catch {}
          } else if (eventType === 'summary_updated') {
            try {
              const parsed = JSON.parse(eventData);
              options.onSummaryUpdated?.(parsed.summary);
            } catch {}
          } else if (eventType === 'error') {
            try {
              const parsed = JSON.parse(eventData);
              options.onError?.(new Error(parsed.error || 'Server stream error'));
            } catch {
              options.onError?.(new Error(eventData));
            }
          } else if (eventType === 'done') {
            options.onDone?.();
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        options.onError?.(err);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const stopStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsStreaming(false);
  };

  return { isStreaming, startStream, stopStream };
}
