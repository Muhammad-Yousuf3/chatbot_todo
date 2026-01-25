# Research Document: Phase V Part 1 - Dapr Event-Driven Architecture

**Branch**: `009-dapr-event-driven` | **Date**: 2026-01-20 | **Plan**: [plan.md](./plan.md)

---

## Purpose

This document resolves all technical unknowns identified during planning and establishes best practices for each technology decision. All "NEEDS CLARIFICATION" items from the Technical Context are addressed here.

---

## 1. Dapr Python SDK Integration

### Decision: Use `dapr-client` Python SDK v1.12+

### Rationale
- Official SDK maintained by Dapr project
- Provides typed client for all building blocks (Pub/Sub, State, Secrets, Service Invocation)
- Async support via `DaprClient` with async context manager
- Well-documented with FastAPI integration examples

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Raw HTTP calls to Dapr sidecar | More boilerplate, no type safety, error handling not standardized |
| dapr-ext-fastapi | Additional dependency; direct SDK is simpler for our use case |
| gRPC interface | HTTP sufficient for our throughput; gRPC adds complexity |

### Integration Pattern
```python
from dapr.clients import DaprClient
from dapr.clients.grpc._state import StateItem

class DaprService:
    def __init__(self):
        self._client = None

    async def get_client(self) -> DaprClient:
        if self._client is None:
            self._client = DaprClient()
        return self._client

    async def close(self):
        if self._client:
            # Client cleanup if needed
            self._client = None
```

### Key SDK Methods
| Method | Use Case |
|--------|----------|
| `publish_event(pubsub_name, topic, data)` | Emit task lifecycle events |
| `save_state(store_name, key, value)` | Store scheduler metadata |
| `get_state(store_name, key)` | Retrieve scheduler state |
| `get_secret(store_name, key)` | Retrieve JWT/DB secrets |
| `invoke_method(app_id, method, data)` | Scheduler → Backend calls |

---

## 2. CloudEvents Specification

### Decision: Use CloudEvents v1.0 JSON format

### Rationale
- CNCF standard for event interoperability
- Native support in Dapr Pub/Sub
- Well-defined schema reduces integration friction
- Enables future event mesh scenarios

### Required Fields (per CloudEvents spec)
```json
{
  "specversion": "1.0",
  "id": "unique-event-id",
  "source": "/backend/tasks",
  "type": "com.todo.task.created",
  "time": "2026-01-20T10:30:00Z",
  "datacontenttype": "application/json",
  "data": { /* payload */ }
}
```

### Event Type Naming Convention
Pattern: `com.todo.<domain>.<action>`

| Event | Type String |
|-------|-------------|
| TaskCreated | `com.todo.task.created` |
| TaskUpdated | `com.todo.task.updated` |
| TaskCompleted | `com.todo.task.completed` |
| TaskDeleted | `com.todo.task.deleted` |
| ReminderTriggered | `com.todo.reminder.triggered` |
| RecurringTaskScheduled | `com.todo.recurring.scheduled` |

### Pydantic Model Pattern
```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class CloudEvent(BaseModel):
    specversion: str = "1.0"
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    type: str
    time: datetime = Field(default_factory=datetime.utcnow)
    datacontenttype: str = "application/json"
    data: dict
```

---

## 3. Dapr Pub/Sub with Redis Streams

### Decision: Use Redis Streams as local message broker

### Rationale
- Single Redis instance serves both Pub/Sub and State Store
- Redis Streams provides persistent, ordered message delivery
- At-least-once delivery guarantee sufficient for our use case
- Zero additional infrastructure beyond what Dapr provides

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| In-memory Redis | Not persistent; messages lost on restart |
| RabbitMQ | Additional service to manage; overkill for local dev |
| Apache Kafka | Heavy for local; managed Kafka explicitly out of scope |
| NATS | Less common; Redis better integrated with Dapr |

### Topic Design
| Topic | Publishers | Subscribers | Purpose |
|-------|------------|-------------|---------|
| `tasks` | Backend, Scheduler | Scheduler, Backend | Task lifecycle events |
| `notifications` | Scheduler | Backend | Reminder/alert events |

### Subscription Configuration (FastAPI)
```python
# Backend subscription endpoint
@app.post("/dapr/subscribe")
async def dapr_subscribe():
    return [
        {
            "pubsubname": "pubsub",
            "topic": "tasks",
            "route": "/events/tasks"
        },
        {
            "pubsubname": "pubsub",
            "topic": "notifications",
            "route": "/events/notifications"
        }
    ]

@app.post("/events/tasks")
async def handle_task_event(event: CloudEvent):
    # Process event based on type
    pass
```

