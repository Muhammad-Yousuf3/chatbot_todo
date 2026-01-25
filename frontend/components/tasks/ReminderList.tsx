'use client';

/**
 * ReminderList Component
 * Feature: 010-ui-enablement
 *
 * Manages multiple reminder times for a task (max 5).
 * Displays help text explaining reminders are scheduled but not delivered.
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { VALIDATION_LIMITS } from '@/lib/utils';
import { DateTimePicker } from './DateTimePicker';

interface Reminder {
  trigger_at: string; // ISO 8601 datetime string
}

interface ReminderListProps {
  reminders: Reminder[];
  onChange: (reminders: Reminder[]) => void;
  disabled?: boolean;
  error?: string;
  dueDate?: string | null; // ISO string, for validation warnings
  maxReminders?: number;
}

export function ReminderList({
  reminders,
  onChange,
  disabled = false,
  error,
  dueDate,
  maxReminders = VALIDATION_LIMITS.MAX_REMINDERS,
}: ReminderListProps) {
  const handleAddReminder = () => {
    if (reminders.length >= maxReminders) return;

    // Default to 1 day before due date, or tomorrow if no due date
    const defaultTime = dueDate
      ? new Date(new Date(dueDate).getTime() - 24 * 60 * 60 * 1000)
      : new Date(Date.now() + 24 * 60 * 60 * 1000);

    onChange([
      ...reminders,
      { trigger_at: defaultTime.toISOString() },
    ]);
  };

  const handleRemoveReminder = (index: number) => {
    onChange(reminders.filter((_, i) => i !== index));
  };

  const handleUpdateReminder = (index: number, triggerAt: string | null) => {
    if (!triggerAt) {
      handleRemoveReminder(index);
      return;
    }

    const updated = [...reminders];
    updated[index] = { trigger_at: triggerAt };
    onChange(updated);
  };

  // Check if reminder is after due date
  const isReminderAfterDueDate = (reminderTime: string): boolean => {
    if (!dueDate) return false;
    return new Date(reminderTime) > new Date(dueDate);
  };

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <label className="text-sm text-slate-600 dark:text-slate-400 font-medium">
          Reminders ({reminders.length}/{maxReminders})
        </label>
        <button
          type="button"
          onClick={handleAddReminder}
          disabled={disabled || reminders.length >= maxReminders}
          className={cn(
            'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
            'bg-primary-100 text-primary-700 hover:bg-primary-200',
            'dark:bg-primary-900/30 dark:text-primary-400 dark:hover:bg-primary-800/50',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          <span className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Reminder
          </span>
        </button>
      </div>

      {/* Help Text */}
      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div className="flex gap-2">
          <svg className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-xs text-blue-700 dark:text-blue-300">
            <p className="font-medium mb-1">Reminders are scheduled but not delivered</p>
            <p>
              This feature stores reminder times in the database for future notification integration.
              No alerts or emails will be sent at this time.
            </p>
          </div>
        </div>
      </div>

      {/* Reminder List */}
      {reminders.length > 0 && (
        <div className="space-y-3">
          {reminders.map((reminder, index) => {
            const afterDueDate = dueDate && isReminderAfterDueDate(reminder.trigger_at);
            return (
              <div
                key={index}
                className="p-3 bg-slate-50 dark:bg-dark-700 border border-slate-200 dark:border-dark-600 rounded-lg"
              >
                <div className="flex items-start gap-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                        Reminder {index + 1}
                      </span>
                      {afterDueDate && (
                        <span className="text-xs text-warning-600 dark:text-warning-400 flex items-center gap-1">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          After due date
                        </span>
                      )}
                    </div>
                    <DateTimePicker
                      value={reminder.trigger_at}
                      onChange={(isoString) => handleUpdateReminder(index, isoString)}
                      label=""
                      disabled={disabled}
                      required={false}
                      showTimezone={false}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveReminder(index)}
                    disabled={disabled}
                    className="mt-6 p-1.5 text-slate-400 hover:text-error-500 hover:bg-error-50 dark:hover:bg-error-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label={`Remove reminder ${index + 1}`}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty State */}
      {reminders.length === 0 && (
        <div className="p-4 text-center border-2 border-dashed border-slate-200 dark:border-dark-600 rounded-lg">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No reminders yet. Click "Add Reminder" to schedule a notification time.
          </p>
        </div>
      )}

      {/* Validation Error */}
      {error && (
        <p className="text-xs text-error-500 dark:text-error-400">{error}</p>
      )}

      {/* Max Limit Info */}
      {reminders.length >= maxReminders && (
        <p className="text-xs text-warning-600 dark:text-warning-400">
          Maximum {maxReminders} reminders per task
        </p>
      )}
    </div>
  );
}

export default ReminderList;
