'use client';

/**
 * FilterPanel Component
 * Feature: 010-ui-enablement
 *
 * Provides checkboxes for filtering by priority and tag selection.
 * Displays active filter count and clear button.
 */

import React from 'react';
import { cn } from '@/lib/utils';
import type { TaskPriority } from '@/types';

interface FilterPanelProps {
  priorityFilter: TaskPriority | null;
  tagFilter: string | null;
  availableTags: string[];
  onPrioritySelect: (priority: TaskPriority | null) => void;
  onTagSelect: (tag: string | null) => void;
  onClearFilters: () => void;
  activeFilterCount: number;
}

const priorityLabels: Record<TaskPriority, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
};

const priorityColors: Record<TaskPriority, string> = {
  high: 'text-error-700 dark:text-error-400',
  medium: 'text-primary-700 dark:text-primary-400',
  low: 'text-slate-600 dark:text-slate-400',
};

export function FilterPanel({
  priorityFilter,
  tagFilter,
  availableTags,
  onPrioritySelect,
  onTagSelect,
  onClearFilters,
  activeFilterCount,
}: FilterPanelProps) {
  return (
    <div className="p-4 bg-slate-50 dark:bg-dark-800 border border-slate-200 dark:border-dark-700 rounded-lg space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
          Filters
          {activeFilterCount > 0 && (
            <span className="ml-2 px-2 py-0.5 text-xs bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400 rounded-full">
              {activeFilterCount}
            </span>
          )}
        </h3>
        {activeFilterCount > 0 && (
          <button
            type="button"
            onClick={onClearFilters}
            className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Priority Filter */}
      <div>
        <label className="text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-2 block">
          Priority
        </label>
        <div className="space-y-1.5">
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="radio"
              name="priority-filter"
              checked={priorityFilter === null}
              onChange={() => onPrioritySelect(null)}
              className="w-4 h-4 text-primary-600 border-slate-300 dark:border-dark-600 focus:ring-2 focus:ring-primary-500 dark:bg-dark-700 cursor-pointer"
            />
            <span className="text-sm text-slate-600 dark:text-slate-400 group-hover:underline">
              All priorities
            </span>
          </label>
          {(['high', 'medium', 'low'] as TaskPriority[]).map((priority) => (
            <label
              key={priority}
              className="flex items-center gap-2 cursor-pointer group"
            >
              <input
                type="radio"
                name="priority-filter"
                checked={priorityFilter === priority}
                onChange={() => onPrioritySelect(priority)}
                className="w-4 h-4 text-primary-600 border-slate-300 dark:border-dark-600 focus:ring-2 focus:ring-primary-500 dark:bg-dark-700 cursor-pointer"
              />
              <span className={cn(
                "text-sm group-hover:underline",
                priorityFilter === priority
                  ? priorityColors[priority]
                  : "text-slate-600 dark:text-slate-400"
              )}>
                {priorityLabels[priority]}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Tag Filter */}
      {availableTags.length > 0 && (
        <div>
          <label htmlFor="tag-filter" className="text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-2 block">
            Tag
          </label>
          <select
            id="tag-filter"
            value={tagFilter || ''}
            onChange={(e) => onTagSelect(e.target.value || null)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-dark-600 rounded-lg text-sm text-slate-800 dark:text-white dark:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="">All tags</option>
            {availableTags.map((tag) => (
              <option key={tag} value={tag}>
                #{tag}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}

export default FilterPanel;
