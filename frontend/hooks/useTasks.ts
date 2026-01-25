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
import { buildTaskQueryString } from '@/lib/utils';
import type { Task, TaskQueryParams, TaskCreateRequest, TaskUpdateRequest, TaskListResponse } from '@/types';

const TASKS_KEY = '/api/tasks';

export function useTasks(queryParams?: TaskQueryParams) {
  const [isUpdating, setIsUpdating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Generate cache key from query params
  const queryString = queryParams ? buildTaskQueryString(queryParams) : '';
  const cacheKey = queryString ? `${TASKS_KEY}?${queryString}` : TASKS_KEY;

  const { data, error: fetchError, isLoading, mutate } = useSWR<TaskListResponse>(
    cacheKey,
    () => apiClient.listTasks(queryParams),
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  );

  const createTask = useCallback(async (data: TaskCreateRequest): Promise<Task | null> => {
    setError(null);
    try {
      const newTask = await apiClient.createTask(data);
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

  const updateTask = useCallback(async (id: string, data: TaskUpdateRequest): Promise<boolean> => {
    setError(null);
    setIsUpdating(id);
    try {
      await apiClient.updateTask(id, data);
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
