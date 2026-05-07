import { createContext, useState, useEffect, useCallback } from 'react';
import { authAPI, profileAPI } from '../api/client';

export const AuthContext = createContext(null);

function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

function isTokenExpired(token) {
  const payload = parseJwt(token);
  if (!payload || !payload.exp) return true;
  return Date.now() >= payload.exp * 1000;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('schemaguard_token');
    const storedUser = localStorage.getItem('schemaguard_user');

    if (storedToken && !isTokenExpired(storedToken)) {
      setToken(storedToken);
      try {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        profileAPI.get()
          .then((profile) => {
            const freshUser = { id: profile.id, email: profile.email, username: profile.username, is_admin: !!profile.is_admin };
            localStorage.setItem('schemaguard_user', JSON.stringify(freshUser));
            setUser(freshUser);
          })
          .catch(() => setUser(parsedUser));
      } catch {
        setUser(null);
      }
    } else {
      localStorage.removeItem('schemaguard_token');
      localStorage.removeItem('schemaguard_user');
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await authAPI.login({ email, password });
    const userData = { id: data.user_id, email: data.email, username: data.username, is_admin: !!data.is_admin };
    localStorage.setItem('schemaguard_token', data.access_token);
    localStorage.setItem('schemaguard_user', JSON.stringify(userData));
    setToken(data.access_token);
    setUser(userData);
    return data;
  }, []);

  const signup = useCallback(async (email, password) => {
    const data = await authAPI.register({ email, password });
    const userData = { id: data.user_id, email: data.email, username: data.username, is_admin: !!data.is_admin };
    localStorage.setItem('schemaguard_token', data.access_token);
    localStorage.setItem('schemaguard_user', JSON.stringify(userData));
    setToken(data.access_token);
    setUser(userData);
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('schemaguard_token');
    localStorage.removeItem('schemaguard_user');
    setToken(null);
    setUser(null);
    window.location.href = '/';
  }, []);

  const value = {
    user,
    token,
    login,
    signup,
    logout,
    isAuthenticated: !!token,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
