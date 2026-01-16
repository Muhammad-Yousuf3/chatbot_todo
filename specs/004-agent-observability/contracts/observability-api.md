# Observability API Contract

**Feature**: 004-agent-observability
**Date**: 2026-01-04
**Version**: 1.0.0

## Overview

This contract defines the internal APIs for the observability layer. These are **internal service APIs** used by the application to:
1. Write decision and tool logs
2. Query logs for review
3. Manage baselines and validation

**Note**: These are NOT external HTTP endpoints. They are Python service interfaces. No UI dashboards are created per constraints.

---

## Log Writing Interface

### LoggingService

The logging service provides a facade for recording agent decisions and tool invocations.

#### write_decision_log

Records a complete agent decision.

**Signature**:
```python
async def write_decision_log(
    decision_id: UUID,
    conversation_id: str,
    user_id: str,
    message: str,
    intent: UserIntent,
    decision: AgentDecision,
    outcome_category: str,
    duration_ms: int
) -> DecisionLog
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| decision_id | UUID | Yes | Unique identifier for this decision |
| conversation_id | str | Yes | Conversation context |
| user_id | str | Yes | User who sent the message |
| message | str | Yes | Original user message (max 4000 chars) |
| intent | UserIntent | Yes | Classified intent from agent |
| decision | AgentDecision | Yes | Decision made by agent |
| outcome_category | str | Yes | Format "CATEGORY:SUBCATEGORY" |
| duration_ms | int | Yes | Total processing time |

**Returns**: `DecisionLog` - The persisted log entry

**Errors**:
- `ValidationError`: Invalid outcome_category format
- `StorageError`: Failed to persist log

---

#### write_tool_invocation_log

Records a tool invocation within a decision.

**Signature**:
```python
async def write_tool_invocation_log(
    decision_id: UUID,
    tool_call: ToolCall,
    result: dict | None,
    success: bool,
    error_code: str | None,
    error_message: str | None,
    duration_ms: int
) -> ToolInvocationLog
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| decision_id | UUID | Yes | Parent decision ID |
| tool_call | ToolCall | Yes | Tool call details from agent |
| result | dict | None | No | Tool response (if successful) |
| success | bool | Yes | Whether tool succeeded |
| error_code | str | None | No | Error category (if failed) |
| error_message | str | None | No | Detailed error (if failed) |
| duration_ms | int | Yes | Tool execution time |

**Returns**: `ToolInvocationLog` - The persisted log entry

**Errors**:
- `InvalidDecisionError`: decision_id not found
- `StorageError`: Failed to persist log

---

## Log Query Interface

### LogQueryService

The query service provides read access to logs for review and analysis.

#### get_decision_trace

Gets the complete decision trace for a single decision.

**Signature**:
```python
async def get_decision_trace(
    decision_id: UUID
) -> DecisionTrace
```

**Returns**:
```python
class DecisionTrace:
    decision: DecisionLog
    tool_invocations: list[ToolInvocationLog]
```

**Errors**:
- `DecisionNotFoundError`: decision_id doesn't exist

---

#### query_decisions

Queries decision logs with filters.

**Signature**:
```python
async def query_decisions(
    conversation_id: str | None = None,
    user_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    decision_type: DecisionType | None = None,
    outcome_category: str | None = None,
    limit: int = 100,
    offset: int = 0
) -> QueryResult[DecisionLog]
```

**Parameters**:
| Name | Type | Default | Description |
|------|------|---------|-------------|
| conversation_id | str | None | Filter by conversation |
| user_id | str | None | Filter by user |
| start_time | datetime | None | Filter after timestamp |
| end_time | datetime | None | Filter before timestamp |
| decision_type | DecisionType | None | Filter by decision type |
| outcome_category | str | None | Filter by outcome (exact or prefix match) |
| limit | int | 100 | Max results (max 1000) |
| offset | int | 0 | Pagination offset |

**Returns**:
```python
class QueryResult[T]:
    items: list[T]
    total: int
    has_more: bool
```

---

#### get_metrics_summary

Gets aggregated metrics for a time period.

**Signature**:
```python
async def get_metrics_summary(
    start_time: datetime,
    end_time: datetime | None = None,
    user_id: str | None = None
) -> MetricsSummary
```

**Returns**:
```python
class MetricsSummary:
    total_decisions: int
    success_rate: float  # 0.0-1.0
    error_breakdown: dict[str, int]  # {category: count}
    avg_decision_duration_ms: float
    avg_tool_duration_ms: float
    intent_distribution: dict[str, float]  # {intent: percentage}
    tool_usage: dict[str, int]  # {tool_name: count}
```

---

#### export_logs

Exports logs in portable JSON format.

