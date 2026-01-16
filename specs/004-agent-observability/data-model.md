# Data Model: Agent Observability

**Feature**: 004-agent-observability
**Date**: 2026-01-04

## Overview

This document defines the data structures for the observability layer. These models are **additive only** - they capture data from existing agent operations without modifying the agent behavior defined in Spec 003.

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Observability Layer                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  DecisionLog    │ 1────n  │ToolInvocationLog│         │ OutcomeCategory │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)         │         │ category        │
│ decision_id     │◄────────│ decision_id (FK)│         │ subcategory     │
│ conversation_id │         │ tool_name       │         │ description     │
│ user_id         │         │ parameters      │         └─────────────────┘
│ message         │         │ result          │                 │
│ intent_type     │         │ success         │                 │
│ confidence      │         │ error_code      │                 │
│ extracted_params│         │ error_message   │         ┌───────▼─────────┐
│ decision_type   │         │ duration_ms     │         │ BaselineSnapshot│
│ outcome_category│─────────│ invoked_at      │         ├─────────────────┤
│ response_text   │         └─────────────────┘         │ id (PK)         │
│ created_at      │                                     │ snapshot_name   │
│ duration_ms     │                                     │ created_at      │
└─────────────────┘                                     │ intent_dist     │
                                                        │ tool_freq       │
        ┌─────────────────┐                             │ error_rate      │
        │ ValidationReport│                             └─────────────────┘
        ├─────────────────┤
        │ id (PK)         │
        │ run_at          │
        │ test_count      │
        │ pass_count      │
        │ fail_count      │
        │ results (JSON)  │
        │ baseline_id (FK)│
        └─────────────────┘
```

## Entity Definitions

### DecisionLog

A complete record of a single agent decision, from user input to final outcome.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique record identifier |
| decision_id | UUID | Unique, Indexed | Links all log entries for one decision |
| conversation_id | String | Indexed | Reference to conversation |
| user_id | String | Indexed | User who triggered the decision |
| message | String | Max 4000 chars | Original user message |
| intent_type | Enum | See IntentType | Classified intent category |
| confidence | Float | 0.0-1.0 | Classification confidence score |
| extracted_params | JSON | Nullable | Parameters extracted from message |
| decision_type | Enum | See DecisionType | Type of decision made |
| outcome_category | String | Format: "CAT:SUB" | Outcome classification |
| response_text | String | Nullable | Final response to user |
| created_at | DateTime | Indexed | When decision was made |
| duration_ms | Integer | >= 0 | Total decision processing time |

**Indexes**:
- `idx_decision_conversation` on (conversation_id)
- `idx_decision_user` on (user_id)
- `idx_decision_created` on (created_at)
- `idx_decision_outcome` on (outcome_category)

### ToolInvocationLog

A record of a single MCP tool call within a decision.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique record identifier |
| decision_id | UUID | FK → DecisionLog, Indexed | Parent decision |
| tool_name | String | Enum values | MCP tool that was called |
| parameters | JSON | Required | Parameters passed to tool |
| result | JSON | Nullable | Tool response data |
| success | Boolean | Required | Whether invocation succeeded |
| error_code | String | Nullable | Error category if failed |
| error_message | String | Nullable | Detailed error description |
| duration_ms | Integer | >= 0 | Tool execution time |
| invoked_at | DateTime | Required | When tool was called |
| sequence | Integer | >= 1 | Order within decision |

**Indexes**:
- `idx_tool_decision` on (decision_id)
- `idx_tool_name` on (tool_name)
- `idx_tool_invoked` on (invoked_at)

### OutcomeCategory (Reference Table)

Predefined outcome categories and subcategories for classification.

| Category | Subcategory | Description |
|----------|-------------|-------------|
| SUCCESS | TASK_COMPLETED | Task operation successful |
| SUCCESS | RESPONSE_GIVEN | Non-task response provided |
| SUCCESS | CLARIFICATION_ANSWERED | User answered clarification |
| ERROR | USER_INPUT | Invalid user input |
| ERROR | INTENT_CLASSIFICATION | Failed to classify intent |
| ERROR | TOOL_INVOCATION | Tool execution failed |
| ERROR | RESPONSE_GENERATION | Failed to generate response |
| REFUSAL | OUT_OF_SCOPE | Request outside capabilities |
| REFUSAL | MISSING_PERMISSION | User lacks permission |
| REFUSAL | RATE_LIMITED | Too many requests |
| AMBIGUITY | UNCLEAR_INTENT | Cannot determine intent |
| AMBIGUITY | MULTIPLE_MATCHES | Multiple tasks match reference |
| AMBIGUITY | MISSING_CONTEXT | Need more information |

### BaselineSnapshot

A stored pattern of expected behavior for drift comparison.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique snapshot identifier |
| snapshot_name | String | Unique | Human-readable name |
| description | String | Nullable | Purpose/context of baseline |
| created_at | DateTime | Required | When snapshot was taken |
| intent_distribution | JSON | Required | Percentage per intent type |
| tool_frequency | JSON | Required | Call count per tool |
| error_rate | Float | 0.0-1.0 | Overall error percentage |
| sample_size | Integer | >= 0 | Number of decisions in sample |

**Structure of intent_distribution**:
```json
{
  "CREATE_TASK": 0.35,
  "LIST_TASKS": 0.25,
  "COMPLETE_TASK": 0.15,
  "UPDATE_TASK": 0.08,
  "DELETE_TASK": 0.05,
  "GENERAL_CHAT": 0.10,
  "AMBIGUOUS": 0.02
}
```

**Structure of tool_frequency**:
```json
{
  "add_task": 350,
  "list_tasks": 480,
  "complete_task": 150,
  "update_task": 80,
  "delete_task": 50
}
```

### ValidationReport

Results of automated comparison between actual and expected behavior.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique report identifier |
| run_at | DateTime | Required | When validation ran |
| baseline_id | UUID | FK → BaselineSnapshot | Reference baseline used |
| test_count | Integer | >= 0 | Total test cases |
| pass_count | Integer | >= 0 | Successful tests |
| fail_count | Integer | >= 0 | Failed tests |
| results | JSON | Required | Detailed per-test results |
| duration_ms | Integer | >= 0 | Total validation time |
| drift_detected | Boolean | Required | Whether drift exceeded threshold |

**Structure of results**:
```json
{
  "tests": [
    {
      "test_id": "TC001",
      "input": "remind me to buy groceries",
      "expected_intent": "CREATE_TASK",
      "actual_intent": "CREATE_TASK",
      "expected_tool": "add_task",
      "actual_tool": "add_task",
      "status": "PASS"
    },
    {
      "test_id": "TC002",
      "input": "what are my tasks",
      "expected_intent": "LIST_TASKS",
      "actual_intent": "LIST_TASKS",
      "expected_tool": "list_tasks",
      "actual_tool": "list_tasks",
      "status": "PASS"
    }
  ],
  "drift_metrics": {
    "intent_drift": {
      "CREATE_TASK": 0.02,
      "LIST_TASKS": -0.01
    },
    "max_drift": 0.02,
    "threshold_exceeded": false
  }
}
```

## Enumerations

### IntentType (from Spec 003)
Used for reference in logging, not modified:
- CREATE_TASK, LIST_TASKS, COMPLETE_TASK, UPDATE_TASK, DELETE_TASK
- GENERAL_CHAT, AMBIGUOUS, MULTI_INTENT
- CONFIRM_YES, CONFIRM_NO

### DecisionType (from Spec 003)
Used for reference in logging, not modified:
- INVOKE_TOOL, RESPOND_ONLY, ASK_CLARIFICATION
- REQUEST_CONFIRMATION, EXECUTE_PENDING, CANCEL_PENDING

### ToolName (from Spec 003)
Used for reference in logging, not modified:
- add_task, list_tasks, update_task, complete_task, delete_task

### ErrorCode (New)
```
VALIDATION_ERROR     - Input validation failed
INTENT_ERROR         - Intent classification failed
TOOL_NOT_FOUND       - Requested tool doesn't exist
TOOL_EXECUTION_ERROR - Tool failed during execution
DATABASE_ERROR       - Database operation failed
TIMEOUT_ERROR        - Operation exceeded time limit
UNKNOWN_ERROR        - Unexpected error type
```

## Storage Strategy

### SQLite Log Database

Logs are stored in a separate SQLite database (`logs.db`) isolated from the main task database:

```
backend/
└── data/
    ├── tasks.db      # Main PostgreSQL (Neon) for tasks
    └── logs.db       # SQLite for observability logs
