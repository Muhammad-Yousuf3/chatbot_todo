# Feature Specification: MCP Task Tools for AI-Controlled Todo Management

**Feature Branch**: `002-mcp-task-tools`
**Created**: 2026-01-03
**Status**: Draft
**Input**: User description: "Define MCP tools that allow AI agents to safely create, read, update, complete, and delete todo tasks without direct database access"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Agent Creates a Task (Priority: P1)

An AI agent, responding to a user's natural language request like "remind me to buy groceries", invokes the `add_task` MCP tool to create a new task owned by the authenticated user. The tool persists the task and returns confirmation with the task identifier.

**Why this priority**: Task creation is the foundational capability. Without the ability to add tasks via MCP tools, no other task management functionality can work. This enables the most basic AI-driven todo interaction.

**Independent Test**: Can be fully tested by invoking `add_task` with valid parameters and verifying a task is created in the database with correct ownership.

**Acceptance Scenarios**:

1. **Given** a valid user context and task description "Buy groceries", **When** the AI agent invokes `add_task`, **Then** a new task is created with the description and the user as owner, and the tool returns the task ID.
2. **Given** a user context, **When** `add_task` is invoked with an empty description, **Then** the tool returns a validation error indicating description is required.
3. **Given** multiple AI agents operating for different users concurrently, **When** each invokes `add_task`, **Then** each task is correctly scoped to its respective user with no data mixing.

---

### User Story 2 - AI Agent Lists User Tasks (Priority: P1)

An AI agent needs to understand what tasks exist for a user to provide context-aware responses. The agent invokes `list_tasks` to retrieve all tasks belonging to the authenticated user, enabling responses like "You have 3 pending tasks."

**Why this priority**: Equally critical as P1 - without listing, the AI cannot provide context about existing tasks. This enables informed, multi-turn task conversations.

**Independent Test**: Can be tested by creating tasks (via US1), then invoking `list_tasks` and verifying all user's tasks are returned.

**Acceptance Scenarios**:

1. **Given** a user with 5 tasks (3 pending, 2 completed), **When** the AI agent invokes `list_tasks`, **Then** all 5 tasks are returned with their status.
2. **Given** a user with no tasks, **When** `list_tasks` is invoked, **Then** an empty list is returned (not an error).
3. **Given** User A has 3 tasks and User B has 2 tasks, **When** AI agent for User A invokes `list_tasks`, **Then** only User A's 3 tasks are returned.

---

### User Story 3 - AI Agent Updates a Task (Priority: P2)

A user says "change my grocery task to include milk". The AI agent invokes `update_task` to modify the task description. Only the task owner's tasks can be updated.

**Why this priority**: Modifying tasks is important for task management but depends on US1 and US2 being functional first. Enables task refinement.

**Independent Test**: Can be tested by creating a task, invoking `update_task` with a new description, and verifying the change persisted.

**Acceptance Scenarios**:

1. **Given** a task with ID "task-123" and description "Buy groceries", **When** `update_task` is invoked with new description "Buy groceries and milk", **Then** the task description is updated and success is returned.
2. **Given** a task ID that does not exist, **When** `update_task` is invoked, **Then** a "not found" error is returned.
3. **Given** User A's task, **When** User B's AI agent attempts to update it, **Then** an "access denied" error is returned (ownership enforced).

---

### User Story 4 - AI Agent Completes a Task (Priority: P2)

A user says "I finished buying groceries". The AI agent invokes `complete_task` to mark the task as done. This is a distinct action from general updates to support explicit completion semantics.

**Why this priority**: Task completion is a core workflow but separate from creation/listing. Enables tracking of accomplished work.

**Independent Test**: Can be tested by creating a pending task, invoking `complete_task`, and verifying status changed to completed.

**Acceptance Scenarios**:

1. **Given** a pending task with ID "task-123", **When** `complete_task` is invoked, **Then** the task status changes to "completed" and completion timestamp is recorded.
2. **Given** an already completed task, **When** `complete_task` is invoked again, **Then** the operation succeeds idempotently (no error, no duplicate completion).
3. **Given** a non-existent task ID, **When** `complete_task` is invoked, **Then** a "not found" error is returned.

---

### User Story 5 - AI Agent Deletes a Task (Priority: P3)

A user says "remove the groceries task, I don't need it anymore". The AI agent invokes `delete_task` to permanently remove the task from the system.

**Why this priority**: Deletion is less frequently used than other operations. Can be deferred after core CRUD works.

**Independent Test**: Can be tested by creating a task, invoking `delete_task`, then verifying the task no longer exists in `list_tasks`.

**Acceptance Scenarios**:

