import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import {
  api,
  apiRequest,
  refreshAccessToken,
  clearAccessToken,
  setAccessToken,
  setAuthFailureHandler,
} from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const clearSession = useCallback(() => {
    clearAccessToken();
    setUser(null);
  }, []);

  useEffect(() => {
    setAuthFailureHandler(clearSession);
    return () => setAuthFailureHandler(null);
  }, [clearSession]);

  useEffect(() => {
    const controller = new AbortController();
    async function restoreSession() {
      try {
        await refreshAccessToken();
        if (controller.signal.aborted) return;
        const me = await api.get('/api/auth/me', { signal: controller.signal });
        if (!controller.signal.aborted) setUser(me.user);
      } catch (error) {
        if (error?.name !== 'AbortError') clearSession();
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    restoreSession();
    return () => controller.abort();
  }, [clearSession]);

  const login = useCallback(async (email, password) => {
    const body = new URLSearchParams({ username: email, password });
    const data = await apiRequest('/api/auth/login', {
      method: 'POST',
      body,
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    setAccessToken(data.access_token);
    const me = await api.get('/api/auth/me');
    setUser(me.user);
    return me.user;
  }, []);

  const register = useCallback(async (email, password) => {
    const data = await api.post('/api/auth/signup', { email, password });
    setAccessToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      const refreshed = await api.post('/api/auth/refresh', null);
      setAccessToken(refreshed.access_token);
      await api.post('/api/auth/logout', null);
    } catch (error) {
      if (error?.status && error.status !== 401) throw error;
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const value = useMemo(
    () => ({ user, loading, authenticated: Boolean(user), login, register, logout, clearSession }),
    [user, loading, login, register, logout, clearSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider');
  return context;
}
