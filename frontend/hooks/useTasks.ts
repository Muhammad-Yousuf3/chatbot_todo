'use client';

/**
 * useTasks Hook - Task Management
 * Feature: 006-frontend-chat-ui
 *
 * Provides task CRUD operations with SWR caching.
 */

import useSWR from 'swr';
import { useState, useCallback } from 'react';
import { apiClient, ApiClientError } from '@/lib/api';
import type { Task, TaskStatus, TaskListResponse } from '@/types';

const TASKS_KEY = '/api/tasks';

export function useTasks(statusFilter?: TaskStatus) {
  const [isUpdating, setIsUpdating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data, error: fetchError, isLoading, mutate } = useSWR<TaskListResponse>(
    statusFilter ? `${TASKS_KEY}?status=${statusFilter}` : TASKS_KEY,
    () => apiClient.listTasks(statusFilter),
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  );

  const createTask = useCallback(async (description: string, dueDate?: string | null): Promise<Task | null> => {
    setError(null);
    try {
      const newTask = await apiClient.createTask(description, dueDate);
      await mutate();
      return newTask;
    } catch (err) {
      const message = err instanceof ApiClientError ? err.message : 'Failed to create task';
      setError(message);
      return null;
    }
  }, [mutate]);

  const completeTask = useCallback(async (id: string): Promise<boolean> => {
    setError(null);
    setIsUpdating(id);
    try {
      await apiClient.completeTask(id);
      await mutate();
      return true;
    } catch (err) {
      const message = err instanceof ApiClientError ? err.message : 'Failed to complete task';
      setError(message);
      return false;
    } finally {
      setIsUpdating(null);
    }
  }, [mutate]);

  const uncompleteTask = useCallback(async (id: string): Promise<boolean> => {
    setError(null);
    setIsUpdating(id);
    try {
      await apiClient.updateTask(id, { status: 'pending' });
      await mutate();
      return true;
    } catch (err) {
      const message = err instanceof ApiClientError ? err.message : 'Failed to update task';
      setError(message);
      return false;
    } finally {
      setIsUpdating(null);
    }
  }, [mutate]);

  const deleteTask = useCallback(async (id: string): Promise<boolean> => {
    setError(null);
    setIsUpdating(id);
    try {
      await apiClient.deleteTask(id);
      await mutate();
      return true;
    } catch (err) {
      const message = err instanceof ApiClientError ? err.message : 'Failed to delete task';
      setError(message);
      return false;
    } finally {
      setIsUpdating(null);
    }
  }, [mutate]);

  const updateTask = useCallback(async (id: string, description: string): Promise<boolean> => {
    setError(null);
    setIsUpdating(id);
    try {
      await apiClient.updateTask(id, { description });
      await mutate();
      return true;
    } catch (err) {
      const message = err instanceof ApiClientError ? err.message : 'Failed to update task';
      setError(message);
      return false;
    } finally {
      setIsUpdating(null);
    }
  }, [mutate]);

  return {
    tasks: data?.tasks ?? [],
    total: data?.total ?? 0,
    isLoading,
    isUpdating,
    error: error || (fetchError instanceof Error ? fetchError.message : null),
    createTask,
    completeTask,
    uncompleteTask,
    deleteTask,
    updateTask,
    refresh: mutate,
  };
}

export default useTasks;
