# Quickstart: Agent Observability

**Feature**: 004-agent-observability
**Date**: 2026-01-04

## Overview

This guide shows how to use the observability layer to log, query, and analyze agent decisions. The observability layer is **additive only** - it captures data from existing agent operations without modifying behavior.

## Prerequisites

- Backend running (Spec 001, 002, 003 implemented)
- SQLite available (system default)
- aiosqlite installed (`pip install aiosqlite`)

## Quick Setup

```bash
# Install dependencies
cd backend
uv add aiosqlite

# The observability layer auto-creates logs.db on first use
# No manual database setup required
```

## Recording Decisions

### Automatic Logging (Integration Hook)

Once integrated, every agent request is automatically logged:

```python
# This happens automatically in chat.py after integration
from src.observability import LoggingService

logging_service = LoggingService()

# Every request generates logs automatically
# Decision log: user message, intent, decision, outcome
# Tool logs: each MCP tool invocation with timing
```

### Manual Logging (For Testing)

```python
from src.observability import LoggingService
from uuid import uuid4
from datetime import datetime

logging_service = LoggingService()

# Create a decision log manually
decision_id = uuid4()
await logging_service.write_decision_log(
    decision_id=decision_id,
    conversation_id="conv-123",
    user_id="user-456",
    message="remind me to buy groceries",
    intent=UserIntent(
        intent_type=IntentType.CREATE_TASK,
        confidence=0.95,
        extracted_params={"description": "buy groceries"}
    ),
    decision=AgentDecision(
        decision_type=DecisionType.INVOKE_TOOL,
        tool_calls=[ToolCall(name="add_task", args={"description": "buy groceries"})]
    ),
    outcome_category="SUCCESS:TASK_COMPLETED",
    duration_ms=150
)

# Log a tool invocation
await logging_service.write_tool_invocation_log(
    decision_id=decision_id,
    tool_call=ToolCall(name="add_task", args={"description": "buy groceries"}),
    result={"task_id": "task-789", "status": "pending"},
    success=True,
    error_code=None,
    error_message=None,
    duration_ms=45
)
```

## Querying Logs

### Basic Queries

```python
from src.observability import LogQueryService
from datetime import datetime, timedelta

query_service = LogQueryService()

# Get all decisions for a conversation
decisions = await query_service.query_decisions(
    conversation_id="conv-123",
    limit=100
)

# Get decisions in time range
recent_errors = await query_service.query_decisions(
    start_time=datetime.utcnow() - timedelta(hours=1),
    outcome_category="ERROR",  # Prefix match - gets all ERROR:* categories
    limit=50
)

# Get full trace for a specific decision
trace = await query_service.get_decision_trace(decision_id)
print(f"Decision: {trace.decision.outcome_category}")
for tool in trace.tool_invocations:
    print(f"  Tool: {tool.tool_name}, Duration: {tool.duration_ms}ms")
```

### Metrics Summary

```python
# Get aggregate metrics
summary = await query_service.get_metrics_summary(
    start_time=datetime.utcnow() - timedelta(days=1)
)

print(f"Total decisions: {summary.total_decisions}")
print(f"Success rate: {summary.success_rate * 100:.1f}%")
print(f"Avg decision time: {summary.avg_decision_duration_ms:.0f}ms")

# Intent distribution
for intent, pct in summary.intent_distribution.items():
    print(f"  {intent}: {pct * 100:.1f}%")

# Tool usage
for tool, count in summary.tool_usage.items():
    print(f"  {tool}: {count} calls")
```

### Export for Offline Analysis

```python
# Export logs as JSON
data = await query_service.export_logs(
    start_time=datetime.utcnow() - timedelta(days=7),
    end_time=datetime.utcnow(),
    format="jsonl"  # or "json"
)

with open("logs_export.jsonl", "wb") as f:
    f.write(data)
```

## Baseline Management

### Creating a Baseline

