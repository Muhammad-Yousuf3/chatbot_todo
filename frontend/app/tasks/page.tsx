'use client';

/**
 * Tasks Page - View and Manage Tasks
 * Feature: 006-frontend-chat-ui
 * Updated: 011-midnight-glass-ui - Glass cards, priority badges, enhanced forms
 *
 * Displays all tasks created by the chatbot with options to
 * complete, uncomplete, edit, and delete tasks.
 * Supports due dates for task scheduling.
 */

import React, { useState, Suspense, useMemo } from 'react';
import { Container } from '@/components/layout/Container';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useTasks } from '@/hooks/useTasks';
import { TagInput } from '@/components/tasks/TagInput';
import { SortControls, type SortField, type SortOrder } from '@/components/tasks/SortControls';
import { FilterPanel } from '@/components/tasks/FilterPanel';
import { DateTimePicker } from '@/components/tasks/DateTimePicker';
import { RecurrenceSelector } from '@/components/tasks/RecurrenceSelector';
import { ReminderList } from '@/components/tasks/ReminderList';
import { Toast, type ToastType } from '@/components/ui/Toast';
import type { Task, TaskStatus, TaskPriority, TaskCreateRequest, RecurrenceType, ReminderCreate } from '@/types';
import { cn, formatDate, validateTaskForm } from '@/lib/utils';

type FilterStatus = 'all' | TaskStatus;

// Priority Badge Component - Midnight Glass theme
function PriorityBadge({ priority }: { priority: TaskPriority }) {
  return (
    <span
      className={cn(
        'px-2 py-0.5 text-xs font-semibold rounded-full',
        priority === 'high' && 'priority-high',
        priority === 'medium' && 'priority-medium',
        priority === 'low' && 'priority-low'
      )}
    >
      {priority.charAt(0).toUpperCase() + priority.slice(1)}
    </span>
  );
}

