'use client';

/**
 * useAuth Hook - wrapper for AuthContext
 * Feature: 006-frontend-chat-ui
 */

import { useAuthContext } from '@/contexts/AuthContext';

export function useAuth() {
  return useAuthContext();
}

export default useAuth;
