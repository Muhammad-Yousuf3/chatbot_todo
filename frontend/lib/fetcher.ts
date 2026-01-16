/**
 * SWR Fetcher with error handling
 * Feature: 006-frontend-chat-ui
 */

import { apiClient, ApiClientError } from './api';

export class FetcherError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = 'FetcherError';
  }
}

/**
 * SWR-compatible fetcher function
 * Uses the API client singleton for consistent headers
 * Updated: 007-jwt-authentication - Uses JWT Bearer tokens
 */
export async function fetcher<T>(url: string): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const accessToken = apiClient.getAccessToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  try {
    const response = await fetch(baseUrl + url, { headers });

    if (!response.ok) {
      let errorData: { error?: { code?: string; message?: string } } = {};
      try {
        errorData = await response.json();
      } catch {
        // Not JSON
      }

      throw new FetcherError(
        response.status,
        errorData.error?.code || 'UNKNOWN',
        errorData.error?.message || 'HTTP ' + response.status
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof FetcherError) {
      throw error;
    }

    if (error instanceof Error) {
      throw new FetcherError(0, 'NETWORK_ERROR', error.message);
    }

    throw new FetcherError(0, 'UNKNOWN', 'Unknown error');
  }
}

export default fetcher;
