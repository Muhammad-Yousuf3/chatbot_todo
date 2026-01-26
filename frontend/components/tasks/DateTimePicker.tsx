'use client';

/**
 * DateTimePicker Component
 * Feature: 010-ui-enablement
 * Updated: 011-midnight-glass-ui - Glass input styling with focus glow
 *
 * HTML5 datetime-local input for selecting date and time.
 * Handles conversion between ISO 8601 UTC and browser local timezone.
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface DateTimePickerProps {
  value: string | null; // ISO 8601 UTC string or null
  onChange: (isoString: string | null) => void;
  label?: string;
  disabled?: boolean;
  error?: string;
  required?: boolean;
  showTimezone?: boolean;
}

/**
 * Convert ISO 8601 UTC string to datetime-local format
 * Input: "2026-01-26T19:30:00Z"
 * Output: "2026-01-26T14:30" (in user's local timezone)
 */
function isoToDatetimeLocal(isoString: string | null): string {
  if (!isoString) return '';
  const date = new Date(isoString);
  // Format: YYYY-MM-DDTHH:mm
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * Convert datetime-local format to ISO 8601 UTC string
 * Input: "2026-01-26T14:30"
 * Output: "2026-01-26T19:30:00.000Z"
 */
function datetimeLocalToISO(datetimeLocal: string): string {
  if (!datetimeLocal) return '';
  const date = new Date(datetimeLocal);
  return date.toISOString();
}

export function DateTimePicker({
  value,
  onChange,
  label = 'Due date and time',
  disabled = false,
  error,
  required = false,
  showTimezone = true,
}: DateTimePickerProps) {
  const localValue = isoToDatetimeLocal(value);
  const timezone = new Date().toLocaleTimeString('en-US', { timeZoneName: 'short' }).split(' ')[2];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    if (newValue) {
      onChange(datetimeLocalToISO(newValue));
    } else {
      onChange(null);
    }
  };

  const handleClear = () => {
    onChange(null);
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label className="text-sm text-dark-300 font-medium flex items-center gap-1.5">
          <svg className="w-4 h-4 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          {label}
          {!required && <span className="text-xs text-dark-500">(optional)</span>}
        </label>
        {showTimezone && (
          <span className="text-xs text-dark-500">
            {timezone}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        <input
          type="datetime-local"
          value={localValue}
          onChange={handleChange}
          disabled={disabled}
          required={required}
          className={cn(
            'flex-1 input-glass',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            error && 'border-error-500/50 focus:ring-error-500/50'
          )}
        />
        {localValue && !disabled && (
          <button
            type="button"
            onClick={handleClear}
            className="p-2 text-dark-400 hover:text-error-400 hover:bg-error-500/10 rounded-lg transition-all duration-200"
            aria-label="Clear date and time"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>

      {error && (
        <p className="text-xs text-error-400">{error}</p>
      )}
    </div>
  );
}

export default DateTimePicker;

// Export helper functions for use in other components
export { isoToDatetimeLocal, datetimeLocalToISO };
