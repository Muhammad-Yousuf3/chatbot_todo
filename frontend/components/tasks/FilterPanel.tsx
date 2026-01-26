'use client';

/**
 * FilterPanel Component
 * Feature: 010-ui-enablement
 * Updated: 011-midnight-glass-ui - Glass panel styling with accent highlights
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
  high: 'text-error-400',
  medium: 'text-warning-400',
  low: 'text-success-400',
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
    <div className="p-4 glass rounded-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-dark-50">
          Filters
          {activeFilterCount > 0 && (
            <span className="ml-2 px-2 py-0.5 text-xs bg-gradient-to-r from-primary-400 to-primary-600 text-white rounded-full">
              {activeFilterCount}
            </span>
          )}
        </h3>
        {activeFilterCount > 0 && (
          <button
            type="button"
            onClick={onClearFilters}
            className="text-xs text-primary-400 hover:text-primary-300 font-medium transition-colors"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Priority Filter */}
      <div>
        <label className="text-xs font-medium text-dark-300 uppercase tracking-wide mb-2 block">
          Priority
        </label>
        <div className="space-y-1.5">
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="radio"
              name="priority-filter"
              checked={priorityFilter === null}
              onChange={() => onPrioritySelect(null)}
              className="w-4 h-4 text-primary-400 border-dark-600 focus:ring-2 focus:ring-primary-400/50 bg-dark-700 cursor-pointer accent-primary-400"
            />
            <span className="text-sm text-dark-300 group-hover:text-dark-100 transition-colors">
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
                className="w-4 h-4 text-primary-400 border-dark-600 focus:ring-2 focus:ring-primary-400/50 bg-dark-700 cursor-pointer accent-primary-400"
              />
              <span className={cn(
                "text-sm transition-colors",
                priorityFilter === priority
                  ? priorityColors[priority]
                  : "text-dark-300 group-hover:text-dark-100"
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
          <label htmlFor="tag-filter" className="text-xs font-medium text-dark-300 uppercase tracking-wide mb-2 block">
            Tag
          </label>
          <select
            id="tag-filter"
            value={tagFilter || ''}
            onChange={(e) => onTagSelect(e.target.value || null)}
            className="w-full input-glass cursor-pointer"
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
