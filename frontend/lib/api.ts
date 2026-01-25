/**
 * API Client for backend communication
 * Feature: 006-frontend-chat-ui
 * Updated: 007-jwt-authentication - Uses JWT Bearer tokens
 */

import type {
  SendMessageRequest,
  SendMessageResponse,
  ConversationListResponse,
  ConversationDetailResponse,
  DecisionQueryParams,
  DecisionQueryResponse,
  DecisionTraceResponse,
  MetricsQueryParams,
  MetricsSummaryResponse,
  ErrorCode,
  SignupRequest,
  SigninRequest,
  AuthResponse,
  TaskListResponse,
  Task,
  TaskStatus,
  TaskCreateRequest,
  TaskUpdateRequest,
  TaskQueryParams,
} from '@/types';
import { buildTaskQueryString } from './utils';

// In production (static export), use empty string to make requests relative to current origin
// This allows nginx to proxy /api/* requests to the backend
// In development, use NEXT_PUBLIC_API_URL or default to localhost
const API_BASE_URL = typeof window !== 'undefined' && process.env.NODE_ENV === 'production'
  ? ''  // Use relative URLs in production (nginx proxy)
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

export class ApiClientError extends Error {
  constructor(
    public status: number,
    public code: ErrorCode,
    message: string
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Set the JWT access token for authenticated requests
   */
  setAccessToken(token: string | null) {
    this.accessToken = token;
  }

  /**
   * Get the current access token
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Build headers for API requests
   */
  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    return headers;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = this.baseUrl + path;
    const headers = this.getHeaders();

    const controller = new AbortController();
    const timeout = path.includes('/chat') ? 30000 : 10000;
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData: { error?: { code?: string; message?: string } } = {};
        try {
          errorData = await response.json();
        } catch {
          // Response not JSON
        }

        const code = (errorData.error?.code as ErrorCode) || 'UNKNOWN';
        const message = errorData.error?.message || 'HTTP ' + response.status;
        throw new ApiClientError(response.status, code, message);
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof ApiClientError) {
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new ApiClientError(0, 'TIMEOUT', 'Request timed out');
        }
        throw new ApiClientError(0, 'NETWORK_ERROR', error.message);
      }

      throw new ApiClientError(0, 'UNKNOWN', 'Unknown error occurred');
    }
  }

  // Chat endpoints
  async sendMessage(request: SendMessageRequest): Promise<SendMessageResponse> {
    return this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Conversation endpoints
  async listConversations(
    limit = 20,
    offset = 0
  ): Promise<ConversationListResponse> {
    return this.request('/api/conversations?limit=' + limit + '&offset=' + offset);
  }

  async getConversation(id: string): Promise<ConversationDetailResponse> {
    return this.request('/api/conversations/' + id);
  }

  // Observability endpoints
  async queryDecisions(
    params: DecisionQueryParams
  ): Promise<DecisionQueryResponse> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        // Convert camelCase to snake_case for API
        const snakeKey = key.replace(/[A-Z]/g, (m) => '_' + m.toLowerCase());
        searchParams.set(snakeKey, String(value));
      }
    });
    return this.request('/api/observability/decisions?' + searchParams);
  }

  async getDecisionTrace(id: string): Promise<DecisionTraceResponse> {
    return this.request('/api/observability/decisions/' + id + '/trace');
  }

  async getMetrics(params: MetricsQueryParams): Promise<MetricsSummaryResponse> {
    const searchParams = new URLSearchParams();
    searchParams.set('start_time', params.startTime);
    if (params.endTime) searchParams.set('end_time', params.endTime);
    if (params.userId) searchParams.set('user_id', params.userId);
    return this.request('/api/observability/metrics?' + searchParams);
  }

  // Auth endpoints (no auth header needed)
  async signup(request: SignupRequest): Promise<AuthResponse> {
    return this.request('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async signin(request: SigninRequest): Promise<AuthResponse> {
    return this.request('/api/auth/signin', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Task endpoints
  async listTasks(queryParams?: TaskQueryParams): Promise<TaskListResponse> {
    const queryString = queryParams ? buildTaskQueryString(queryParams) : '';
    const params = queryString ? '?' + queryString : '';
    return this.request('/api/tasks' + params);
  }

  async createTask(data: TaskCreateRequest): Promise<Task> {
    return this.request('/api/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getTask(id: string): Promise<Task> {
    return this.request('/api/tasks/' + id);
  }

  async updateTask(id: string, data: TaskUpdateRequest): Promise<Task> {
    return this.request('/api/tasks/' + id, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async completeTask(id: string): Promise<Task> {
    return this.request('/api/tasks/' + id + '/complete', {
      method: 'POST',
    });
  }

  async deleteTask(id: string): Promise<void> {
    await this.request('/api/tasks/' + id, {
      method: 'DELETE',
    });
  }
}

// Singleton instance
export const apiClient = new ApiClient();

export default apiClient;