```

**Rationale**:
- Separation of concerns: observability doesn't affect task persistence
- No external dependencies per constraints
- SQLite handles concurrent writes safely
- Simple backup/export via file copy

### Retention Policy

- Default retention: 30 days
- Cleanup via scheduled query: `DELETE FROM decision_logs WHERE created_at < date('now', '-30 days')`
- Baselines and validation reports: Retained indefinitely (manually managed)

## Query Patterns

### Query by Conversation
```sql
SELECT * FROM decision_logs
WHERE conversation_id = ?
ORDER BY created_at ASC;
```

### Query by Time Range
```sql
SELECT * FROM decision_logs
WHERE created_at BETWEEN ? AND ?
ORDER BY created_at DESC;
```

### Aggregate Metrics
```sql
SELECT
  outcome_category,
  COUNT(*) as count,
  AVG(duration_ms) as avg_duration
FROM decision_logs
WHERE created_at > date('now', '-1 day')
GROUP BY outcome_category;
```

### Intent Distribution
```sql
SELECT
  intent_type,
  COUNT(*) * 100.0 / (SELECT COUNT(*) FROM decision_logs WHERE created_at > ?) as percentage
FROM decision_logs
WHERE created_at > ?
GROUP BY intent_type;
```

### Tool Usage Frequency
```sql
SELECT
  tool_name,
  COUNT(*) as invocation_count,
  AVG(duration_ms) as avg_duration,
  SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
FROM tool_invocation_logs
WHERE invoked_at > ?
GROUP BY tool_name;
```

## Validation Rules

1. **decision_id uniqueness**: Each decision gets exactly one DecisionLog entry
2. **tool_invocation ordering**: sequence must be unique per decision_id
3. **outcome_category format**: Must match "CATEGORY:SUBCATEGORY" pattern
4. **baseline consistency**: intent_distribution values must sum to 1.0 (±0.01 tolerance)
5. **validation report integrity**: pass_count + fail_count = test_count
