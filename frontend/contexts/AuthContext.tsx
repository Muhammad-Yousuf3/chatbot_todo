'use client';

/**
 * Authentication Context Provider
 * Feature: 006-frontend-chat-ui
 * Updated: 007-jwt-authentication - Uses JWT Bearer tokens
 *
 * Provides real authentication with backend API and localStorage persistence.
 * Stores JWT access token for authenticated API requests.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import type { UserSession, AuthState } from '@/types';
import { apiClient, ApiClientError } from '@/lib/api';

const STORAGE_KEY = 'chatbot_user_session';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load session from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const session: UserSession = JSON.parse(stored);
        setUser(session);
        // Set JWT token in API client
        apiClient.setAccessToken(session.accessToken);
      }
    } catch {
      // Invalid stored session
      localStorage.removeItem(STORAGE_KEY);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    if (!email || !password) {
      throw new Error('Email and password are required');
    }

    try {
      const response = await apiClient.signin({ email, password });

      // Create session from response (includes JWT token)
      const session: UserSession = {
        userId: response.user_id,
        email: response.email,
        displayName: response.display_name,
        createdAt: response.created_at,
        accessToken: response.access_token,
      };

      // Persist to localStorage
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));

      // Update API client with JWT token
      apiClient.setAccessToken(session.accessToken);

      // Update state
      setUser(session);
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.code === 'INVALID_CREDENTIALS') {
          throw new Error('Invalid email or password');
        }
        throw new Error(error.message);
      }
      throw error;
    }
  }, []);

  const signup = useCallback(async (email: string, password: string, displayName: string) => {
    if (!email || !password || !displayName) {
      throw new Error('All fields are required');
    }

    try {
      const response = await apiClient.signup({
        email,
        password,
        display_name: displayName
      });

      // Create session from response (includes JWT token)
      const session: UserSession = {
        userId: response.user_id,
        email: response.email,
        displayName: response.display_name,
        createdAt: response.created_at,
        accessToken: response.access_token,
      };

      // Persist to localStorage
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));

      // Update API client with JWT token
      apiClient.setAccessToken(session.accessToken);

      // Update state
      setUser(session);
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.code === 'EMAIL_EXISTS') {
          throw new Error('Email already registered');
        }
        throw new Error(error.message);
      }
      throw error;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    apiClient.setAccessToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextType>(() => ({
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    signup,
    logout,
  }), [user, isLoading, login, signup, logout]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }
  return context;
}

export default AuthContext;
