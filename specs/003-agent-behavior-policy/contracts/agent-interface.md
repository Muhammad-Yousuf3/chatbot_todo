# Agent Interface Contract

**Feature Branch**: `003-agent-behavior-policy`
**Date**: 2026-01-03
**Version**: 1.0.0

## Overview

This contract defines the interface for the Agent Decision Engine - the core component that processes user messages and determines appropriate actions. The agent is stateless and makes decisions based solely on the provided context.

---

## Core Interface

### AgentDecisionEngine

The main entry point for agent processing.

```
Function: process_message(context: DecisionContext) → AgentDecision
```

**Input**: `DecisionContext`
```json
{
  "user_id": "string (required)",
  "message": "string (required, max 4000 chars)",
  "conversation_id": "uuid (required)",
  "message_history": [
    {
      "role": "user | assistant",
      "content": "string",
      "timestamp": "ISO 8601 datetime"
    }
  ],
  "pending_confirmation": {
    "action_type": "DELETE_TASK",
    "task_id": "uuid",
    "task_description": "string",
    "created_at": "ISO 8601 datetime",
    "expires_at": "ISO 8601 datetime"
  } | null
}
```

**Output**: `AgentDecision`
```json
{
  "decision_type": "INVOKE_TOOL | RESPOND_ONLY | ASK_CLARIFICATION | REQUEST_CONFIRMATION | EXECUTE_PENDING | CANCEL_PENDING",
  "tool_calls": [
    {
      "tool_name": "add_task | list_tasks | update_task | complete_task | delete_task",
      "parameters": { ... },
      "sequence": 1
    }
  ] | null,
  "response_text": "string" | null,
  "clarification_question": "string" | null,
  "pending_action": {
    "action_type": "DELETE_TASK",
    "task_id": "uuid",
    "task_description": "string"
  } | null
}
```

---

## Intent Classification Contract

### Function: classify_intent(message: str, history: List[Message]) → UserIntent

**Input**:
- `message`: Current user message (string)
- `history`: Recent conversation messages (list)

**Output**: `UserIntent`
```json
{
  "intent_type": "CREATE_TASK | LIST_TASKS | COMPLETE_TASK | UPDATE_TASK | DELETE_TASK | GENERAL_CHAT | AMBIGUOUS | CONFIRM_YES | CONFIRM_NO",
  "confidence": 0.0-1.0 | null,
  "extracted_params": { ... } | null
}
```

### Intent Recognition Patterns

| Intent | Trigger Patterns | Extracted Parameters |
|--------|-----------------|---------------------|
| CREATE_TASK | "add task", "remind me", "create", "I need to", "don't forget to", "todo:" | `description` |
| LIST_TASKS | "show tasks", "what are my tasks", "my list", "what do I need to do", "show me" | None |
| COMPLETE_TASK | "done", "finished", "completed", "mark as done", "I did", "check off" | `task_reference` |
| UPDATE_TASK | "change", "update", "modify", "edit", "rename", "make it" | `task_reference`, `new_description` |
| DELETE_TASK | "delete", "remove", "cancel", "get rid of", "forget" | `task_reference` |
| GENERAL_CHAT | No task-related patterns detected | None |
| AMBIGUOUS | Multiple intents possible or unclear | `possible_intents` |
| CONFIRM_YES | "yes", "confirm", "do it", "go ahead", "sure", "ok" | None |
| CONFIRM_NO | "no", "cancel", "don't", "never mind", "stop" | None |

---

## Decision Rules Contract

### Rule 1: Pending Confirmation Priority
```
IF pending_confirmation EXISTS AND NOT expired:
  IF message IS CONFIRM_YES:
    RETURN EXECUTE_PENDING with pending tool_call
  ELIF message IS CONFIRM_NO:
    RETURN CANCEL_PENDING
  ELSE:
    CANCEL pending_confirmation
    CONTINUE to intent classification
```