**Signature**:
```python
async def export_logs(
    start_time: datetime,
    end_time: datetime,
    format: Literal["json", "jsonl"] = "json"
) -> bytes
```

**Returns**: JSON-formatted log data as bytes (for file writing)

---

## Baseline Management Interface

### BaselineService

Manages behavioral baselines for drift detection.

#### create_baseline

Creates a new baseline snapshot from current logs.

**Signature**:
```python
async def create_baseline(
    name: str,
    description: str | None,
    sample_start: datetime,
    sample_end: datetime
) -> BaselineSnapshot
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | str | Yes | Unique baseline name |
| description | str | No | Purpose of baseline |
| sample_start | datetime | Yes | Start of sample period |
| sample_end | datetime | Yes | End of sample period |

**Returns**: `BaselineSnapshot` - Created baseline

**Errors**:
- `InsufficientDataError`: Not enough decisions in sample period
- `DuplicateNameError`: Baseline name already exists

---

#### compare_to_baseline

Compares current behavior to a stored baseline.

**Signature**:
```python
async def compare_to_baseline(
    baseline_id: UUID,
    current_start: datetime,
    current_end: datetime | None = None,
    drift_threshold: float = 0.10
) -> DriftReport
```

**Returns**:
```python
class DriftReport:
    baseline_id: UUID
    baseline_name: str
    comparison_period: tuple[datetime, datetime]
    intent_drift: dict[str, float]  # {intent: delta}
    tool_drift: dict[str, float]   # {tool: delta}
    max_drift: float
    drift_exceeded: bool
    flagged_metrics: list[str]
```

---

## Validation Interface

### ValidationService

Runs automated validation against expected behaviors.

#### run_validation

Executes validation test suite.

**Signature**:
```python
async def run_validation(
    test_fixtures: list[TestCase],
    baseline_id: UUID | None = None
) -> ValidationReport
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| test_fixtures | list[TestCase] | Yes | Test cases to run |
| baseline_id | UUID | None | No | Optional baseline for drift check |

**TestCase Structure**:
```python
class TestCase:
    test_id: str
    input_message: str
    expected_intent: IntentType
    expected_tool: ToolName | None
    expected_outcome: str  # Outcome category prefix
```

**Returns**: `ValidationReport` as defined in data model

---

#### load_fixtures

Loads test fixtures from file.

**Signature**:
```python
async def load_fixtures(
    fixtures_path: Path
) -> list[TestCase]
```

**Fixture File Format (YAML)**:
```yaml
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
```

---

## Error Codes

| Code | Description |
|------|-------------|
| VALIDATION_ERROR | Input validation failed |
| STORAGE_ERROR | Database operation failed |
| DECISION_NOT_FOUND | Decision ID doesn't exist |
| BASELINE_NOT_FOUND | Baseline ID doesn't exist |
| INSUFFICIENT_DATA | Not enough data for operation |
| DUPLICATE_NAME | Name already exists |
| INVALID_FORMAT | Input format is incorrect |
| QUERY_TIMEOUT | Query exceeded time limit |

---

## Usage Examples

### Recording a Decision

```python
from src.observability import LoggingService
from uuid import uuid4

logging_service = LoggingService()

# After agent processes message
decision_id = uuid4()
start = datetime.now()

# ... agent processing ...

decision_log = await logging_service.write_decision_log(
    decision_id=decision_id,
    conversation_id=context.conversation_id,
    user_id=context.user_id,
    message=context.message,
    intent=classified_intent,
    decision=agent_decision,
    outcome_category="SUCCESS:TASK_COMPLETED",
    duration_ms=int((datetime.now() - start).total_seconds() * 1000)
)
```

### Querying for Review

```python
from src.observability import LogQueryService

query_service = LogQueryService()

# Get all errors in last hour
errors = await query_service.query_decisions(
    start_time=datetime.now() - timedelta(hours=1),
    outcome_category="ERROR",
    limit=50
)

for error in errors.items:
    trace = await query_service.get_decision_trace(error.id)
    print(f"Error: {trace.decision.outcome_category}")
    for tool in trace.tool_invocations:
        print(f"  Tool: {tool.tool_name}, Success: {tool.success}")
```

### Running Validation

```python
from src.observability import ValidationService

validation_service = ValidationService()

fixtures = await validation_service.load_fixtures(
    Path("tests/fixtures/agent_behaviors.yaml")
)

report = await validation_service.run_validation(
    test_fixtures=fixtures,
    baseline_id=production_baseline_id
)

if report.fail_count > 0:
    print(f"Validation failed: {report.fail_count} failures")
    for test in report.results["tests"]:
        if test["status"] == "FAIL":
            print(f"  {test['test_id']}: expected {test['expected_intent']}, got {test['actual_intent']}")
```
