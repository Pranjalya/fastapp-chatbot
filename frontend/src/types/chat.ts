export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_calls?: Array<{
    tool: string;
    input?: any;
    output_preview?: string;
  }>;
  tool_call_id?: string;
  turn_index?: number;
  is_summarized?: boolean;
  created_at?: string;
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  size_bytes: number;
  token_count_estimate: number;
  strategy: 'DIRECT_CONTEXT' | 'TOOL_RETRIEVAL';
  summary_or_toc?: string;
  created_at?: string;
}

export interface Thread {
  id: string;
  title: string;
  user_id: string;
  summary: string;
  n_turns: number;
  provider: string;
  model_name: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  document_count?: number;
  messages?: Message[];
  documents?: DocumentItem[];
}

export interface ModelProvider {
  id: string;
  name: string;
  default_model: string;
  models: string[];
  has_server_key: boolean;
  base_url?: string;
}

export interface AuthState {
  token: string | null;
  username: string | null;
  isAuthenticated: boolean;
}