```python
from src.observability import BaselineService

baseline_service = BaselineService()

# Create baseline from last week's verified-good behavior
baseline = await baseline_service.create_baseline(
    name="v1.0-production-baseline",
    description="Baseline from first production week",
    sample_start=datetime(2026, 1, 1),
    sample_end=datetime(2026, 1, 7)
)

print(f"Created baseline: {baseline.snapshot_name}")
print(f"Intent distribution: {baseline.intent_distribution}")
print(f"Tool frequency: {baseline.tool_frequency}")
print(f"Error rate: {baseline.error_rate:.2%}")
```

### Comparing to Baseline

```python
# Compare current behavior to baseline
drift_report = await baseline_service.compare_to_baseline(
    baseline_id=baseline.id,
    current_start=datetime.utcnow() - timedelta(days=1),
    drift_threshold=0.10  # Flag if >10% deviation
)

if drift_report.drift_exceeded:
    print("⚠️ DRIFT DETECTED")
    print(f"Max drift: {drift_report.max_drift:.2%}")
    for metric in drift_report.flagged_metrics:
        print(f"  - {metric}")
else:
    print("✅ Behavior within expected range")
    print(f"Max drift: {drift_report.max_drift:.2%}")
```

## Automated Validation

### Running Test Cases

```python
from src.observability import ValidationService
from pathlib import Path

validation_service = ValidationService()

# Load test fixtures
fixtures = await validation_service.load_fixtures(
    Path("tests/observability/fixtures/agent_behaviors.yaml")
)

# Run validation
report = await validation_service.run_validation(
    test_fixtures=fixtures,
    baseline_id=baseline.id  # Optional: also check drift
)

print(f"Tests: {report.pass_count}/{report.test_count} passed")
if report.fail_count > 0:
    print("Failures:")
    for test in report.results["tests"]:
        if test["status"] == "FAIL":
            print(f"  {test['test_id']}: expected {test['expected_intent']}, got {test['actual_intent']}")

if report.drift_detected:
    print("⚠️ Drift detected during validation")
```

### Test Fixture Format

```yaml
# tests/observability/fixtures/agent_behaviors.yaml
tests:
  - test_id: TC001
    input: "remind me to buy groceries"
    expected_intent: CREATE_TASK
    expected_tool: add_task
    expected_outcome: SUCCESS

  - test_id: TC002
    input: "what are my tasks"
    expected_intent: LIST_TASKS
    expected_tool: list_tasks
    expected_outcome: SUCCESS

  - test_id: TC003
    input: "groceries"
    expected_intent: AMBIGUOUS
    expected_tool: null
    expected_outcome: AMBIGUITY

  - test_id: TC004
    input: "hello"
    expected_intent: GENERAL_CHAT
    expected_tool: null
    expected_outcome: SUCCESS
```

## Demo Review Workflow

### Preparing for Demo

```python
# Clear old test data (optional)
# Run with fresh logs for clean demo

# Create a reference session
demo_conversation_id = "demo-session-001"

# ... run through demo scenarios ...

# Get session summary
summary = await query_service.get_metrics_summary(
    start_time=demo_start_time,
    user_id=demo_user_id
)

print("Demo Summary:")
print(f"  Total interactions: {summary.total_decisions}")
print(f"  Success rate: {summary.success_rate:.0%}")
print(f"  Avg response time: {summary.avg_decision_duration_ms:.0f}ms")
```

### Reviewer Inspection

```python
# Reviewer gets decision trace for any interaction
trace = await query_service.get_decision_trace(decision_id)

# Display decision path
print(f"User said: {trace.decision.message}")
print(f"Intent: {trace.decision.intent_type} (confidence: {trace.decision.confidence:.0%})")
print(f"Decision: {trace.decision.decision_type}")
print(f"Outcome: {trace.decision.outcome_category}")

if trace.tool_invocations:
    print("Tools invoked:")
    for tool in trace.tool_invocations:
        status = "✓" if tool.success else "✗"
        print(f"  {status} {tool.tool_name}: {tool.duration_ms}ms")
```

