'use client';

/**
 * SortControls Component
 * Feature: 010-ui-enablement
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
      <span className="text-sm text-slate-600 dark:text-slate-400 font-medium whitespace-nowrap">
        Sort by:
      </span>

      {/* Sort Field Dropdown */}
      <select
        aria-label="Sort field"
        value={sortBy}
        onChange={(e) => onSortByChange(e.target.value as SortField)}
        className="px-3 py-1.5 border border-slate-300 dark:border-dark-600 rounded-lg text-sm text-slate-800 dark:text-white dark:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
      >
        {Object.entries(sortFieldLabels).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>

      {/* Sort Order Toggle */}
      <button
        type="button"
        onClick={() => onSortOrderChange(sortOrder === 'asc' ? 'desc' : 'asc')}
        className="p-1.5 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-dark-700 rounded-lg transition-colors"
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
