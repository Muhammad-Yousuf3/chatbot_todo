'use client';

/**
 * useMetrics Hook - SWR wrapper for metrics data
 * Feature: 006-frontend-chat-ui
 */

import useSWR from 'swr';
import { fetcher } from '@/lib/fetcher';
import type { MetricsSummaryResponse } from '@/types';

interface UseMetricsOptions {
  /** Start time for metrics period (ISO string) */
  startTime: string;
  /** End time for metrics period (ISO string), defaults to now */
  endTime?: string;
  /** Filter by user ID */
  userId?: string;
  /** Refresh interval in ms (default: 60000 = 1 minute) */
  refreshInterval?: number;
}

interface UseMetricsResult {
  metrics: MetricsSummaryResponse | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | undefined;
  mutate: () => void;
}

export function useMetrics({
  startTime,
  endTime,
  userId,
  refreshInterval = 60000,
}: UseMetricsOptions): UseMetricsResult {
  // Build query string
  const params = new URLSearchParams();
  params.set('start_time', startTime);
  if (endTime) params.set('end_time', endTime);
  if (userId) params.set('user_id', userId);

  const url = `/api/observability/metrics?${params.toString()}`;

  const { data, error, isLoading, mutate } = useSWR<MetricsSummaryResponse>(
    url,
    fetcher,
    {
      refreshInterval,
      revalidateOnFocus: false,
      dedupingInterval: 10000,
    }
  );

  return {
    metrics: data,
    isLoading,
    isError: !!error,
    error,
    mutate,
  };
}

export default useMetrics;
