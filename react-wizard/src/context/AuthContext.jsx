import React, { createContext, useContext, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { TOKEN_KEY, USER_KEY } from '../config/constants';

// ─── Context ───────────────────────────────────────────────────────────────
const AuthContext = createContext(null);

// ─── Provider ──────────────────────────────────────────────────────────────
// Wraps the app and provides auth state (user, token) + helpers (login, logout).
// Currently App.jsx manages auth state with useState; this context can be used
// to gradually migrate away from prop-drilling user/onLogin/onLogout props.
//
// Usage:
//   const { user, login, logout } = useAuth();
export function AuthProvider({ children }) {
  const navigate = useNavigate();
  const [user, setUser] = useState(localStorage.getItem(USER_KEY));

  const login = useCallback((username, token) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, username);
    setUser(username);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    navigate('/auth');
  }, [navigate]);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Hook ──────────────────────────────────────────────────────────────────
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}

export default AuthContext;