## Outcome Categories Reference

| Category | Subcategory | When Used |
|----------|-------------|-----------|
| SUCCESS | TASK_COMPLETED | Task operation succeeded |
| SUCCESS | RESPONSE_GIVEN | General response without tool |
| SUCCESS | CLARIFICATION_ANSWERED | User answered a clarification |
| ERROR | USER_INPUT | Invalid user input |
| ERROR | INTENT_CLASSIFICATION | Could not classify intent |
| ERROR | TOOL_INVOCATION | Tool execution failed |
| ERROR | RESPONSE_GENERATION | Could not generate response |
| REFUSAL | OUT_OF_SCOPE | Request outside capabilities |
| REFUSAL | MISSING_PERMISSION | User lacks permission |
| REFUSAL | RATE_LIMITED | Too many requests |
| AMBIGUITY | UNCLEAR_INTENT | Cannot determine intent |
| AMBIGUITY | MULTIPLE_MATCHES | Multiple tasks match reference |
| AMBIGUITY | MISSING_CONTEXT | Need more information |

## Common Patterns

### Investigating a Failed Request

```python
# Find the failing decision
errors = await query_service.query_decisions(
    user_id="affected-user",
    outcome_category="ERROR",
    limit=10
)

for error in errors.items:
    trace = await query_service.get_decision_trace(error.id)

    print(f"\n--- Error Analysis ---")
    print(f"Time: {error.created_at}")
    print(f"Message: {error.message}")
    print(f"Intent: {error.intent_type}")
    print(f"Outcome: {error.outcome_category}")

    if trace.tool_invocations:
        failed_tools = [t for t in trace.tool_invocations if not t.success]
        for tool in failed_tools:
            print(f"Tool failed: {tool.tool_name}")
            print(f"  Error: {tool.error_code} - {tool.error_message}")
```

### Monitoring Intent Distribution Over Time

```python
# Compare last week to this week
last_week = await query_service.get_metrics_summary(
    start_time=datetime.utcnow() - timedelta(days=14),
    end_time=datetime.utcnow() - timedelta(days=7)
)

this_week = await query_service.get_metrics_summary(
    start_time=datetime.utcnow() - timedelta(days=7)
)

print("Intent Distribution Change:")
for intent in last_week.intent_distribution:
    old = last_week.intent_distribution.get(intent, 0)
    new = this_week.intent_distribution.get(intent, 0)
    change = new - old
    sign = "+" if change > 0 else ""
    print(f"  {intent}: {old:.1%} → {new:.1%} ({sign}{change:.1%})")
```

## Troubleshooting

### Logs Not Appearing

```python
# Verify logging service is initialized
from src.observability import LoggingService
service = LoggingService()

# Check database file exists
import os
print(f"Logs DB exists: {os.path.exists('data/logs.db')}")

# Verify connection
from src.observability.database import get_log_db
async with get_log_db() as db:
    result = await db.execute("SELECT COUNT(*) FROM decision_logs")
    count = result.fetchone()[0]
    print(f"Decision logs in DB: {count}")
```

### Query Performance Issues

```python
# For large datasets, use time-based filters
results = await query_service.query_decisions(
    start_time=datetime.utcnow() - timedelta(hours=1),  # Narrow time range
    limit=100  # Limit results
)

# Avoid unbounded queries
# BAD: query_decisions(limit=10000)
# GOOD: query_decisions(start_time=..., limit=100)
```

### Missing Tool Invocations

```python
# Ensure tool logging is happening
trace = await query_service.get_decision_trace(decision_id)
if trace.decision.decision_type == "INVOKE_TOOL" and not trace.tool_invocations:
    print("WARNING: Decision says tool was invoked but no tool logs found")
    print("Check that tool logging hook is properly integrated")
```