1. **Given** a task with ID "task-123", **When** `delete_task` is invoked, **Then** the task is permanently removed and success is returned.
2. **Given** a task ID that does not exist, **When** `delete_task` is invoked, **Then** the operation succeeds idempotently (no error for missing task).
3. **Given** User A's task, **When** User B's AI agent attempts to delete it, **Then** an "access denied" error is returned.

---

### Edge Cases

- What happens when a task description exceeds maximum length?
  - Tool returns a validation error indicating the maximum allowed length.
- What happens when the database is temporarily unavailable?
  - Tool returns an error; no partial data is persisted. AI agent receives clear failure signal.
- What happens when user identity is missing or invalid?
  - Tool returns an authentication error; no operation is performed.
- What happens when concurrent operations target the same task?
  - Last write wins for updates; deletes are idempotent; no data corruption occurs.
- What happens when a tool is invoked with malformed parameters?
  - Tool returns a validation error with specific details about the malformed input.
- What happens when an AI agent attempts to bypass tools and access the database directly?
  - Not possible by design; AI agents have no database credentials and can only invoke MCP tools.

## Requirements *(mandatory)*

### Functional Requirements

**Tool Definitions**:

- **FR-001**: System MUST provide an `add_task` MCP tool that creates a new task for the authenticated user.
- **FR-002**: System MUST provide a `list_tasks` MCP tool that returns all tasks belonging to the authenticated user.
- **FR-003**: System MUST provide an `update_task` MCP tool that modifies a task's description for tasks owned by the authenticated user.
- **FR-004**: System MUST provide a `complete_task` MCP tool that marks a task as completed for tasks owned by the authenticated user.
- **FR-005**: System MUST provide a `delete_task` MCP tool that permanently removes a task owned by the authenticated user.

**Tool Contracts**:

- **FR-006**: Each MCP tool MUST accept user identity as an input parameter (externally provided, not self-determined by AI).
- **FR-007**: Each MCP tool MUST return a structured response indicating success or failure with appropriate details.
- **FR-008**: Each MCP tool MUST validate all input parameters before performing any database operation.
- **FR-009**: Each MCP tool MUST enforce ownership - tools can only operate on tasks belonging to the provided user.

**Tool Behavior**:

- **FR-010**: `add_task` MUST create a task with status "pending" and current timestamp.
- **FR-011**: `list_tasks` MUST return tasks sorted by creation date (newest first) by default.
- **FR-012**: `update_task` MUST only modify the description field; status changes require `complete_task`.
- **FR-013**: `complete_task` MUST be idempotent - completing an already completed task returns success.
- **FR-014**: `delete_task` MUST be idempotent - deleting a non-existent task returns success.
- **FR-015**: All tools MUST be stateless - no tool invocation depends on prior invocations.

**Data Integrity**:

- **FR-016**: MCP tools are the ONLY layer permitted to read/write the tasks table.
- **FR-017**: System MUST persist task changes to the database before returning success to the caller.
- **FR-018**: System MUST reject operations with invalid or missing required parameters.
- **FR-019**: System MUST enforce maximum task description length of 1,000 characters.

**Auditability**:

- **FR-020**: Each tool invocation MUST be independently traceable (tool name, inputs, outputs, timestamp).

### Key Entities

- **Task**: Represents a single todo item owned by a user. Key attributes include: unique identifier (UUID), owner (user ID reference), description (text), status (pending/completed), creation timestamp, completion timestamp (nullable).

- **User Reference**: External entity (from Better Auth). Tasks reference the user but do not define user attributes. User ID is used as foreign key for ownership.

### Assumptions

- User authentication is handled externally by Better Auth; MCP tools receive authenticated user context as input.
- AI agents cannot directly access the database; they can only invoke MCP tools via the official MCP SDK.
- Task descriptions are plain text only; rich formatting or attachments are out of scope.
- Task ordering, prioritization, due dates, and reminders are out of scope for this specification.
- Soft delete is not required; tasks are permanently removed via `delete_task`.
- Batch operations (bulk create, bulk delete) are out of scope.
- Maximum task description length: 1,000 characters.
- No limit on tasks per user for this specification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AI agents can create, list, update, complete, and delete tasks using only MCP tools (100% tool-mediated).
- **SC-002**: No task data leakage across users - each user only sees/modifies their own tasks (100% ownership enforcement).
- **SC-003**: Tool responses return within 500ms for typical operations (single task CRUD).
- **SC-004**: Idempotent operations (`complete_task`, `delete_task`) produce consistent results regardless of initial state.
- **SC-005**: Tools reject 100% of invalid inputs with clear, actionable error messages.
- **SC-006**: System maintains data integrity - no orphaned tasks, no duplicate IDs, no inconsistent states.
- **SC-007**: Each tool invocation is independently auditable - tool name, user, inputs, and result are traceable.
