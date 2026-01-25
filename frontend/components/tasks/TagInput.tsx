'use client';

/**
 * TagInput Component
 * Feature: 010-ui-enablement
 *
 * Allows users to add and remove tags with chip display.
 * Enforces validation: max 10 tags, each max 50 characters.
 */

import React, { useState, KeyboardEvent } from 'react';
import { cn } from '@/lib/utils';
import { VALIDATION_LIMITS } from '@/lib/utils';

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  disabled?: boolean;
  error?: string;
  maxTags?: number;
  maxTagLength?: number;
}

export function TagInput({
  tags,
  onChange,
  disabled = false,
  error,
  maxTags = VALIDATION_LIMITS.MAX_TAGS,
  maxTagLength = VALIDATION_LIMITS.MAX_TAG_LENGTH,
}: TagInputProps) {
  const [inputValue, setInputValue] = useState('');
  const [inputError, setInputError] = useState<string | null>(null);

  const handleAddTag = () => {
    const trimmedTag = inputValue.trim();

    // Clear input error
    setInputError(null);

    // Validate: empty
    if (!trimmedTag) {
      return;
    }

    // Validate: max tags
    if (tags.length >= maxTags) {
      setInputError(`Maximum ${maxTags} tags allowed`);
      return;
    }

    // Validate: tag length
    if (trimmedTag.length > maxTagLength) {
      setInputError(`Tag must be ${maxTagLength} characters or less`);
      return;
    }

    // Validate: duplicate
    if (tags.includes(trimmedTag)) {
      setInputError('Tag already added');
      return;
    }

    // Add tag
    onChange([...tags, trimmedTag]);
    setInputValue('');
  };

  const handleRemoveTag = (tagToRemove: string) => {
    onChange(tags.filter((tag) => tag !== tagToRemove));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    } else if (e.key === 'Backspace' && inputValue === '' && tags.length > 0) {
      // Remove last tag when backspace is pressed on empty input
      e.preventDefault();
      onChange(tags.slice(0, -1));
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-col gap-2">
        {/* Tag chips display */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {tags.map((tag, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-sm bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400 rounded-full"
              >
                <span>#{tag}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  disabled={disabled}
                  className="hover:bg-primary-200 dark:hover:bg-primary-800/50 rounded-full p-0.5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label={`Remove tag ${tag}`}
                >
                  <svg
                    className="w-3 h-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Input field */}
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              tags.length >= maxTags
                ? `Max ${maxTags} tags reached`
                : 'Add tag...'
            }
            disabled={disabled || tags.length >= maxTags}
            className={cn(
              'flex-1 px-3 py-2 border rounded-lg text-sm',
              'text-slate-800 dark:text-white dark:bg-dark-700',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
              'placeholder:text-slate-400 dark:placeholder:text-slate-500',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              (error || inputError) && 'border-error-500 dark:border-error-500',
              !(error || inputError) && 'border-slate-300 dark:border-dark-600'
            )}
          />
          <button
            type="button"
            onClick={handleAddTag}
            disabled={disabled || !inputValue.trim() || tags.length >= maxTags}
            className={cn(
              'px-3 py-2 text-sm font-medium rounded-lg transition-colors',
              'bg-primary-100 text-primary-700 hover:bg-primary-200',
              'dark:bg-primary-900/30 dark:text-primary-400 dark:hover:bg-primary-800/50',
              'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-primary-100 dark:disabled:hover:bg-primary-900/30'
            )}
          >
            Add
          </button>
        </div>
      </div>

      {/* Error message */}
      {(error || inputError) && (
        <p className="text-xs text-error-500 dark:text-error-400">
          {error || inputError}
        </p>
      )}

      {/* Help text */}
      {!error && !inputError && (
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {tags.length}/{maxTags} tags • Press Enter to add • Backspace to remove last tag
        </p>
      )}
    </div>
  );
}

export default TagInput;
