'use client';

/**
 * ToolInvocationCard Component - Display a single tool invocation
 * Feature: 006-frontend-chat-ui
 */

import React, { useState } from 'react';
import type { ToolInvocationLog } from '@/types';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

interface ToolInvocationCardProps {
  invocation: ToolInvocationLog;
  sequence: number;
}

export function ToolInvocationCard({
  invocation,
  sequence,
}: ToolInvocationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Format tool name
  const formatToolName = (name: string) => {
    return name
      .replace(/^mcp_/, '')
      .replace(/_/g, ' ')
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Format JSON for display
  const formatJson = (obj: unknown): string => {
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(obj);
    }
  };

  return (
    <Card
      className={cn(
        'p-4',
        invocation.success ? 'border-l-4 border-l-success-500' : 'border-l-4 border-l-error-500'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-xs font-medium text-slate-600">
            {sequence}
          </span>
          <span className="font-medium text-slate-800">
            {formatToolName(invocation.toolName)}
          </span>
          <span
            className={cn(
              'px-2 py-0.5 text-xs font-medium rounded-full',
              invocation.success
                ? 'bg-success-100 text-success-700'
                : 'bg-error-100 text-error-700'
            )}
          >
            {invocation.success ? 'Success' : 'Failed'}
          </span>
        </div>
        <span className="text-xs text-slate-500">
          {invocation.durationMs}ms
        </span>
      </div>

      {/* Error message if failed */}
      {!invocation.success && invocation.errorMessage && (
        <div className="mb-3 p-2 bg-error-50 rounded text-sm text-error-700">
          <span className="font-medium">{invocation.errorCode}: </span>
          {invocation.errorMessage}
        </div>
      )}

      {/* Expand/collapse button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-xs text-slate-500 hover:text-primary-600 flex items-center gap-1 mb-2"
      >
        <svg
          className={cn(
            'w-3 h-3 transition-transform',
            isExpanded && 'rotate-90'
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
        {isExpanded ? 'Hide details' : 'Show details'}
      </button>

      {/* Expanded details */}
      {isExpanded && (
        <div className="space-y-3">
          {/* Parameters */}
          <div>
            <p className="text-xs font-medium text-slate-500 mb-1">Parameters</p>
            <pre className="p-2 bg-slate-50 rounded text-xs text-slate-700 overflow-x-auto max-h-40">
              {formatJson(invocation.parameters)}
            </pre>
          </div>

          {/* Result */}
          {invocation.result && (
            <div>
              <p className="text-xs font-medium text-slate-500 mb-1">Result</p>
              <pre className="p-2 bg-slate-50 rounded text-xs text-slate-700 overflow-x-auto max-h-40">
                {formatJson(invocation.result)}
              </pre>
            </div>
          )}

          {/* Timestamp */}
          <p className="text-xs text-slate-400">
            Invoked at: {new Date(invocation.invokedAt).toLocaleString()}
          </p>
        </div>
      )}
    </Card>
  );
}

export default ToolInvocationCard;
