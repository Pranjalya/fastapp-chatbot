import React, { createContext, useContext, useEffect, useState } from 'react';
import { api, authStorage } from '../services/api';

interface AuthContextType {
  username: string | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (u: string, p: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  username: null,
  token: null,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(authStorage.getToken());
  const [username, setUsername] = useState<string | null>(authStorage.getUsername());

  useEffect(() => {
    const handleUnauthorized = () => {
      setToken(null);
      setUsername(null);
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  const login = async (u: string, p: string) => {
    const res = await api.login(u, p);
    setToken(res.access_token);
    setUsername(res.username);
  };

  const logout = () => {
    authStorage.clear();
    setToken(null);
    setUsername(null);
  };

  return (
    <AuthContext.Provider value={{ token, username, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