### Consumer Idempotency Strategy
- Store processed event IDs in Redis with TTL (24 hours)
- Key format: `processed:{service}:{event_id}`
- Check existence before processing
- Mark processed after successful handling

---

## 4. Dapr State Store Patterns

### Decision: Use Redis State Store with consistent key namespacing

### Rationale
- Same Redis instance as Pub/Sub reduces infrastructure
- Key-value model sufficient for scheduler metadata
- Dapr provides concurrency control (ETags)
- TTL support for automatic cleanup

### Key Naming Convention
| Data Type | Key Pattern | Example |
|-----------|-------------|---------|
| Recurring schedule | `recurring:{task_id}` | `recurring:abc-123` |
| Reminder state | `reminder:{reminder_id}` | `reminder:xyz-456` |
| Processed events | `processed:{service}:{event_id}` | `processed:scheduler:evt-789` |

### State Schema (Recurring Task)
```json
{
  "task_id": "uuid",
  "user_id": "uuid",
  "title": "string",
  "recurrence_type": "daily | weekly | custom",
  "cron_expression": "string | null",
  "next_occurrence": "ISO8601",
  "created_from_event_id": "uuid"
}
```

### State Schema (Reminder)
```json
{
  "reminder_id": "uuid",
  "task_id": "uuid",
  "user_id": "uuid",
  "trigger_at": "ISO8601",
  "fired": false,
  "cancelled": false
}
```

### Concurrency Control
```python
# Use ETags for optimistic concurrency
state = await client.get_state("statestore", key)
etag = state.etag

# Update with ETag
await client.save_state(
    store_name="statestore",
    key=key,
    value=new_value,
    etag=etag,
    state_metadata={"ttlInSeconds": "86400"}  # 24 hour TTL
)
```

---

## 5. Dapr Cron Bindings

### Decision: Use Dapr input bindings with `@every 1m` schedule

### Rationale
- Native Dapr feature, no custom scheduler code
- Declarative configuration via YAML
- Scoped to specific services (only Scheduler receives triggers)
- 1-minute granularity matches spec requirement

### Binding Configuration
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: recurring-task-trigger
  namespace: todo-app
spec:
  type: bindings.cron
  version: v1
  metadata:
    - name: schedule
      value: "@every 1m"
  scopes:
    - scheduler
```

### Handler Implementation
```python
@app.post("/triggers/recurring")
async def handle_recurring_trigger(request: Request):
    """
    Called by Dapr cron binding every minute.
    Checks state store for recurring tasks due now.
    """
    # 1. Get all recurring task keys from state store
    # 2. Filter by next_occurrence <= now
    # 3. For each due task:
    #    a. Publish RecurringTaskScheduled event
    #    b. Calculate next occurrence
    #    c. Update state with new next_occurrence
    return {"status": "processed"}
```

### Testing Strategy
1. Deploy with `@every 30s` schedule for faster feedback
2. Add structured logging for trigger invocation
3. Verify via `kubectl logs` or Dapr Dashboard
4. Restore `@every 1m` for production-like behavior

---

## 6. Dapr Secrets with Kubernetes Backend

### Decision: Use Kubernetes Secrets as Dapr secret store

### Rationale
- Native to Minikube/Kubernetes
- No additional secret management infrastructure
- Dapr abstracts access; application code is portable
- Supports secret rotation via kubectl

### Secrets to Manage
| Secret Name | Key | Purpose |
|-------------|-----|---------|
| `app-secrets` | `jwt-secret` | JWT token signing |
| `app-secrets` | `database-url` | PostgreSQL connection |

### Secret Creation
```bash
kubectl create secret generic app-secrets \
  --from-literal=jwt-secret=your-32-char-minimum-secret-key-here \
  --from-literal=database-url=postgresql://user:pass@host:5432/db \
  -n todo-app
```

### Application Usage
```python
from dapr.clients import DaprClient

async def get_database_url() -> str:
    with DaprClient() as client:
        secret = client.get_secret(
            store_name="kubernetes-secrets",
            key="app-secrets"
        )
        return secret.secret["database-url"]

# Fallback for local development without Dapr
import os
DATABASE_URL = os.getenv("DATABASE_URL") or await get_database_url()
```

### Graceful Fallback Pattern
```python
class SecretsService:
    def __init__(self, dapr_enabled: bool = True):
        self.dapr_enabled = dapr_enabled

    async def get_secret(self, key: str) -> str:
        if self.dapr_enabled:
            try:
                return await self._get_dapr_secret(key)
            except Exception:
                # Fall back to environment variable
                pass
        return os.environ.get(key, "")
