# Data Model: Agent Behavior & Tool Invocation Policy

**Feature Branch**: `003-agent-behavior-policy`
**Date**: 2026-01-03
**Source**: spec.md Key Entities + research.md decisions

## Overview

This data model defines the entities required for deterministic agent behavior and tool invocation tracking. The agent itself is stateless; these models capture the decision context and audit trail.

---

## Entities

### 1. UserIntent

Represents the classified purpose of a user message.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| intent_type | Enum | Required | Classified intent category |
| confidence | Float | 0.0-1.0, Optional | Classification confidence (if available) |
| extracted_params | Dict | Optional | Parameters extracted from message |

**Intent Types (Enum)**:
```
CREATE_TASK      - User wants to create a new task
LIST_TASKS       - User wants to see their tasks
COMPLETE_TASK    - User wants to mark a task as done
UPDATE_TASK      - User wants to modify a task
DELETE_TASK      - User wants to remove a task
GENERAL_CHAT     - Non-task conversation
AMBIGUOUS        - Intent cannot be determined
CONFIRM_YES      - User confirms a pending action
CONFIRM_NO       - User denies a pending action
```

**Extracted Parameters by Intent**:

| Intent | Parameters |
|--------|------------|
| CREATE_TASK | `description: str` |
| LIST_TASKS | None |
| COMPLETE_TASK | `task_reference: str` (description fragment or position) |
| UPDATE_TASK | `task_reference: str`, `new_description: str` |
| DELETE_TASK | `task_reference: str` |
| GENERAL_CHAT | None |
| AMBIGUOUS | `possible_intents: List[str]` |
| CONFIRM_YES | None |
| CONFIRM_NO | None |

---

### 2. DecisionContext

The complete context used to make an agent decision. Enables reproducibility.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| user_id | String | Required | Authenticated user identifier |
| message | String | Required, max 4000 chars | Current user message |
| conversation_id | UUID | Required | Reference to conversation |
| message_history | List[Message] | Required | Recent conversation history |
| pending_confirmation | PendingAction | Optional | Action awaiting user confirmation |

**Message Structure** (from Spec 001):
```
{
  role: "user" | "assistant",
  content: str,
  timestamp: datetime
}
```

---

### 3. PendingAction

Represents a destructive action awaiting user confirmation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| action_type | Enum | DELETE_TASK only | Type of pending action |
| task_id | UUID | Required | Task targeted for action |
| task_description | String | Required | Human-readable task description |
| created_at | DateTime | Required | When confirmation was requested |
| expires_at | DateTime | Required | Confirmation timeout (e.g., 5 minutes) |

**State Transitions**:
```
[No Pending] --delete_request--> [Pending Confirmation]
[Pending Confirmation] --confirm_yes--> [Execute & Clear]
[Pending Confirmation] --confirm_no--> [Cancel & Clear]
[Pending Confirmation] --timeout--> [Expire & Clear]
[Pending Confirmation] --new_message--> [Cancel & Process New]
```

---

### 4. AgentDecision

The output of the agent's decision process. Determines what action to take.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| decision_type | Enum | Required | Type of decision made |
| tool_calls | List[ToolCall] | Optional | MCP tools to invoke |
| response_text | String | Optional | Natural language response |
| clarification_question | String | Optional | Question to ask user |

**Decision Types (Enum)**:
```
INVOKE_TOOL      - Call one or more MCP tools
RESPOND_ONLY     - Return natural language without tools
ASK_CLARIFICATION - Ask user for more information
REQUEST_CONFIRMATION - Ask user to confirm destructive action
EXECUTE_PENDING  - Execute previously confirmed action
CANCEL_PENDING   - Cancel previously requested action
```

---

### 5. ToolCall

Represents a single MCP tool invocation request.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| tool_name | Enum | Required | MCP tool to invoke |
| parameters | Dict | Required | Parameters for the tool |
| sequence | Integer | Required | Execution order (1-based) |

**Tool Names (Enum)**:
```
add_task
list_tasks
update_task
complete_task
delete_task
```

**Parameter Schemas by Tool**:

| Tool | Parameters |
|------|------------|
| add_task | `{user_id: str, description: str}` |
| list_tasks | `{user_id: str}` |
| update_task | `{user_id: str, task_id: str, description: str}` |
| complete_task | `{user_id: str, task_id: str}` |
| delete_task | `{user_id: str, task_id: str}` |

---

### 6. ToolInvocationRecord

