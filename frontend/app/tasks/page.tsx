'use client';

/**
 * Tasks Page - View and Manage Tasks
 * Feature: 006-frontend-chat-ui
 *
 * Displays all tasks created by the chatbot with options to
 * complete, uncomplete, edit, and delete tasks.
 * Supports due dates for task scheduling.
 */

import React, { useState, Suspense } from 'react';
import { Container } from '@/components/layout/Container';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useTasks } from '@/hooks/useTasks';
import type { Task, TaskStatus } from '@/types';
import { cn, formatDate } from '@/lib/utils';

type FilterStatus = 'all' | TaskStatus;

function formatDueDate(dateStr: string | null): string | null {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dueDay = new Date(date);
  dueDay.setHours(0, 0, 0, 0);

  const diffDays = Math.ceil((dueDay.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return `Overdue by ${Math.abs(diffDays)} day${Math.abs(diffDays) !== 1 ? 's' : ''}`;
  } else if (diffDays === 0) {
    return 'Due today';
  } else if (diffDays === 1) {
    return 'Due tomorrow';
  } else if (diffDays <= 7) {
    return `Due in ${diffDays} days`;
  } else {
    return `Due ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
  }
}

function getDueDateStyle(dateStr: string | null, isCompleted: boolean): string {
  if (!dateStr || isCompleted) return 'text-slate-400 dark:text-slate-500';
  const date = new Date(dateStr);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dueDay = new Date(date);
  dueDay.setHours(0, 0, 0, 0);

  const diffDays = Math.ceil((dueDay.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return 'text-error-500 dark:text-error-400 font-medium';
  } else if (diffDays <= 1) {
    return 'text-warning-500 dark:text-warning-400 font-medium';
  }
  return 'text-slate-400 dark:text-slate-500';
}

function TaskItem({
  task,
  onComplete,
  onUncomplete,
  onDelete,
  onEdit,
  isUpdating
}: {
  task: Task;
  onComplete: (id: string) => void;
  onUncomplete: (id: string) => void;
  onDelete: (id: string) => void;
  onEdit: (id: string, description: string) => void;
  isUpdating: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(task.description);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleSaveEdit = () => {
    if (editValue.trim() && editValue !== task.description) {
      onEdit(task.id, editValue.trim());
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditValue(task.description);
    setIsEditing(false);
  };

  const handleDelete = () => {
    onDelete(task.id);
    setShowDeleteConfirm(false);
  };

  const isCompleted = task.status === 'completed';
  const dueDateText = formatDueDate(task.due_date);
  const dueDateStyle = getDueDateStyle(task.due_date, isCompleted);

  return (
    <div className={cn(
      'group p-4 rounded-xl border transition-all duration-200',
      isCompleted
        ? 'bg-slate-50 dark:bg-dark-800/50 border-slate-200 dark:border-dark-700'
        : 'bg-white dark:bg-dark-800 border-slate-200 dark:border-dark-700 hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-sm'
    )}>
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        <button
          onClick={() => isCompleted ? onUncomplete(task.id) : onComplete(task.id)}
          disabled={isUpdating}
          className={cn(
            'mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all flex-shrink-0',
            isCompleted
              ? 'bg-success-500 border-success-500 text-white'
              : 'border-slate-300 hover:border-primary-500',
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
            <div className="flex flex-col gap-2">
              <input
                type="text"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 dark:border-dark-600 rounded-lg text-slate-800 dark:text-white dark:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveEdit();
                  if (e.key === 'Escape') handleCancelEdit();
                }}
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={handleSaveEdit}>Save</Button>
                <Button size="sm" variant="ghost" onClick={handleCancelEdit}>Cancel</Button>
              </div>
            </div>
          ) : (
            <>
              <p className={cn(
                'text-slate-800 dark:text-slate-200 break-words',
                isCompleted && 'line-through text-slate-500 dark:text-slate-500'
              )}>
                {task.description}
              </p>
              <div className="flex flex-wrap items-center gap-2 mt-1">
                <p className="text-xs text-slate-400 dark:text-slate-500">
                  Created {formatDate(task.created_at)}
                  {task.completed_at && ` • Completed ${formatDate(task.completed_at)}`}
                </p>
                {dueDateText && (
                  <>
                    <span className="text-xs text-slate-300 dark:text-slate-600">•</span>
                    <p className={cn('text-xs flex items-center gap-1', dueDateStyle)}>
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      {dueDateText}
                    </p>
                  </>
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
                className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-dark-600 rounded-lg transition-colors"
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
                  className="px-2 py-1 text-xs text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-dark-600 rounded transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                disabled={isUpdating}
                className="p-1.5 text-slate-400 hover:text-error-500 hover:bg-error-50 dark:hover:bg-error-900/20 rounded-lg transition-colors"
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
    </div>
  );
}

function TasksContent() {
  const [filter, setFilter] = useState<FilterStatus>('all');
  const [newTaskText, setNewTaskText] = useState('');
  const [newTaskDueDate, setNewTaskDueDate] = useState('');
  const [isCreating, setIsCreating] = useState(false);

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
  } = useTasks(statusFilter);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskText.trim()) return;

    setIsCreating(true);
    const dueDate = newTaskDueDate ? newTaskDueDate : null;
    const result = await createTask(newTaskText.trim(), dueDate);
    if (result) {
      setNewTaskText('');
      setNewTaskDueDate('');
    }
    setIsCreating(false);
  };

  const pendingTasks = tasks.filter(t => t.status === 'pending');
  const completedTasks = tasks.filter(t => t.status === 'completed');

  return (
    <div className="min-h-[calc(100vh-8rem)] py-8">
      <Container className="max-w-3xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">My Tasks</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">
            Manage tasks created through your AI assistant
          </p>
        </div>

        {/* Add Task Form */}
        <Card className="p-4 mb-6">
          <form onSubmit={handleCreateTask} className="space-y-3">
            <div className="flex gap-3">
              <input
                type="text"
                value={newTaskText}
                onChange={(e) => setNewTaskText(e.target.value)}
                placeholder="Add a new task..."
                className="flex-1 px-4 py-2.5 border border-slate-300 dark:border-dark-600 rounded-lg text-slate-800 dark:text-white dark:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-slate-400 dark:placeholder:text-slate-500"
                disabled={isCreating}
              />
              <Button type="submit" disabled={isCreating || !newTaskText.trim()} isLoading={isCreating}>
                Add Task
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="due-date" className="text-sm text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Due date (optional):
              </label>
              <input
                id="due-date"
                type="date"
                value={newTaskDueDate}
                onChange={(e) => setNewTaskDueDate(e.target.value)}
                className="px-3 py-1.5 border border-slate-300 dark:border-dark-600 rounded-lg text-sm text-slate-800 dark:text-white dark:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                disabled={isCreating}
              />
              {newTaskDueDate && (
                <button
                  type="button"
                  onClick={() => setNewTaskDueDate('')}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                  aria-label="Clear due date"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </form>
        </Card>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {(['all', 'pending', 'completed'] as FilterStatus[]).map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={cn(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                filter === status
                  ? 'bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-700'
              )}
            >
              {status === 'all' ? 'All' : status === 'pending' ? 'Pending' : 'Completed'}
              {status === 'all' && total > 0 && (
                <span className="ml-1.5 text-xs bg-slate-200 dark:bg-dark-600 text-slate-600 dark:text-slate-300 px-1.5 py-0.5 rounded-full">
                  {total}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-error-50 border border-error-200 rounded-lg">
            <p className="text-sm text-error-700">{error}</p>
            <button
              onClick={() => refresh()}
              className="mt-2 text-sm text-error-600 hover:text-error-700 font-medium"
            >
              Try again
            </button>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 rounded-xl border border-slate-200 bg-white">
                <div className="flex items-start gap-3">
                  <Skeleton className="w-5 h-5 rounded-full" />
                  <div className="flex-1">
                    <Skeleton className="h-5 w-3/4 mb-2" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tasks List */}
        {!isLoading && tasks.length === 0 && (
          <Card className="p-12 text-center">
            <div className="w-16 h-16 bg-slate-100 dark:bg-dark-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-slate-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">No tasks yet</h3>
            <p className="text-slate-600 dark:text-slate-400 mb-4">
              {filter === 'all'
                ? 'Ask your AI assistant to create tasks, or add one manually above.'
                : filter === 'pending'
                ? 'No pending tasks. Great job!'
                : 'No completed tasks yet.'}
            </p>
          </Card>
        )}

        {!isLoading && tasks.length > 0 && (
          <div className="space-y-6">
            {/* Pending Tasks */}
            {filter !== 'completed' && pendingTasks.length > 0 && (
              <div>
                {filter === 'all' && (
                  <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
                    Pending ({pendingTasks.length})
                  </h2>
                )}
                <div className="space-y-2">
                  {pendingTasks.map((task) => (
                    <TaskItem
                      key={task.id}
                      task={task}
                      onComplete={completeTask}
                      onUncomplete={uncompleteTask}
                      onDelete={deleteTask}
                      onEdit={updateTask}
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
                  <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
                    Completed ({completedTasks.length})
                  </h2>
                )}
                <div className="space-y-2">
                  {completedTasks.map((task) => (
                    <TaskItem
                      key={task.id}
                      task={task}
                      onComplete={completeTask}
                      onUncomplete={uncompleteTask}
                      onDelete={deleteTask}
                      onEdit={updateTask}
                      isUpdating={isUpdating === task.id}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      }>
        <TasksContent />
      </Suspense>
    </ProtectedRoute>
  );
}