```

---

## 7. Task Model Extension Strategy

### Decision: Add fields incrementally with null defaults

### Rationale
- Backward compatible with existing data
- No migration required for existing tasks
- New fields are optional on create/update
- Gradual adoption in API and MCP tools

### New Fields
| Field | Type | Default | Nullable |
|-------|------|---------|----------|
| `priority` | Enum (high/medium/low) | `medium` | No |
| `tags` | JSON array | `[]` | No |
| `title` | String | N/A | No (rename from description) |
| `reminders` | Relationship | N/A | Yes |
| `recurrence` | Relationship | N/A | Yes |

### SQLModel Definition
```python
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from typing import Optional, List
from uuid import UUID

class TaskPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True)
    title: str = Field(max_length=200)  # Renamed from description
    description: Optional[str] = Field(default=None, max_length=1000)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    tags: List[str] = Field(default=[], sa_column=Column(JSON))
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Relationships
    reminders: List["Reminder"] = Relationship(back_populates="task")
    recurrence: Optional["Recurrence"] = Relationship(back_populates="task")
```

### Migration Approach
1. Add new columns with defaults (non-breaking)
2. Rename `description` to `title` if needed (breaking - coordinate with team)
3. Create Reminder and Recurrence tables
4. Update API schemas to accept new fields
5. Update MCP tools to emit events with full data

---

## 8. Scheduler Service Architecture

### Decision: Standalone FastAPI service with Dapr sidecar

### Rationale
- Separation of concerns: Backend handles CRUD, Scheduler handles time-based logic
- Stateless: All state in Dapr State Store
- Event-driven: Reacts to task events and cron triggers
- No direct database access: Only Dapr building blocks

### Service Responsibilities
| Responsibility | Implementation |
|---------------|----------------|
| Receive TaskCreated events | Extract recurrence/reminder data, store in State Store |
| Receive TaskUpdated events | Update stored schedules/reminders |
| Receive TaskCompleted/Deleted events | Cancel/remove schedules |
| Handle cron trigger (recurring) | Check due tasks, publish RecurringTaskScheduled |
| Handle cron trigger (reminders) | Check due reminders, publish ReminderTriggered |

### Directory Structure
```
scheduler/
├── src/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings (from Dapr secrets)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── triggers.py         # POST /triggers/recurring, /triggers/reminders
│   │   └── subscriptions.py    # POST /dapr/subscribe, event handlers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── recurring.py        # RecurringTaskService
│   │   └── reminder.py         # ReminderService
│   └── dapr/
│       ├── __init__.py
│       ├── client.py           # DaprClient wrapper
│       ├── state.py            # State store operations
│       └── publisher.py        # Event publishing
├── tests/
│   ├── test_recurring.py
│   └── test_reminder.py
├── Dockerfile
├── pyproject.toml
└── README.md
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src/

EXPOSE 8001

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## 9. Event Publishing After Database Operations

### Decision: Publish events after successful commit, not before

### Rationale
- Ensures events represent committed facts
- Avoids publishing events for failed operations
- Maintains consistency between database and event stream

### Pattern: Transactional Outbox (Simplified)
```python
async def create_task(task_data: TaskCreate) -> Task:
    async with session.begin():
        # 1. Create task in database
        task = Task(**task_data.dict())
        session.add(task)
        await session.flush()  # Get task ID

        # 2. Commit transaction
        await session.commit()

    # 3. Publish event AFTER successful commit
    await event_publisher.publish(
        topic="tasks",
        event_type="com.todo.task.created",
        data=task.dict()
    )

    return task
```

### Error Handling
- If database commit fails: No event published (correct)
- If event publish fails: Log error, don't fail user request
- Events are best-effort; consumers handle missing events gracefully

### MCP Tool Integration
```python
@mcp.tool()
async def add_task(
    user_id: str,
    title: str,
    priority: str = "medium",
    tags: list[str] = [],
    ctx: AppContext = None
) -> str:
    # Create task in database
    task = await task_service.create_task(...)

    # Publish event (fire and forget)
    try:
        await ctx.event_publisher.publish_task_created(task)
    except Exception as e:
        logger.error(f"Failed to publish TaskCreated: {e}")

    return f"Created task: {task.title}"
```

---

## 10. Local Development Without Dapr

### Decision: Support both Dapr and non-Dapr modes

### Rationale
- Developers may want to run backend alone for quick testing
- CI environments may not have Dapr installed
- Graceful degradation improves developer experience

### Detection Pattern
```python
import os

def is_dapr_enabled() -> bool:
    # Dapr sidecar sets DAPR_HTTP_PORT environment variable
    return os.getenv("DAPR_HTTP_PORT") is not None

# Or check for sidecar health
async def check_dapr_health() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3500/v1.0/healthz")
            return response.status_code == 204
    except:
        return False
```