Audit record of a tool invocation. Stored for traceability.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | Primary Key | Unique record identifier |
| conversation_id | UUID | Required, FK | Parent conversation |
| message_id | UUID | Required, FK | Triggering user message |
| user_id | String | Required | User who triggered the action |
| tool_name | String | Required | MCP tool that was called |
| parameters | JSON | Required | Parameters passed to tool |
| intent_classification | String | Required | Classified intent that led to this call |
| result | JSON | Required | Tool response |
| success | Boolean | Required | Whether tool call succeeded |
| error_message | String | Optional | Error details if failed |
| invoked_at | DateTime | Required | Timestamp of invocation |
| duration_ms | Integer | Required | Execution time in milliseconds |

---

## Validation Rules

### Intent Classification

1. Intent MUST be one of the defined enum values
2. `extracted_params` MUST match the schema for the classified intent
3. `AMBIGUOUS` classification MUST include `possible_intents` list

### Tool Invocation

1. `user_id` MUST be present in all tool calls
2. `task_id` MUST be valid UUID format when required
3. `description` MUST be 1-1000 characters when required
4. Tool sequence MUST be respected (no parallel execution)

### Pending Actions

1. Only one pending action per conversation at a time
2. Pending action MUST expire after timeout (default: 5 minutes)
3. Any new user message (except confirmation) cancels pending action

---

## State Machine: Agent Decision Flow

```
                    ┌─────────────────────────────────────────────────┐
                    │                 User Message                     │
                    └─────────────────────┬───────────────────────────┘
                                          │
                    ┌─────────────────────▼───────────────────────────┐
                    │           Check Pending Confirmation             │
                    └─────────────────────┬───────────────────────────┘
                                          │
                         ┌────────────────┴────────────────┐
                         │                                 │
                    Has Pending                       No Pending
                         │                                 │
            ┌────────────┴────────────┐                    │
            │                         │                    │
       Is Confirm?              Not Confirm                │
            │                         │                    │
       ┌────┴────┐             Cancel Pending              │
       │         │                    │                    │
      Yes        No                   │                    │
       │         │                    │                    │
   Execute    Cancel                  │                    │
   Pending    Pending                 │                    │
       │         │                    │                    │
       └────┬────┘                    │                    │
            │                         │                    │
            └─────────────────────────┴────────────────────┤
                                                           │
                    ┌──────────────────────────────────────▼──────────┐
                    │              Classify Intent                     │
                    └──────────────────────────────────────┬──────────┘
                                                           │
         ┌───────────┬───────────┬───────────┬────────────┼────────────┐
         │           │           │           │            │            │
    CREATE_TASK  LIST_TASKS  COMPLETE   UPDATE      DELETE      GENERAL/
         │           │       TASK        TASK        TASK       AMBIGUOUS
         │           │           │           │            │            │
         │           │           └─────┬─────┘            │            │
         │           │                 │                  │            │
         │           │           Read First               │            │
         │           │           (list_tasks)             │            │
         │           │                 │                  │            │
         │           │           Match Task?              │            │
         │           │           /        \               │            │
         │           │        Yes          No             │            │
         │           │          │           │             │            │
         │           │     Execute      Clarify           │            │
         │           │      Tool                          │            │
         │           │                              Request             │
         │           │                            Confirmation          │
         │           │                                    │            │
         ▼           ▼                                    ▼            ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                        Return AgentDecision                          │
    └─────────────────────────────────────────────────────────────────────┘
```

---

## Relationships

```
Conversation (Spec 001)
    │
    ├── has many → Message (Spec 001)
    │                 │
    │                 └── triggers → ToolInvocationRecord
    │
    └── has one → PendingAction (optional, transient)

DecisionContext
    │
    ├── contains → user_id (from auth context)
    ├── contains → message (current user input)
    ├── references → Conversation
    ├── references → Message[] (history)
    └── references → PendingAction (if exists)

AgentDecision
    │
    ├── contains → ToolCall[] (0 or more)
    └── produces → ToolInvocationRecord[] (audit trail)
```

---

## Notes

1. **No new database tables required**: This feature defines logical models for agent processing; `ToolInvocationRecord` can be stored as part of message metadata or a dedicated audit table.

2. **Statelessness**: `DecisionContext` is constructed fresh for each request from conversation history. No server-side agent state persists between requests.

3. **PendingAction storage**: Can be stored in conversation metadata or a separate lightweight store. Must support TTL/expiration.