function formatDueDate(dateStr: string | null): string | null {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  const now = new Date();
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dueDay = new Date(date);
  dueDay.setHours(0, 0, 0, 0);

  // Check if time is specified (not midnight UTC)
  const hasTime = date.getUTCHours() !== 0 || date.getUTCMinutes() !== 0;

  const diffDays = Math.ceil((dueDay.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  const diffMs = date.getTime() - now.getTime();
  const isOverdue = diffMs < 0;

  const timeStr = hasTime
    ? ` at ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`
    : '';

  if (isOverdue && diffDays < 0) {
    return `Overdue by ${Math.abs(diffDays)} day${Math.abs(diffDays) !== 1 ? 's' : ''}${timeStr}`;
  } else if (diffDays === 0 && !isOverdue) {
    return `Due today${timeStr}`;
  } else if (diffDays === 0 && isOverdue) {
    const hoursOverdue = Math.floor(Math.abs(diffMs) / (1000 * 60 * 60));
    if (hoursOverdue < 24) {
      return `Overdue by ${hoursOverdue} hour${hoursOverdue !== 1 ? 's' : ''}`;
    }
    return `Overdue${timeStr}`;
  } else if (diffDays === 1) {
    return `Due tomorrow${timeStr}`;
  } else if (diffDays <= 7) {
    return `Due in ${diffDays} days${timeStr}`;
  } else {
    const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    return `Due ${dateStr}${timeStr}`;
  }
}

function getDueDateStyle(dateStr: string | null, isCompleted: boolean): string {
  if (!dateStr || isCompleted) return 'text-dark-400';
  const date = new Date(dateStr);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dueDay = new Date(date);
  dueDay.setHours(0, 0, 0, 0);

  const diffDays = Math.ceil((dueDay.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return 'text-error-400 font-medium';
  } else if (diffDays <= 1) {
    return 'text-warning-400 font-medium';
  }
  return 'text-dark-400';
}

function TaskItem({
  task,
  onComplete,
  onUncomplete,
  onDelete,
  onEdit,
  onEditFull,
  isUpdating
}: {
  task: Task;
  onComplete: (id: string) => void;
  onUncomplete: (id: string) => void;
  onDelete: (id: string) => void;
  onEdit: (id: string, title: string) => void;
  onEditFull?: (id: string, data: { title?: string; description?: string }) => void;
  isUpdating: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(task.title);
  const [editDescription, setEditDescription] = useState(task.description || '');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleSaveEdit = () => {
    if (onEditFull) {
      const hasChanges = editTitle.trim() !== task.title || editDescription.trim() !== (task.description || '');
      if (hasChanges && editTitle.trim()) {
        onEditFull(task.id, {
          title: editTitle.trim(),
          description: editDescription.trim() || undefined
        });
      }
    } else if (editTitle.trim() && editTitle !== task.title) {
      onEdit(task.id, editTitle.trim());
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditTitle(task.title);
    setEditDescription(task.description || '');
    setIsEditing(false);
  };

  const handleDelete = () => {
    onDelete(task.id);
    setShowDeleteConfirm(false);
  };

  const isCompleted = task.status === 'completed';
  const dueDateText = formatDueDate(task.due_date);
  const dueDateStyle = getDueDateStyle(task.due_date, isCompleted);

  // Limit displayed tags
  const displayedTags = task.tags.slice(0, 3);
  const hiddenTagCount = task.tags.length - 3;

  return (
    <Card
      variant="glass"
      hover={!isCompleted}
      className={cn(
        'group transition-all duration-200',
        isCompleted && 'opacity-70'
      )}
    >
      <div className="flex items-start gap-4">
        {/* Checkbox - Accent styled */}
        <button
          onClick={() => isCompleted ? onUncomplete(task.id) : onComplete(task.id)}
          disabled={isUpdating}
          className={cn(
            'mt-1 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all flex-shrink-0',
            isCompleted
              ? 'bg-success-500 border-success-500 text-white'
              : 'border-primary-400/50 hover:border-primary-400 hover:shadow-glow',
            isUpdating && 'opacity-50 cursor-not-allowed'
          )}
          aria-label={isCompleted ? 'Mark as incomplete' : 'Mark as complete'}
        >
          {isCompleted && (
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </button>

        {/* Task Content */}
        <div className="flex-1 min-w-0">
          {isEditing ? (
            <div className="flex flex-col gap-3">
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                placeholder="Task title"
                className="input-glass w-full"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) handleSaveEdit();
                  if (e.key === 'Escape') handleCancelEdit();
                }}
              />
              <textarea
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder="Description (optional)"
                rows={3}
                maxLength={2000}
                className="input-glass w-full resize-y"
                onKeyDown={(e) => {
                  if (e.key === 'Escape') handleCancelEdit();
                }}
              />
              <div className="flex items-center justify-between">
                <p className="text-xs text-dark-400">
                  {editDescription.length}/2000
                </p>
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleSaveEdit}>Save</Button>
                  <Button size="sm" variant="ghost" onClick={handleCancelEdit}>Cancel</Button>
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* Title and Priority */}
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <h3
                  className={cn(
                    'text-dark-50 font-medium break-words',
                    isCompleted && 'line-through text-dark-400'
                  )}
                  title={task.title}
                >
                  {task.title}
                </h3>
                <PriorityBadge priority={task.priority} />
              </div>

              {/* Description - Truncated */}
              {task.description && (
                <p className={cn(
                  'text-sm text-dark-300 mb-2 line-clamp-2',
                  isCompleted && 'line-through text-dark-500'
                )}>
                  {task.description}
                </p>
              )}

              {/* Tags - Accent gradient chips */}
              {task.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {displayedTags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 text-xs font-medium bg-accent-gradient text-white rounded-full"
                    >
                      #{tag}
                    </span>
                  ))}
                  {hiddenTagCount > 0 && (
                    <span className="px-2 py-0.5 text-xs font-medium bg-dark-700 text-dark-300 rounded-full">
                      +{hiddenTagCount} more
                    </span>
                  )}
                </div>
              )}

              {/* Metadata row */}
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
                <span className="text-dark-400">
                  Created {formatDate(task.created_at)}
                </span>
                {task.completed_at && (
                  <span className="text-dark-400">
                    • Completed {formatDate(task.completed_at)}
                  </span>
                )}
                {dueDateText && (
                  <span className={cn('flex items-center gap-1', dueDateStyle)}>
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {dueDateText}
                  </span>
                )}
                {/* Recurrence indicator */}
                {task.recurrence && (
                  <span className="flex items-center gap-1 text-primary-400">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Recurring: {task.recurrence.recurrence_type}
                  </span>
                )}
                {/* Reminder indicator with tooltip */}
                {task.reminders.length > 0 && (
                  <span
                    className="flex items-center gap-1 text-warning-400"
                    title={`${task.reminders.length} reminder${task.reminders.length > 1 ? 's' : ''} scheduled`}
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    {task.reminders.length}
                  </span>
                )}
              </div>
            </>
          )}
        </div>

        {/* Actions */}
        {!isEditing && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {!isCompleted && (
              <button
                onClick={() => setIsEditing(true)}
                disabled={isUpdating}
                className="p-2 text-dark-400 hover:text-primary-400 hover:bg-dark-700/50 rounded-lg transition-colors"
                aria-label="Edit task"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
            )}
            {showDeleteConfirm ? (
              <div className="flex items-center gap-1">
                <button
                  onClick={handleDelete}
                  disabled={isUpdating}
                  className="px-2 py-1 text-xs bg-error-500 text-white rounded hover:bg-error-600 transition-colors"
                >
                  Delete
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-2 py-1 text-xs text-dark-300 hover:bg-dark-700/50 rounded transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                disabled={isUpdating}
                className="p-2 text-dark-400 hover:text-error-400 hover:bg-error-500/10 rounded-lg transition-colors"
                aria-label="Delete task"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

function TasksContent() {
  const [filter, setFilter] = useState<FilterStatus>('all');
  const [newTaskText, setNewTaskText] = useState('');
  const [newTaskDescription, setNewTaskDescription] = useState('');
  const [newTaskDueDate, setNewTaskDueDate] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState<TaskPriority>('medium');
  const [newTaskTags, setNewTaskTags] = useState<string[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Advanced options state
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [recurrenceType, setRecurrenceType] = useState<RecurrenceType | null>(null);
  const [cronExpression, setCronExpression] = useState('');
  const [reminders, setReminders] = useState<ReminderCreate[]>([]);

  // Toast notification state
  const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(null);

  // Sort state
  const [sortBy, setSortBy] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // Filter state
  const [priorityFilter, setPriorityFilter] = useState<TaskPriority | null>(null);
  const [tagFilter, setTagFilter] = useState<string | null>(null);

  const statusFilter = filter === 'all' ? undefined : filter;
  const {
    tasks,
    total,
    isLoading,
    isUpdating,
    error,
    createTask,
    completeTask,
    uncompleteTask,
    deleteTask,
    updateTask,
    refresh
  } = useTasks({
    status: statusFilter,
    sort_by: sortBy,
    sort_order: sortOrder,
    priority: priorityFilter || undefined,
    tag: tagFilter || undefined,
  });

  // Extract unique tags from all tasks
  const availableTags = useMemo(() => {
    const tagSet = new Set<string>();
    tasks.forEach(task => {
      task.tags.forEach(tag => tagSet.add(tag));
    });
    return Array.from(tagSet).sort();
  }, [tasks]);

  // Calculate active filter count
  const activeFilterCount = (priorityFilter ? 1 : 0) + (tagFilter ? 1 : 0);

  // Filter handlers
  const handleClearFilters = () => {
    setPriorityFilter(null);
    setTagFilter(null);
  };

  // Keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + K to focus on task input
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const taskInput = document.querySelector<HTMLInputElement>('input[placeholder*="Add a new task"]');
        taskInput?.focus();
      }
      // Escape to clear filters
      if (e.key === 'Escape' && (priorityFilter || tagFilter)) {
        handleClearFilters();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [priorityFilter, tagFilter]);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();

    // Clear previous errors
    setValidationErrors({});

    // Build recurrence object
    const recurrence = recurrenceType
      ? {
          recurrence_type: recurrenceType,
          cron_expression: recurrenceType === 'custom' ? cronExpression : null,
        }
      : null;

    // Validate form
    const errors = validateTaskForm({
      title: newTaskText,
      description: newTaskDescription,
      tags: newTaskTags,
      reminders,
      recurrence,
    });

    // Additional validation for custom recurrence
    if (recurrenceType === 'custom' && !cronExpression.trim()) {
      errors.cron_expression = 'Cron expression is required for custom recurrence';
    }

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    setIsCreating(true);

    // Build request payload
    const taskData: TaskCreateRequest = {
      title: newTaskText.trim(),
      description: newTaskDescription.trim() || null,
      priority: newTaskPriority,
      tags: newTaskTags,
      due_date: newTaskDueDate || null,
      reminders: reminders.length > 0 ? reminders : undefined,
      recurrence: recurrence || undefined,
    };

    try {
      const result = await createTask(taskData);
      if (result) {
        // Reset form
        setNewTaskText('');
        setNewTaskDescription('');
        setNewTaskDueDate('');
        setNewTaskPriority('medium');
        setNewTaskTags([]);
        setRecurrenceType(null);
        setCronExpression('');
        setReminders([]);
        setValidationErrors({});
        setShowAdvancedOptions(false);

        // Show success toast
        setToast({ message: 'Task created successfully!', type: 'success' });
      }
    } catch (error) {
      // Show error toast
      const errorMessage = error instanceof Error ? error.message : 'Failed to create task';
      setToast({ message: errorMessage, type: 'error' });
    } finally {
      setIsCreating(false);
    }
  };

  const handleEditTask = async (id: string, title: string) => {
    await updateTask(id, { title });
  };

  const handleEditTaskFull = async (id: string, data: { title?: string; description?: string }) => {
    await updateTask(id, {
      title: data.title,
      description: data.description || null,
    });
  };

  const pendingTasks = tasks.filter(t => t.status === 'pending');
  const completedTasks = tasks.filter(t => t.status === 'completed');

  return (
    <div className="min-h-[calc(100vh-8rem)] py-8">
      <Container className="max-w-3xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-dark-50">My Tasks</h1>
          <p className="text-dark-400 mt-2">
            Manage tasks created through your AI assistant
            <span className="ml-2 text-xs text-dark-500">
              (Tip: Press Ctrl+K to focus on task input)
            </span>
          </p>
        </div>

        {/* Add Task Form - Glass Panel */}
        <Card variant="glass" className="p-4 sm:p-6 mb-6">
          <form onSubmit={handleCreateTask} className="space-y-4" aria-label="Create new task">
            {/* Validation Errors */}
            {Object.keys(validationErrors).length > 0 && (
              <div className="p-3 glass-subtle border-error-500/30 rounded-lg">
                <p className="text-sm font-medium text-error-400 mb-1">Please fix the following errors:</p>
                <ul className="text-sm text-error-300 list-disc list-inside space-y-0.5">
                  {Object.entries(validationErrors).map(([field, error]) => (
                    <li key={field}>{error}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Title Input - Glass styled */}
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={newTaskText}
                onChange={(e) => setNewTaskText(e.target.value)}
                placeholder="Add a new task (task title)..."
                className={cn(
                  "input-glass flex-1",
                  validationErrors.title && 'border-error-500'
                )}
                disabled={isCreating}
                aria-label="Task title"
                aria-required="true"
                aria-invalid={!!validationErrors.title}
                aria-describedby={validationErrors.title ? 'title-error' : undefined}
              />
              <Button
                type="submit"
                disabled={isCreating || !newTaskText.trim()}
                isLoading={isCreating}
                className="w-full sm:w-auto"
              >
                Add Task
              </Button>
            </div>

            {/* Description Textarea - Glass styled */}
            <div>
              <label htmlFor="task-description" className="text-sm text-dark-300 font-medium mb-2 block">
                Description (optional):
              </label>
              <textarea
                id="task-description"
                value={newTaskDescription}
                onChange={(e) => setNewTaskDescription(e.target.value)}
                placeholder="Add more details about this task..."
                rows={3}
                maxLength={2000}
                className={cn(
                  "input-glass w-full resize-y",
                  validationErrors.description && 'border-error-500'
                )}
                disabled={isCreating}
              />
              <div className="flex justify-between items-center mt-1">
                <p className="text-xs text-dark-500">
                  Supports line breaks and special characters
                </p>
                <p className={cn(
                  "text-xs",
                  newTaskDescription.length > 1900
                    ? "text-warning-400 font-medium"
                    : newTaskDescription.length === 2000
                    ? "text-error-400 font-medium"
                    : "text-dark-500"
                )}>
                  {newTaskDescription.length}/2000
                </p>
              </div>
            </div>

            {/* Priority Selector - Glass buttons with gradient accent */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
              <label className="text-sm text-dark-300 font-medium">
                Priority:
              </label>
              <div className="flex gap-2 flex-wrap">
                {(['low', 'medium', 'high'] as TaskPriority[]).map((priority) => (
                  <button
                    key={priority}
                    type="button"
                    onClick={() => setNewTaskPriority(priority)}
                    disabled={isCreating}
                    className={cn(
                      'px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 border',
                      newTaskPriority === priority
                        ? priority === 'high'
                          ? 'bg-error-500 text-white border-error-500'
                          : priority === 'low'
                          ? 'bg-success-500 text-white border-success-500'
                          : 'bg-accent-gradient text-white border-primary-500'
                        : 'glass-subtle border-dark-600 text-dark-300 hover:border-dark-500',
                      isCreating && 'opacity-50 cursor-not-allowed'
                    )}
                  >
                    {priority.charAt(0).toUpperCase() + priority.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Tags Input */}
            <div>
              <label className="text-sm text-dark-300 font-medium mb-2 block">
                Tags (optional):
              </label>
              <TagInput
                tags={newTaskTags}
                onChange={setNewTaskTags}
                disabled={isCreating}
                error={validationErrors.tags}
              />
            </div>

            {/* Due Date and Time */}
            <DateTimePicker
              value={newTaskDueDate}
              onChange={(isoString) => setNewTaskDueDate(isoString || '')}
              label="Due date and time"
              disabled={isCreating}
              required={false}
              showTimezone={true}
            />

            {/* Advanced Options Toggle */}
            <div className="pt-3 border-t border-dark-600">
              <button
                type="button"
                onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                disabled={isCreating}
                className="flex items-center gap-2 text-sm text-dark-300 hover:text-primary-400 font-medium transition-colors"
              >
                <svg
                  className={cn(
                    'w-4 h-4 transition-transform',
                    showAdvancedOptions && 'rotate-90'
                  )}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                Advanced Options
                {(recurrenceType || reminders.length > 0) && (
                  <span className="px-2 py-0.5 text-xs bg-accent-gradient text-white rounded-full">
                    {[recurrenceType && 'Recurrence', reminders.length > 0 && `${reminders.length} reminder${reminders.length > 1 ? 's' : ''}`].filter(Boolean).join(', ')}
                  </span>
                )}
              </button>
            </div>

            {/* Advanced Options Section */}
            {showAdvancedOptions && (
              <div className="space-y-4 p-4 glass-subtle rounded-lg">
                {/* Recurrence Selector */}
                <RecurrenceSelector
                  recurrenceType={recurrenceType}
                  cronExpression={cronExpression}
                  onChange={(type, cron) => {
                    setRecurrenceType(type);
                    setCronExpression(cron);
                  }}
                  disabled={isCreating}
                  error={validationErrors.cron_expression}
                />

                {/* Reminder List */}
                <div className="pt-4 border-t border-dark-600">
                  <ReminderList
                    reminders={reminders}
                    onChange={setReminders}
                    disabled={isCreating}
                    error={validationErrors.reminders}
                    dueDate={newTaskDueDate}
                  />
                </div>
              </div>
            )}
          </form>
        </Card>

        {/* Filter Tabs and Sort Controls */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div className="flex gap-2" role="tablist" aria-label="Task status filter">
            {(['all', 'pending', 'completed'] as FilterStatus[]).map((status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                role="tab"
                aria-selected={filter === status}
                aria-label={`Show ${status} tasks`}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                  filter === status
                    ? 'bg-accent-gradient text-white shadow-glow'
                    : 'glass-subtle text-dark-300 hover:text-dark-100'
                )}
              >
                {status === 'all' ? 'All' : status === 'pending' ? 'Pending' : 'Completed'}
                {status === 'all' && total > 0 && (
                  <span className="ml-1.5 text-xs bg-dark-700 text-dark-200 px-1.5 py-0.5 rounded-full">
                    {total}
                  </span>
                )}
              </button>
            ))}
          </div>
          <SortControls
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSortByChange={setSortBy}
            onSortOrderChange={setSortOrder}
          />
        </div>

        {/* Filter Panel */}
        <div className="mb-6">
          <FilterPanel
            priorityFilter={priorityFilter}
            tagFilter={tagFilter}
            availableTags={availableTags}
            onPrioritySelect={setPriorityFilter}
            onTagSelect={setTagFilter}
            onClearFilters={handleClearFilters}
            activeFilterCount={activeFilterCount}
          />
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 glass-subtle border-error-500/30 rounded-lg">
            <p className="text-sm text-error-400">{error}</p>
            <button
              onClick={() => refresh()}
              className="mt-2 text-sm text-primary-400 hover:text-primary-300 font-medium"
            >
              Try again
            </button>
          </div>
        )}

        {/* Loading State - Glass skeletons */}
        {isLoading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 rounded-xl glass">
                <div className="flex items-start gap-4">
                  <Skeleton className="w-5 h-5 rounded-full bg-dark-600" />
                  <div className="flex-1">
                    <Skeleton className="h-5 w-3/4 mb-2 bg-dark-600" />
                    <Skeleton className="h-3 w-1/2 mb-2 bg-dark-700" />
                    <Skeleton className="h-3 w-1/4 bg-dark-700" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && tasks.length === 0 && (
          <Card variant="glass" className="p-12 text-center">
            <div className="w-16 h-16 bg-dark-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-dark-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-dark-50 mb-2">No tasks yet</h3>
            <p className="text-dark-400 mb-4">
              {filter === 'all'
                ? 'Ask your AI assistant to create tasks, or add one manually above.'
                : filter === 'pending'
                ? 'No pending tasks. Great job!'
                : 'No completed tasks yet.'}
            </p>
          </Card>
        )}

        {/* Tasks List */}
        {!isLoading && tasks.length > 0 && (
          <div className="space-y-6">
            {/* Pending Tasks */}
            {filter !== 'completed' && pendingTasks.length > 0 && (
              <div>
                {filter === 'all' && (
                  <h2 className="text-sm font-semibold text-dark-400 uppercase tracking-wide mb-3">
                    Pending ({pendingTasks.length})
                  </h2>
                )}
                <div className="space-y-3">
                  {pendingTasks.map((task) => (
                    <TaskItem
                      key={task.id}
                      task={task}
                      onComplete={completeTask}
                      onUncomplete={uncompleteTask}
                      onDelete={deleteTask}
                      onEdit={handleEditTask}
                      onEditFull={handleEditTaskFull}
                      isUpdating={isUpdating === task.id}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Completed Tasks */}
            {filter !== 'pending' && completedTasks.length > 0 && (
              <div>
                {filter === 'all' && (
                  <h2 className="text-sm font-semibold text-dark-400 uppercase tracking-wide mb-3">
                    Completed ({completedTasks.length})
                  </h2>
                )}
                <div className="space-y-3">
                  {completedTasks.map((task) => (
                    <TaskItem
                      key={task.id}
                      task={task}
                      onComplete={completeTask}
                      onUncomplete={uncompleteTask}
                      onDelete={deleteTask}
                      onEdit={handleEditTask}
                      onEditFull={handleEditTaskFull}
                      isUpdating={isUpdating === task.id}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Toast Notifications */}
        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
            duration={3000}
          />
        )}
      </Container>
    </div>
  );
}

export default function TasksPage() {
  return (
    <ProtectedRoute>
      <Suspense fallback={
        <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-400" />
        </div>
      }>
        <TasksContent />
      </Suspense>
    </ProtectedRoute>
  );
}
