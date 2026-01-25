'use client';

/**
 * RecurrenceSelector Component
 * Feature: 010-ui-enablement
 *
 * Allows users to configure task recurrence (daily, weekly, or custom cron expression).
 * Displays help text with cron expression examples.
 */

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import type { RecurrenceType } from '@/types';

interface RecurrenceSelectorProps {
  recurrenceType: RecurrenceType | null;
  cronExpression: string;
  onChange: (type: RecurrenceType | null, cron: string) => void;
  disabled?: boolean;
  error?: string;
}

const recurrenceOptions: { value: RecurrenceType | null; label: string; description: string }[] = [
  { value: null, label: 'None', description: 'Task does not repeat' },
  { value: 'daily', label: 'Daily', description: 'Repeats every day' },
  { value: 'weekly', label: 'Weekly', description: 'Repeats every week' },
  { value: 'custom', label: 'Custom', description: 'Use cron expression for advanced scheduling' },
];

const cronExamples = [
  { expression: '0 9 * * *', description: 'Every day at 9:00 AM' },
  { expression: '0 */2 * * *', description: 'Every 2 hours' },
  { expression: '0 9 * * 1', description: 'Every Monday at 9:00 AM' },
  { expression: '0 0 1 * *', description: 'First day of every month at midnight' },
  { expression: '0 9 * * 1-5', description: 'Weekdays at 9:00 AM' },
];

export function RecurrenceSelector({
  recurrenceType,
  cronExpression,
  onChange,
  disabled = false,
  error,
}: RecurrenceSelectorProps) {
  const [showCronHelp, setShowCronHelp] = useState(false);

  const handleTypeChange = (type: RecurrenceType | null) => {
    onChange(type, cronExpression);
  };

  const handleCronChange = (cron: string) => {
    onChange(recurrenceType, cron);
  };

  return (
    <div className="space-y-3">
      {/* Recurrence Type Selection */}
      <div>
        <label className="text-sm text-slate-600 dark:text-slate-400 font-medium mb-2 block">
          Recurrence
        </label>
        <div className="grid grid-cols-2 gap-2">
          {recurrenceOptions.map((option) => (
            <button
              key={option.value || 'none'}
              type="button"
              onClick={() => handleTypeChange(option.value)}
              disabled={disabled}
              className={cn(
                'p-3 border rounded-lg text-left transition-colors',
                recurrenceType === option.value
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 dark:border-primary-600'
                  : 'border-slate-300 dark:border-dark-600 hover:bg-slate-50 dark:hover:bg-dark-700',
                disabled && 'opacity-50 cursor-not-allowed'
              )}
            >
              <div className="font-medium text-sm text-slate-800 dark:text-white">
                {option.label}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {option.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Cron Expression Input (shown only for custom) */}
      {recurrenceType === 'custom' && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label htmlFor="cron-expression" className="text-sm text-slate-600 dark:text-slate-400 font-medium">
              Cron Expression
            </label>
            <button
              type="button"
              onClick={() => setShowCronHelp(!showCronHelp)}
              className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
            >
              {showCronHelp ? 'Hide' : 'Show'} examples
            </button>
          </div>

          <input
            id="cron-expression"
            type="text"
            value={cronExpression}
            onChange={(e) => handleCronChange(e.target.value)}
            placeholder="0 9 * * *"
            disabled={disabled}
            className={cn(
              'w-full px-3 py-2 border rounded-lg text-sm font-mono',
              'text-slate-800 dark:text-white dark:bg-dark-700',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
              'placeholder:text-slate-400 dark:placeholder:text-slate-500',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              error
                ? 'border-error-500 dark:border-error-500'
                : 'border-slate-300 dark:border-dark-600'
            )}
          />

          {error && (
            <p className="text-xs text-error-500 dark:text-error-400">{error}</p>
          )}

          {/* Cron Help Text */}
          {showCronHelp && (
            <div className="p-3 bg-slate-50 dark:bg-dark-700 border border-slate-200 dark:border-dark-600 rounded-lg">
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Cron Expression Format: minute hour day month weekday
              </p>
              <div className="space-y-1.5">
                {cronExamples.map((example, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <code className="text-xs font-mono text-primary-600 dark:text-primary-400 bg-white dark:bg-dark-800 px-2 py-0.5 rounded flex-shrink-0">
                      {example.expression}
                    </code>
                    <span className="text-xs text-slate-600 dark:text-slate-400">
                      {example.description}
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                Use <a href="https://crontab.guru" target="_blank" rel="noopener noreferrer" className="text-primary-600 dark:text-primary-400 hover:underline">crontab.guru</a> for help creating cron expressions
              </p>
            </div>
          )}
        </div>
      )}

      {/* Info Text */}
      {recurrenceType && recurrenceType !== 'custom' && (
        <p className="text-xs text-slate-500 dark:text-slate-400">
          This task will be automatically recreated based on the selected schedule
        </p>
      )}
    </div>
  );
}

export default RecurrenceSelector;
