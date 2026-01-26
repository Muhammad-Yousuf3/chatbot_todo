'use client';

/**
 * Theme Context Provider
 * Feature: 006-frontend-chat-ui
 * Updated: 011-midnight-glass-ui - Force dark mode
 *
 * Provides dark mode support - always dark for Midnight AI Glass theme.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | null>(null);

const STORAGE_KEY = 'chatbot_theme';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Force dark mode for Midnight AI Glass theme
  const [theme, setThemeState] = useState<Theme>('dark');
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('dark');
  const [mounted, setMounted] = useState(false);

  // Apply theme to document - always dark
  const applyTheme = useCallback((resolved: 'light' | 'dark') => {
    if (typeof document !== 'undefined') {
      document.documentElement.classList.remove('light', 'dark');
      // Always apply dark for Midnight AI Glass theme
      document.documentElement.classList.add('dark');
      setResolvedTheme('dark');
    }
  }, []);

  // Initialize theme on mount - force dark
  useEffect(() => {
    setMounted(true);
    // Always start with dark mode for Midnight AI Glass theme
    setThemeState('dark');
    applyTheme('dark');
    // Store preference
    localStorage.setItem(STORAGE_KEY, 'dark');
  }, [applyTheme]);

  const setTheme = useCallback((newTheme: Theme) => {
    // For Midnight AI Glass theme, we always use dark mode
    // but keep the API functional for future theme toggle support
    setThemeState('dark');
    localStorage.setItem(STORAGE_KEY, 'dark');
    applyTheme('dark');
  }, [applyTheme]);

  const toggleTheme = useCallback(() => {
    // No-op for Midnight AI Glass theme (dark only)
    // Keep API functional for future support
    setTheme('dark');
  }, [setTheme]);

  const value = useMemo<ThemeContextType>(() => ({
    theme,
    resolvedTheme,
    setTheme,
    toggleTheme,
  }), [theme, resolvedTheme, setTheme, toggleTheme]);

  // Prevent flash of unstyled content
  if (!mounted) {
    return null;
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}

export default ThemeContext;
