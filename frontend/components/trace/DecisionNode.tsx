'use client';

/**
 * DecisionNode Component - Single decision in the timeline
 * Feature: 006-frontend-chat-ui
 */

import React from 'react';
import type { DecisionLog } from '@/types';
import { cn, formatRelativeTime } from '@/lib/utils';

interface DecisionNodeProps {
  decision: DecisionLog;
  isSelected: boolean;
  onClick: () => void;
}

export function DecisionNode({
  decision,
  isSelected,
  onClick,
}: DecisionNodeProps) {
  // Determine status based on outcomeCategory
  const isSuccess = decision.outcomeCategory.startsWith('SUCCESS:');
  const isError = decision.outcomeCategory.startsWith('ERROR:');

  // Format intent for display
  const formatIntent = (intent: string) => {
    return intent
      .replace(/_/g, ' ')
      .toLowerCase()
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div
      className={cn(
        'relative pl-10 cursor-pointer group',
        'transition-colors duration-200'
      )}
      onClick={onClick}
    >
      {/* Timeline dot */}
      <div
        className={cn(
          'absolute left-2.5 w-3 h-3 rounded-full border-2 bg-white',
          'transform -translate-x-1/2',
          isSuccess && 'border-success-500',
          isError && 'border-error-500',
          !isSuccess && !isError && 'border-slate-400',
          isSelected && 'ring-2 ring-primary-300'
        )}
      />

      {/* Content card */}
      <div
        className={cn(
          'p-4 rounded-lg border transition-all duration-200',
          isSelected
            ? 'bg-primary-50 border-primary-300 shadow-sm'
            : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-sm'
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                'px-2 py-0.5 text-xs font-medium rounded-full',
                isSuccess && 'bg-success-100 text-success-700',
                isError && 'bg-error-100 text-error-700',
                !isSuccess && !isError && 'bg-slate-100 text-slate-700'
              )}
            >
              {formatIntent(decision.intentType)}
            </span>
            <span className="text-xs text-slate-400">
              {formatRelativeTime(decision.createdAt)}
            </span>
          </div>
          <span className="text-xs text-slate-500">
            {decision.durationMs}ms
          </span>
        </div>

        {/* Message preview */}
        <p className="text-sm text-slate-700 line-clamp-2 mb-2">
          {decision.message}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between text-xs">
          <span
            className={cn(
              'font-medium',
              isSuccess && 'text-success-600',
              isError && 'text-error-600',
              !isSuccess && !isError && 'text-slate-500'
            )}
          >
            {decision.outcomeCategory}
          </span>
          {decision.confidence !== null && (
            <span className="text-slate-400">
              Confidence: {(decision.confidence * 100).toFixed(0)}%
            </span>
          )}
        </div>

        {/* Expand indicator */}
        <div
          className={cn(
            'mt-2 pt-2 border-t border-slate-100 flex items-center justify-center',
            'text-xs text-slate-400 group-hover:text-primary-500',
            'transition-colors duration-200'
          )}
        >
          <svg
            className={cn(
              'w-4 h-4 mr-1 transition-transform duration-200',
              isSelected && 'rotate-180'
            )}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
          {isSelected ? 'Collapse' : 'Expand to view tools'}
        </div>
      </div>
    </div>
  );
}

export default DecisionNode;
