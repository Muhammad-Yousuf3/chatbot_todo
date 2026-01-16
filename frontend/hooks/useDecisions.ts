'use client';

/**
 * useDecisions Hook - SWR wrapper for decision logs
 * Feature: 006-frontend-chat-ui
 */

import useSWR from 'swr';
import { fetcher } from '@/lib/fetcher';
import type {
  DecisionQueryResponse,
  DecisionTraceResponse,
  DecisionLog,
  ToolInvocationLog,
  DecisionLogResponse,
  ToolInvocationLogResponse,
} from '@/types';

// Transform snake_case API response to camelCase for UI
function transformDecision(d: DecisionLogResponse): DecisionLog {
  return {
    decisionId: d.decision_id,
    conversationId: d.conversation_id,
    userId: d.user_id,
    message: d.message,
    intentType: d.intent_type,
    confidence: d.confidence,
    decisionType: d.decision_type,
    outcomeCategory: d.outcome_category,
    responseText: d.response_text,
    createdAt: d.created_at,
    durationMs: d.duration_ms,
  };
}

function transformToolInvocation(t: ToolInvocationLogResponse): ToolInvocationLog {
  return {
    toolName: t.tool_name,
    parameters: t.parameters,
    result: t.result,
    success: t.success,
    errorCode: t.error_code,
    errorMessage: t.error_message,
    durationMs: t.duration_ms,
    invokedAt: t.invoked_at,
    sequence: t.sequence,
  };
}

interface UseDecisionsOptions {
  /** Filter by conversation ID */
  conversationId?: string;
  /** Filter by user ID */
  userId?: string;
  /** Start time for query (ISO string) */
  startTime?: string;
  /** End time for query (ISO string) */
  endTime?: string;
  /** Filter by decision type */
  decisionType?: string;
  /** Filter by outcome category */
  outcomeCategory?: string;
  /** Number of results per page */
  limit?: number;
  /** Pagination offset */
  offset?: number;
  /** Refresh interval in ms (default: 30000 = 30s) */
  refreshInterval?: number;
}

interface TransformedDecisionQuery {
  items: DecisionLog[];
  total: number;
  hasMore: boolean;
}

interface UseDecisionsResult {
  decisions: TransformedDecisionQuery | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | undefined;
  mutate: () => void;
}

export function useDecisions({
  conversationId,
  userId,
  startTime,
  endTime,
  decisionType,
  outcomeCategory,
  limit = 50,
  offset = 0,
  refreshInterval = 30000,
}: UseDecisionsOptions = {}): UseDecisionsResult {
  // Build query string
  const params = new URLSearchParams();
  if (conversationId) params.set('conversation_id', conversationId);
  if (userId) params.set('user_id', userId);
  if (startTime) params.set('start_time', startTime);
  if (endTime) params.set('end_time', endTime);
  if (decisionType) params.set('decision_type', decisionType);
  if (outcomeCategory) params.set('outcome_category', outcomeCategory);
  params.set('limit', String(limit));
  params.set('offset', String(offset));

  const url = `/api/observability/decisions?${params.toString()}`;

  const { data, error, isLoading, mutate } = useSWR<DecisionQueryResponse>(
    url,
    fetcher,
    {
      refreshInterval,
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  );

  // Transform to camelCase
  const transformed: TransformedDecisionQuery | undefined = data
    ? {
        items: data.items.map(transformDecision),
        total: data.total,
        hasMore: data.has_more,
      }
    : undefined;

  return {
    decisions: transformed,
    isLoading,
    isError: !!error,
    error,
    mutate,
  };
}

/**
 * Hook to fetch a single decision trace
 */
interface UseDecisionTraceOptions {
  decisionId: string | null;
  enabled?: boolean;
}

interface TransformedDecisionTrace {
  decision: DecisionLog;
  toolInvocations: ToolInvocationLog[];
}

interface UseDecisionTraceResult {
  trace: TransformedDecisionTrace | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | undefined;
}

export function useDecisionTrace({
  decisionId,
  enabled = true,
}: UseDecisionTraceOptions): UseDecisionTraceResult {
  const url = decisionId
    ? `/api/observability/decisions/${decisionId}/trace`
    : null;

  const { data, error, isLoading } = useSWR<DecisionTraceResponse>(
    enabled && url ? url : null,
    fetcher,
    {
      revalidateOnFocus: false,
    }
  );

  // Transform to camelCase
  const transformed: TransformedDecisionTrace | undefined = data
    ? {
        decision: transformDecision(data.decision),
        toolInvocations: data.tool_invocations.map(transformToolInvocation),
      }
    : undefined;

  return {
    trace: transformed,
    isLoading,
    isError: !!error,
    error,
  };
}

export default useDecisions;