### Conditional Feature Enablement
```python
class EventPublisher:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._client = DaprClient() if enabled else None

    async def publish(self, topic: str, event_type: str, data: dict):
        if not self.enabled:
            logger.debug(f"Dapr disabled, skipping event: {event_type}")
            return

        # Actual publish logic
        ...
```

---

## 11. Helm Chart Extension Strategy

### Decision: Add new templates alongside existing ones

### Rationale
- Preserves existing backend/frontend deployments
- Enables gradual rollout
- Single `helm install` deploys complete stack
- Values files control component enablement

### New Templates Required
| Template | Purpose |
|----------|---------|
| `templates/redis/deployment.yaml` | Redis server for Pub/Sub + State Store |
| `templates/redis/service.yaml` | ClusterIP service for Redis |
| `templates/scheduler/deployment.yaml` | Scheduler service with Dapr annotations |
| `templates/scheduler/service.yaml` | ClusterIP service for Scheduler |
| `templates/dapr-components/pubsub.yaml` | Dapr Pub/Sub component |
| `templates/dapr-components/statestore.yaml` | Dapr State Store component |
| `templates/dapr-components/secrets.yaml` | Dapr Secrets component |
| `templates/dapr-components/bindings.yaml` | Dapr Cron bindings |

### Values Structure
```yaml
# values-local.yaml additions
redis:
  enabled: true
  image: redis:7-alpine
  service:
    port: 6379

scheduler:
  enabled: true
  image: todo-scheduler:local
  replicas: 1
  dapr:
    enabled: true
    appId: scheduler
    appPort: 8001

backend:
  dapr:
    enabled: true
    appId: backend
    appPort: 8000

dapr:
  components:
    pubsub:
      name: pubsub
      type: pubsub.redis
    statestore:
      name: statestore
      type: state.redis
    secrets:
      name: kubernetes-secrets
      type: secretstores.kubernetes
```

### Dapr Annotation Template
```yaml
# templates/backend/deployment.yaml
spec:
  template:
    metadata:
      annotations:
        {{- if .Values.backend.dapr.enabled }}
        dapr.io/enabled: "true"
        dapr.io/app-id: {{ .Values.backend.dapr.appId }}
        dapr.io/app-port: {{ .Values.backend.dapr.appPort | quote }}
        {{- end }}
```

---

## 12. Testing Strategy

### Unit Tests
| Component | Test Focus |
|-----------|------------|
| Event schemas | Serialization/deserialization, CloudEvents compliance |
| State operations | Key formatting, TTL handling |
| Recurring logic | Cron expression parsing, next occurrence calculation |
| Reminder logic | Trigger time calculation, cancellation |

### Integration Tests
| Test | Setup | Validation |
|------|-------|------------|
| Event publishing | Local Dapr + Redis | Event appears in Redis Streams |
| Event subscription | Local Dapr + mock subscriber | Handler receives event |
| State store round-trip | Local Dapr + Redis | Value persists and retrieves |
| Cron trigger | Short interval binding | Endpoint called on schedule |

### End-to-End Tests (Minikube)
| Scenario | Steps | Expected Outcome |
|----------|-------|------------------|
| Task creation flow | Create task → Check event → Verify scheduler received | Event in logs, state in Redis |
| Recurring task | Create recurring → Wait for trigger → Check new task | New task in PostgreSQL |
| Reminder flow | Set reminder → Wait for trigger → Check notification | ReminderTriggered event logged |

### Test Tooling
```python
# pytest fixtures for Dapr testing
import pytest
from dapr.clients import DaprClient

@pytest.fixture
def dapr_client():
    """Provides DaprClient for integration tests."""
    client = DaprClient()
    yield client
    # Cleanup state after test
    # client.delete_state(...)

@pytest.fixture
def mock_dapr_client(mocker):
    """Mocks DaprClient for unit tests."""
    return mocker.patch("dapr.clients.DaprClient")
```

---

## Summary of Key Decisions

| Area | Decision | Confidence |
|------|----------|------------|
| SDK | dapr-client Python SDK v1.12+ | High |
| Event Format | CloudEvents v1.0 JSON | High |
| Message Broker | Redis Streams | High |
| State Store | Redis (same instance) | High |
| Cron Scheduler | Dapr Bindings | High |
| Secret Store | Kubernetes Secrets | High |
| Model Extension | Incremental with null defaults | High |
| Scheduler Architecture | Standalone FastAPI service | High |
| Event Publishing | After commit, fire-and-forget | High |
| Local Dev Mode | Dapr detection with fallback | Medium |
| Helm Strategy | Add new templates, extend values | High |

---

**Research Status**: Complete. All unknowns resolved. Ready for Phase 1 design artifacts.
