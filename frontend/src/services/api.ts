import type { DocumentItem, ModelProvider, Thread } from '../types/chat';

const TOKEN_KEY = 'aurachat_jwt_token';
const USER_KEY = 'aurachat_user';

export const authStorage = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  getUsername: () => localStorage.getItem(USER_KEY),
  setUsername: (user: string) => localStorage.setItem(USER_KEY, user),
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
};

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = authStorage.getToken();
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  const response = await fetch(url, { ...options, headers });
  
  if (response.status === 401) {
    authStorage.clear();
    window.dispatchEvent(new Event('auth:unauthorized'));
    throw new Error('Unauthorized');
  }
  
  return response;
}

export const api = {
  async login(username: string, password: string) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Authentication failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    authStorage.setToken(data.access_token);
    authStorage.setUsername(data.username);
    return data;
  },

  async getMe() {
    const res = await fetchWithAuth('/api/auth/me');
    return res.json();
  },

  async getProviders(): Promise<{ default_provider: string; default_model: string; default_n_turns: number; providers: ModelProvider[] }> {
    const res = await fetchWithAuth('/api/models');
    return res.json();
  },

  async getThreads(): Promise<Thread[]> {
    const res = await fetchWithAuth('/api/threads');
    return res.json();
  },

  async createThread(data: { title?: string; provider?: string; model_name?: string; n_turns?: number }): Promise<Thread> {
    const res = await fetchWithAuth('/api/threads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async getThread(threadId: string): Promise<Thread> {
    const res = await fetchWithAuth(`/api/threads/${threadId}`);
    return res.json();
  },

  async updateThread(threadId: string, data: Partial<Thread>): Promise<Thread> {
    const res = await fetchWithAuth(`/api/threads/${threadId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async deleteThread(threadId: string): Promise<void> {
    await fetchWithAuth(`/api/threads/${threadId}`, { method: 'DELETE' });
  },

  async uploadDocument(threadId: string, file: File): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await fetchWithAuth(`/api/threads/${threadId}/documents`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'File upload failed');
    }
    return res.json();
  },

  async deleteDocument(threadId: string, documentId: string): Promise<void> {
    await fetchWithAuth(`/api/threads/${threadId}/documents/${documentId}`, {
      method: 'DELETE',
    });
  }
};
