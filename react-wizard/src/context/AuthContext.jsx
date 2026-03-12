import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/api';
import { toast } from '../components/Toast';

// ─── Context ───────────────────────────────────────────────────────────────
const AuthContext = createContext(null);

// ─── Provider ──────────────────────────────────────────────────────────────
/**
 * AuthProvider manages authentication state using HTTP-only cookies.
 * - user: Current authenticated user object (null if not logged in)
 * - loading: True during initial auth check and auth operations
 * - error: Authentication error message
 * - login: Authenticate user with username/password
 * - signup: Register new user account
 * - logout: Clear authentication and redirect to login
 * - checkAuth: Verify authentication status by calling /auth/me
 */
export function AuthProvider({ children }) {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check authentication status on mount
  const checkAuth = useCallback(async () => {
    try {
      setLoading(true);
      const response = await authService.getMe();
      setUser(response.data);
      setError(null);
    } catch (err) {
      // 401 is expected when not logged in
      if (err.response?.status !== 401) {
        console.error('Auth check failed:', err);
      }
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Login with username and password
  const login = useCallback(async (username, password) => {
    try {
      setLoading(true);
      setError(null);
      
      await authService.login(username, password);
      
      // Fetch user profile after successful login
      const response = await authService.getMe();
      setUser(response.data);
      
      toast('Login successful!', 'success');
      navigate('/dashboard');
      
      return { success: true };
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Login failed. Please try again.';
      setError(errorMsg);
      toast(errorMsg, 'error');
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  // Signup new user
  const signup = useCallback(async (username, password, email = '', fullName = '', companyId = '') => {
    try {
      setLoading(true);
      setError(null);
      
      await authService.signup(username, password, email, fullName, companyId);
      
      // Auto-login after successful signup
      return await login(username, password);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Signup failed. Please try again.';
      setError(errorMsg);
      toast(errorMsg, 'error');
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  }, [login]);

  // Logout user
  const logout = useCallback(async () => {
    try {
      await authService.logout();
      setUser(null);
      setError(null);
      toast('Logged out successfully', 'info');
      navigate('/auth');
    } catch (err) {
      console.error('Logout error:', err);
      // Clear client state even if server request fails
      setUser(null);
      navigate('/auth');
    }
  }, [navigate]);

  // Check auth status on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Listen for auth:logout events (from 401 interceptor)
  useEffect(() => {
    const handleAuthLogout = () => {
      setUser(null);
      navigate('/auth');
    };
    
    window.addEventListener('auth:logout', handleAuthLogout);
    return () => window.removeEventListener('auth:logout', handleAuthLogout);
  }, [navigate]);

  return (
    <AuthContext.Provider value={{ user, loading, error, login, signup, logout, checkAuth }}>
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