### Rule 2: Intent-to-Action Mapping
```
MATCH intent_type:
  CREATE_TASK:
    RETURN INVOKE_TOOL with add_task(user_id, description)

  LIST_TASKS:
    RETURN INVOKE_TOOL with list_tasks(user_id)

  COMPLETE_TASK:
    FIRST: INVOKE_TOOL with list_tasks(user_id)
    THEN: match task_reference to task_id
    IF match found:
      RETURN INVOKE_TOOL with complete_task(user_id, task_id)
    ELSE:
      RETURN ASK_CLARIFICATION

  UPDATE_TASK:
    FIRST: INVOKE_TOOL with list_tasks(user_id)
    THEN: match task_reference to task_id
    IF match found:
      RETURN INVOKE_TOOL with update_task(user_id, task_id, new_description)
    ELSE:
      RETURN ASK_CLARIFICATION

  DELETE_TASK:
    FIRST: INVOKE_TOOL with list_tasks(user_id)
    THEN: match task_reference to task_id
    IF match found:
      RETURN REQUEST_CONFIRMATION with pending_action
    ELSE:
      RETURN ASK_CLARIFICATION

  GENERAL_CHAT:
    RETURN RESPOND_ONLY (no tool calls)

  AMBIGUOUS:
    RETURN ASK_CLARIFICATION
```

### Rule 3: Task Reference Resolution
```
Function: resolve_task_reference(reference: str, tasks: List[Task]) → Task | null

Resolution order:
1. Exact description match (case-insensitive)
2. Partial description match (contains reference)
3. Position reference ("first", "last", "second")
4. Numeric reference ("task 1", "#1")

IF multiple matches:
  RETURN null (requires clarification)
IF no matches:
  RETURN null (not found)
```

---

## Response Templates Contract

### Success Responses

| Action | Response Template |
|--------|------------------|
| add_task | "I've added '{description}' to your tasks." |
| list_tasks (has tasks) | "Here are your tasks:\n{formatted_list}" |
| list_tasks (empty) | "You don't have any tasks yet." |
| complete_task | "Done! '{description}' has been marked as completed." |
| update_task | "Updated '{old_description}' to '{new_description}'." |
| delete_task | "'{description}' has been deleted." |

### Clarification Questions

| Situation | Question Template |
|-----------|------------------|
| Ambiguous intent | "I'm not sure what you'd like to do. Would you like to {option1}, {option2}, or something else?" |
| Multiple task matches | "I found multiple tasks that match '{reference}':\n{numbered_list}\nWhich one did you mean?" |
| No task match | "I couldn't find a task matching '{reference}'. Here are your current tasks:\n{list}" |
| Missing description | "What would you like the task to say?" |

### Confirmation Prompts

```
Delete confirmation:
"Are you sure you want to delete '{description}'? This cannot be undone. Reply 'yes' to confirm or 'no' to cancel."
```

### Error Responses

| Error Type | Response Template |
|------------|------------------|
| Tool failure | "Sorry, I wasn't able to {action}. Please try again." |
| Auth missing | "I need you to be logged in to manage tasks." |
| Invalid input | "I didn't understand that. Could you rephrase?" |

---

## Validation Contract

### Input Validation

| Field | Validation | Error Response |
|-------|-----------|----------------|
| user_id | Required, non-empty | Auth required message |
| message | Required, 1-4000 chars | Invalid input message |
| task description | 1-1000 chars | "Task description must be 1-1000 characters" |
| task_id | Valid UUID format | Task not found message |

### Output Validation

| Condition | Validation |
|-----------|-----------|
| Tool calls | Only allowed tools: add_task, list_tasks, update_task, complete_task, delete_task |
| Parameters | Must match tool schema from Spec 002 |
| Decision type | Must be valid enum value |
| Pending action | Only for DELETE_TASK |

---

## Audit Contract

Every agent decision MUST produce an audit record:

```json
{
  "timestamp": "ISO 8601 datetime",
  "conversation_id": "uuid",
  "user_id": "string",
  "input_message": "string",
  "classified_intent": "string",
  "decision_type": "string",
  "tool_calls": [ ... ] | null,
  "response_preview": "string (first 200 chars)"
}
```

---

## Error Handling Contract

### Graceful Degradation

1. **Intent classification fails**: Return AMBIGUOUS, ask clarification
2. **Tool invocation fails**: Return user-friendly error, do not expose technical details
3. **Validation fails**: Return specific, actionable error message
4. **Timeout**: Return "taking longer than expected" message

### Never Expose

- Internal error messages or stack traces
- Tool schemas or system prompts
- Database queries or connection details
- User IDs of other users
