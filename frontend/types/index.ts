/**
 * Frontend TypeScript Types
 * Generated from specs/006-frontend-chat-ui/data-model.md
 */

// ============================================================================
// Authentication Types
// ============================================================================

/**
 * Authenticated user session stored in localStorage.
 * Updated: 007-jwt-authentication - Includes JWT access token
 */
export interface UserSession {
  userId: string;
  email: string;
  displayName: string;
  createdAt: string;
  accessToken: string;  // JWT access token for API requests
}

export interface AuthState {
  user: UserSession | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export interface SignupRequest {
  email: string;
  password: string;
  display_name: string;
}

export interface SigninRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  user_id: string;
  email: string;
  display_name: string;
  created_at: string;
  access_token: string;  // JWT access token
  token_type: string;    // Always "bearer"
}

// ============================================================================
// Task Types
// ============================================================================

export type TaskStatus = 'pending' | 'completed';

export interface Task {
  id: string;
  description: string;
  status: TaskStatus;
  due_date: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
}

export interface TaskCreateRequest {
  description: string;
  due_date?: string | null;
}

export interface TaskUpdateRequest {
  description?: string;
  status?: TaskStatus;
  due_date?: string | null;
}

// ============================================================================
// Chat Entity Types
// ============================================================================

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  updatedAt: string;
  messageCount: number;
}

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
}

export interface ChatMessage extends Message {
  isPending?: boolean;
  hasError?: boolean;
  errorMessage?: string;
}

// ============================================================================
// Observability Entity Types
// ============================================================================

// API Response types (snake_case to match backend)
export interface DecisionLogResponse {
  decision_id: string;
  conversation_id: string;
  user_id: string;
  message: string;
  intent_type: string;
  confidence: number | null;
  decision_type: string;
  outcome_category: string;
  response_text: string | null;
  created_at: string;
  duration_ms: number;
}

export interface ToolInvocationLogResponse {
  tool_name: string;
  parameters: Record<string, unknown>;
  result: Record<string, unknown> | null;
  success: boolean;
  error_code: string | null;
  error_message: string | null;
  duration_ms: number;
  invoked_at: string;
  sequence: number;
}

// Frontend types (camelCase for UI components)
export interface DecisionLog {
  decisionId: string;
  conversationId: string;
  userId: string;
  message: string;
  intentType: string;
  confidence: number | null;
  decisionType: string;
  outcomeCategory: string;
  responseText: string | null;
  createdAt: string;
  durationMs: number;
}

export interface ToolInvocationLog {
  toolName: string;
  parameters: Record<string, unknown>;
  result: Record<string, unknown> | null;
  success: boolean;
  errorCode: string | null;
  errorMessage: string | null;
  durationMs: number;
  invokedAt: string;
  sequence: number;
}

export interface DecisionTrace {
  decision: DecisionLog;
  toolInvocations: ToolInvocationLog[];
}

export interface MetricsSummary {
  totalDecisions: number;
  successRate: number;
  errorBreakdown: Record<string, number>;
  avgDecisionDurationMs: number;
  avgToolDurationMs: number;
  intentDistribution: Record<string, number>;
  toolUsage: Record<string, number>;
}

export interface QueryResult<T> {
  items: T[];
  total: number;
  hasMore: boolean;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

export interface SendMessageRequest {
  conversation_id?: string | null;
  content: string;
}

export interface SendMessageResponse {
  conversation_id: string;
  message: Message;
  messages: Message[];
}

export interface ConversationListResponse {
  conversations: ConversationSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ConversationDetailResponse {
  conversation: Conversation;
  messages: Message[];
}

export interface DecisionQueryParams {
  conversationId?: string;
  userId?: string;
  startTime?: string;
  endTime?: string;
  decisionType?: string;
  outcomeCategory?: string;
  limit?: number;
  offset?: number;
}

export interface MetricsQueryParams {
  startTime: string;
  endTime?: string;
  userId?: string;
}

export interface DecisionQueryResponse {
  items: DecisionLogResponse[];
  total: number;
  has_more: boolean;
}

export interface DecisionTraceResponse {
  decision: DecisionLogResponse;
  tool_invocations: ToolInvocationLogResponse[];
}

export interface MetricsSummaryResponse {
  total_decisions: number;
  success_rate: number;
  error_breakdown: Record<string, number>;
  avg_decision_duration_ms: number;
  avg_tool_duration_ms: number;
  intent_distribution: Record<string, number>;
  tool_usage: Record<string, number>;
}

// ============================================================================
// Error Types
// ============================================================================

export type ErrorCode =
  | 'INVALID_ID_FORMAT'
  | 'CONVERSATION_NOT_FOUND'
  | 'ACCESS_DENIED'
  | 'VALIDATION_ERROR'
  | 'SERVICE_UNAVAILABLE'
  | 'DECISION_NOT_FOUND'
  | 'NETWORK_ERROR'
  | 'TIMEOUT'
  | 'UNKNOWN'
  // Authentication error codes
  | 'INVALID_CREDENTIALS'
  | 'EMAIL_EXISTS'
  | 'MISSING_TOKEN'
  | 'INVALID_TOKEN'
  | 'TOKEN_EXPIRED'
  | 'PASSWORD_TOO_LONG';

export interface ApiError {
  error: {
    code: ErrorCode;
    message: string;
  };
}

export interface ErrorState {
  code: ErrorCode;
  message: string;
  isRetryable: boolean;
}

// ============================================================================
// UI State Types
// ============================================================================

export interface ChatPageState {
  activeConversationId: string | null;
  inputValue: string;
  isSending: boolean;
  isLoadingHistory: boolean;
  error: ErrorState | null;
}

export interface DashboardPageState {
  timeRange: 'hour' | 'day' | 'week' | 'month';
  isLoading: boolean;
  error: ErrorState | null;
}

export interface TraceViewerState {
  selectedConversationId: string | null;
  expandedDecisionId: string | null;
  isLoading: boolean;
  error: ErrorState | null;
}
