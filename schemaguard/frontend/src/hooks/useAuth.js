import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

/**
 * Custom hook to access authentication context.
 * @returns {{ user: {id: string, email: string}|null, token: string|null, login: Function, signup: Function, logout: Function, isAuthenticated: boolean, isLoading: boolean }}
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
