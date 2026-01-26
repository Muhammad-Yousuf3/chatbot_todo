'use client';

/**
 * SortControls Component
 * Feature: 010-ui-enablement
 * Updated: 011-midnight-glass-ui - Glass dropdown with accent highlights
 *
 * Provides dropdown for sort field selection and toggle for sort order.
 * Supports sorting by: due_date, priority, title, created_at
 */

import React from 'react';
import { cn } from '@/lib/utils';

export type SortField = 'due_date' | 'priority' | 'title' | 'created_at';
export type SortOrder = 'asc' | 'desc';

interface SortControlsProps {
  sortBy: SortField;
  sortOrder: SortOrder;
  onSortByChange: (field: SortField) => void;
  onSortOrderChange: (order: SortOrder) => void;
}

const sortFieldLabels: Record<SortField, string> = {
  due_date: 'Due Date',
  priority: 'Priority',
  title: 'Title',
  created_at: 'Created Date',
};

export function SortControls({
  sortBy,
  sortOrder,
  onSortByChange,
  onSortOrderChange,
}: SortControlsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-dark-300 font-medium whitespace-nowrap">
        Sort by:
      </span>

      {/* Sort Field Dropdown - Glass styling */}
      <select
        aria-label="Sort field"
        value={sortBy}
        onChange={(e) => onSortByChange(e.target.value as SortField)}
        className="px-3 py-1.5 input-glass cursor-pointer"
      >
        {Object.entries(sortFieldLabels).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>

      {/* Sort Order Toggle - Accent highlight */}
      <button
        type="button"
        onClick={() => onSortOrderChange(sortOrder === 'asc' ? 'desc' : 'asc')}
        className={cn(
          'p-1.5 rounded-lg transition-all duration-200',
          'text-dark-300 hover:text-primary-400',
          'hover:bg-primary-400/10 hover:shadow-glow',
          'focus:outline-none focus:ring-2 focus:ring-primary-400/50'
        )}
        aria-label={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
        title={`Currently: ${sortOrder === 'asc' ? 'Ascending' : 'Descending'}`}
      >
        {sortOrder === 'asc' ? (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
          </svg>
        )}
      </button>
    </div>
  );
}

export default SortControls;
