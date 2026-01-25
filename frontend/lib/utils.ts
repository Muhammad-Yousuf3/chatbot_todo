/**
 * Utility functions
 * Feature: 006-frontend-chat-ui
 */

import { type ClassValue, clsx } from 'clsx';

/**
 * Combines class names with clsx for conditional styling
 * Note: Using clsx directly since we're not using tailwind-merge
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

/**
 * Format date for display
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

/**
 * Format date with time
 */
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

/**
 * Format relative time (e.g., "2 minutes ago")
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) {
    return 'just now';
  } else if (diffMin < 60) {
    return diffMin + ' minute' + (diffMin === 1 ? '' : 's') + ' ago';
  } else if (diffHour < 24) {
    return diffHour + ' hour' + (diffHour === 1 ? '' : 's') + ' ago';
  } else if (diffDay < 7) {
    return diffDay + ' day' + (diffDay === 1 ? '' : 's') + ' ago';
  } else {
    return formatDate(dateString);
  }
}

/**
 * Format duration in milliseconds to human readable
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return ms + 'ms';
  } else if (ms < 60000) {
    return (ms / 1000).toFixed(1) + 's';
  } else {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return minutes + 'm ' + seconds + 's';
  }
}

/**
 * Format percentage
 */
export function formatPercent(value: number): string {
  return (value * 100).toFixed(1) + '%';
}

/**
 * Generate a UUID v4
 */
export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

// ============================================================================
// Task Validation - Feature: 010-ui-enablement
// ============================================================================

/**
 * Validation limits matching backend constraints
 */
export const VALIDATION_LIMITS = {
  TITLE_MIN_LENGTH: 1,
  TITLE_MAX_LENGTH: 200,
  DESCRIPTION_MAX_LENGTH: 2000,
  MAX_TAGS: 10,
  MAX_TAG_LENGTH: 50,
  MAX_REMINDERS: 5,
} as const;

/**
 * Validate task form state
 * Returns validation errors or empty object if valid
 */
export function validateTaskForm(state: {
  title: string;
  description: string;
  tags: string[];
  reminders: Array<{ trigger_at: string }>;
  recurrence: { recurrence_type: string; cron_expression?: string | null } | null;
}): Record<string, string> {
  const errors: Record<string, string> = {};

  // Title validation
  if (!state.title.trim()) {
    errors.title = 'Title is required';
  } else if (state.title.length > VALIDATION_LIMITS.TITLE_MAX_LENGTH) {
    errors.title = `Title must be ${VALIDATION_LIMITS.TITLE_MAX_LENGTH} characters or less`;
  }

  // Description validation
  if (state.description.length > VALIDATION_LIMITS.DESCRIPTION_MAX_LENGTH) {
    errors.description = `Description must be ${VALIDATION_LIMITS.DESCRIPTION_MAX_LENGTH} characters or less`;
  }

  // Tags validation
  if (state.tags.length > VALIDATION_LIMITS.MAX_TAGS) {
    errors.tags = `Maximum ${VALIDATION_LIMITS.MAX_TAGS} tags allowed`;
  }
  const invalidTag = state.tags.find(tag => tag.length > VALIDATION_LIMITS.MAX_TAG_LENGTH);
  if (invalidTag) {
    errors.tags = `Each tag must be ${VALIDATION_LIMITS.MAX_TAG_LENGTH} characters or less`;
  }

  // Reminders validation
  if (state.reminders.length > VALIDATION_LIMITS.MAX_REMINDERS) {
    errors.reminders = `Maximum ${VALIDATION_LIMITS.MAX_REMINDERS} reminders allowed`;
  }

  // Recurrence validation
  if (state.recurrence) {
    if (state.recurrence.recurrence_type === 'custom' && !state.recurrence.cron_expression) {
      errors.cron_expression = 'Cron expression is required for custom recurrence';
    }
  }

  return errors;
}

/**
 * Build query string from task query params
 * Omits undefined/null values
 */
export function buildTaskQueryString(params: {
  status?: string;
  priority?: string;
  tag?: string;
  search?: string;
  due_before?: string;
  due_after?: string;
  sort_by?: string;
  sort_order?: string;
  limit?: number;
  offset?: number;
}): string {
  const searchParams = new URLSearchParams();

  if (params.status) searchParams.append('status', params.status);
  if (params.priority) searchParams.append('priority', params.priority);
  if (params.tag) searchParams.append('tag', params.tag);
  if (params.search) searchParams.append('search', params.search);
  if (params.due_before) searchParams.append('due_before', params.due_before);
  if (params.due_after) searchParams.append('due_after', params.due_after);
  if (params.sort_by) searchParams.append('sort_by', params.sort_by);
  if (params.sort_order) searchParams.append('sort_order', params.sort_order);
  if (params.limit !== undefined) searchParams.append('limit', params.limit.toString());
  if (params.offset !== undefined) searchParams.append('offset', params.offset.toString());

  return searchParams.toString();
}
