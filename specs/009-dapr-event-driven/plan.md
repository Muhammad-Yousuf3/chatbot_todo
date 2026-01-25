# Implementation Plan: Phase V Part 1 - Cloud-Native Event-Driven Todo Chatbot

**Branch**: `009-dapr-event-driven` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-dapr-event-driven/spec.md`

---

## Summary

Transform the existing Todo Chatbot into a **cloud-native, event-driven application** using Dapr building blocks, with local Minikube deployment. This phase extends the Task model with priority, tags, recurrence, and reminders; introduces event publishing for task lifecycle operations; creates a new Scheduler Service for time-based triggers; and integrates all five Dapr building blocks (Pub/Sub, State Store, Bindings, Secrets, Service Invocation).

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.109+, SQLModel, dapr-client (Python SDK), pydantic 2.x
**Storage**: PostgreSQL (existing via Neon), Redis (new - for Dapr Pub/Sub & State Store)
**Testing**: pytest, pytest-asyncio, httpx (async HTTP client)
**Target Platform**: Minikube (single-node Kubernetes cluster)
**Project Type**: Web application (multi-service)
**Performance Goals**: 3s CRUD operations, 2s search, 2min reminder/recurrence trigger accuracy
**Constraints**: LOCAL ONLY - no cloud providers, no CI/CD, no managed services, no monitoring stacks
**Scale/Scope**: Single-user focus, development/validation environment only

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Development | ✅ PASS | Specification created and approved before planning |
| II. Stateless Backend Architecture | ✅ PASS | Backend remains stateless; scheduler state persisted via Dapr State Store |
| III. Clear Responsibility Boundaries | ✅ PASS | Backend: CRUD + event emission; Scheduler: time-based triggers; Dapr: infrastructure abstraction |
| IV. AI Safety Through Controlled Tool Usage | ✅ PASS | MCP tools remain the only database access point for AI agents |
| V. Simplicity Over Cleverness | ✅ PASS | Uses established Dapr patterns; Redis for local simplicity |
| VI. Deterministic, Debuggable Behavior | ✅ PASS | Events are immutable facts with IDs and timestamps; Dapr Dashboard for debugging |

**Technical Constraints Compliance**:
- ✅ Backend Framework: FastAPI (unchanged)
- ✅ Database ORM: SQLModel (unchanged)
- ✅ Database: PostgreSQL (unchanged)
- ✅ Authentication: JWT python-jose (unchanged)
- ✅ AI Orchestration: OpenAI Agents SDK via MCP (unchanged)
- ✅ Tool Interface: Official MCP SDK (unchanged)
- ✅ Frontend Chat UI: Next.js + Tailwind (unchanged)
- ✅ NEW: Dapr Python SDK for event-driven infrastructure

**Prohibited Patterns Check**:
- ✅ No direct database access from AI agents (MCP tools only)
- ✅ No hidden global state (Dapr State Store is explicit, external)
- ✅ Specification approved before this plan
- ✅ No hardcoded secrets (Dapr Secrets component)
- ✅ No speculative features (all features defined in spec)

---

## Project Structure

### Documentation (this feature)

```text
specs/009-dapr-event-driven/
├── spec.md              # Feature specification (COMPLETED)
├── plan.md              # This file
├── research.md          # Phase 0 output - Dapr patterns and decisions
├── data-model.md        # Phase 1 output - Extended entity definitions
├── quickstart.md        # Phase 1 output - Local deployment guide
├── contracts/           # Phase 1 output - Event schemas and API contracts
│   ├── events.yaml      # CloudEvents schemas for all event types
│   ├── scheduler-api.yaml  # Scheduler Service OpenAPI spec
│   └── backend-events.yaml # Backend event publishing endpoints
└── tasks.md             # Phase 2 output (via /sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── tasks.py        # EXTEND: Add event publishing
│   │   │   └── events.py       # NEW: Event subscription endpoints
│   │   └── schemas/
│   │       ├── tasks.py        # EXTEND: Priority, tags, recurrence, reminders
│   │       └── events.py       # NEW: Event payload schemas
│   ├── models/
│   │   ├── task.py             # EXTEND: Priority, tags fields
│   │   ├── reminder.py         # NEW: Reminder model
│   │   └── recurrence.py       # NEW: Recurrence schedule model
│   ├── events/                 # NEW: Event infrastructure
│   │   ├── publisher.py        # Dapr Pub/Sub publishing
│   │   ├── schemas.py          # CloudEvents envelope format
│   │   └── constants.py        # Topic names, event types
│   ├── mcp_server/tools/       # EXTEND: Emit events after operations
│   │   ├── add_task.py
│   │   ├── update_task.py
│   │   ├── complete_task.py
│   │   └── delete_task.py
│   └── dapr/                   # NEW: Dapr client wrapper
│       ├── client.py           # DaprClient initialization
│       └── secrets.py          # Secrets retrieval helper

scheduler/                       # NEW SERVICE
├── src/
│   ├── main.py                 # FastAPI app for scheduler service
│   ├── api/
│   │   ├── triggers.py         # Cron binding trigger endpoints
│   │   └── subscriptions.py    # Pub/Sub event handlers
│   ├── services/
│   │   ├── recurring.py        # Recurring task logic
│   │   └── reminder.py         # Reminder processing logic
│   └── dapr/
│       ├── state.py            # State store operations
│       └── publisher.py        # Event publishing
├── Dockerfile
├── pyproject.toml
└── tests/

helm/todo-chatbot/
├── templates/
│   ├── backend/
│   │   └── deployment.yaml     # EXTEND: Add Dapr annotations
│   ├── scheduler/              # NEW
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── redis/                  # NEW
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── dapr-components/        # NEW
│       ├── pubsub.yaml
│       ├── statestore.yaml
│       ├── secrets.yaml
│       └── bindings.yaml
└── values-local.yaml           # EXTEND: Scheduler + Redis config
```

**Structure Decision**: Web application with two backend services (backend + scheduler) plus infrastructure (Redis). Frontend unchanged. Dapr components deployed as Kubernetes manifests within Helm chart.

---

## Architecture Decomposition

### Core Services

| Service | Responsibility | Dapr Sidecar | Database Access |
|---------|---------------|--------------|-----------------|
| **Backend** | Task CRUD, JWT auth, event publishing, notification handling | Yes (app-id: backend) | PostgreSQL (direct) |
| **Scheduler** | Recurring task instantiation, reminder triggering, cron binding handlers | Yes (app-id: scheduler) | None (via State Store only) |
| **Frontend** | User interface, API calls via NodePort | No | None |

### Event Producers

| Producer | Events Emitted | Topic |
|----------|---------------|-------|
| Backend Service | TaskCreated, TaskUpdated, TaskCompleted, TaskDeleted | `tasks` |
| Scheduler Service | ReminderTriggered, RecurringTaskScheduled | `notifications`, `tasks` |

### Event Consumers

| Consumer | Events Subscribed | Topic | Action |
|----------|------------------|-------|--------|
| Scheduler Service | TaskCreated, TaskUpdated, TaskCompleted, TaskDeleted | `tasks` | Update schedules/reminders in State Store |
| Backend Service | ReminderTriggered | `notifications` | Mark reminder as fired, update task metadata |
| Backend Service | RecurringTaskScheduled | `tasks` | Create new task instance in PostgreSQL |

### Dapr Sidecar Responsibilities

| Building Block | Used By | Purpose |
|---------------|---------|---------|
| Pub/Sub | Backend, Scheduler | Publish/subscribe to `tasks` and `notifications` topics |
| State Store | Scheduler | Persist recurring task schedules and reminder state |
| Bindings (Cron) | Scheduler | Trigger recurring task checks and reminder checks every minute |
| Secrets | Backend, Scheduler | Retrieve DATABASE_URL, JWT_SECRET at runtime |
| Service Invocation | Scheduler → Backend | Query task details when processing recurrence |

### Supporting Components

| Component | Type | Purpose |
|-----------|------|---------|
| Redis | Infrastructure | Message broker (Pub/Sub) + Key-Value store (State Store) |
| Kubernetes Secrets | Infrastructure | Store sensitive configuration (JWT secret, DB URL) |

---

## Phased Execution Strategy

### Phase A: Feature Model Extensions

**Goal**: Extend Task model with priority, tags, recurrence, and reminder fields without breaking existing functionality.

**Inputs**:
- Existing Task model (`backend/src/models/task.py`)
- Existing Task schemas (`backend/src/api/schemas/tasks.py`)
- Existing MCP tools (`backend/src/mcp_server/tools/`)

**Outputs**:
- Extended Task model with new fields
- Extended API schemas for CRUD operations
- Database migration script
- Updated MCP tools accepting new fields

**Dependencies**: None (can start immediately)

**Acceptance Criteria**:
- [ ] Task model includes `priority: Enum(high|medium|low)` field
- [ ] Task model includes `tags: List[str]` field (JSON array in PostgreSQL)
- [ ] Task model includes `due_date: Optional[datetime]` field (already exists - verify)
- [ ] Task model includes `reminders: List[Reminder]` relationship
- [ ] Task model includes `recurrence: Optional[Recurrence]` relationship
- [ ] All existing tests pass with new fields
- [ ] API accepts priority and tags in create/update operations
- [ ] MCP tools accept new fields as optional parameters

---

### Phase B: Event Model Definition

**Goal**: Define standardized event schemas using CloudEvents specification.

**Inputs**:
- Event catalog from spec (Section 5)
- CloudEvents specification (CNCF standard)

**Outputs**:
- Event envelope schema (CloudEvents format)
- Individual event payload schemas (TaskCreated, TaskUpdated, etc.)
- Event constants (topic names, event types)
- Pydantic models for validation

**Dependencies**: Phase A (needs extended Task model for event payloads)

**Acceptance Criteria**:
- [ ] CloudEvents envelope with `id`, `source`, `type`, `time`, `datacontenttype`, `data`
- [ ] TaskCreated event includes full task data with priority, tags, recurrence
- [ ] TaskUpdated event includes changed fields with old/new values
- [ ] TaskCompleted event includes task_id, user_id, completed_at
- [ ] TaskDeleted event includes task_id, user_id
- [ ] ReminderTriggered event includes reminder_id, task_id, due_date
- [ ] RecurringTaskScheduled event includes source_task_id, new_task_id, scheduled_for
- [ ] All event schemas have unique type identifiers (e.g., `com.todo.task.created`)

---

### Phase C: Dapr Integration (Backend)

**Goal**: Integrate Dapr Python SDK into Backend service for event publishing and secrets retrieval.

**Inputs**:
- Event schemas from Phase B
- Dapr Python SDK documentation
- Existing Backend service

**Outputs**:
- Dapr client wrapper module
- Event publisher service
- Updated MCP tools with event emission
- Secrets retrieval via Dapr (replacing env vars)

**Dependencies**: Phase B (needs event schemas)

**Acceptance Criteria**:
- [ ] `DaprClient` initialized on app startup
- [ ] Event publisher publishes to `tasks` topic after each task operation
- [ ] MCP tools emit events after successful database operations
- [ ] Secrets (JWT_SECRET, DATABASE_URL) retrieved via Dapr Secrets API
- [ ] Events published with CloudEvents format
- [ ] Application works with or without Dapr sidecar (graceful fallback for local dev)

---

### Phase D: Scheduler Service Creation

**Goal**: Create new Scheduler service that handles recurring tasks and reminders.

**Inputs**:
- Event schemas from Phase B
- Dapr component specifications
- Recurring task requirements (spec Section 4, User Story 4-5)

**Outputs**:
- New `scheduler/` directory with FastAPI application
- Event subscription endpoints for task lifecycle events
- Cron binding trigger endpoints
- State store operations for schedule persistence
- Event publishing for ReminderTriggered and RecurringTaskScheduled
- Dockerfile for containerization

**Dependencies**: Phase C (needs event publishing infrastructure)

**Acceptance Criteria**:
- [ ] Scheduler service starts and registers with Dapr
- [ ] Subscribes to `tasks` topic (TaskCreated, TaskUpdated, TaskCompleted, TaskDeleted)
- [ ] Handles `/triggers/recurring` endpoint (cron binding)
- [ ] Handles `/triggers/reminders` endpoint (cron binding)
- [ ] Stores recurring schedules in Dapr State Store (key: `recurring:{task_id}`)
- [ ] Stores reminder state in Dapr State Store (key: `reminder:{reminder_id}`)
- [ ] Publishes ReminderTriggered to `notifications` topic
- [ ] Publishes RecurringTaskScheduled to `tasks` topic
- [ ] Implements idempotency using event IDs

---

### Phase E: Backend Event Subscriptions

**Goal**: Enable Backend service to consume events from Scheduler.

**Inputs**:
- ReminderTriggered and RecurringTaskScheduled event schemas
- Backend existing database operations

**Outputs**:
- Event subscription endpoints in Backend
- RecurringTaskScheduled handler (creates new task in DB)
- ReminderTriggered handler (updates task metadata)

**Dependencies**: Phase D (needs Scheduler to publish events)

**Acceptance Criteria**:
- [ ] Backend subscribes to `notifications` topic (ReminderTriggered)
- [ ] Backend subscribes to `tasks` topic for RecurringTaskScheduled events
- [ ] ReminderTriggered creates notification record (or logs for now)
- [ ] RecurringTaskScheduled creates new Task in PostgreSQL
- [ ] Newly created tasks emit TaskCreated events (completing the cycle)
- [ ] Idempotency prevents duplicate task creation from replayed events

---

### Phase F: Local Kubernetes Deployment (Minikube + Dapr)

**Goal**: Deploy complete event-driven system on Minikube with Dapr.

**Inputs**:
- Backend and Scheduler services from Phases C-E
- Existing Helm chart structure
- Dapr component YAML specifications

**Outputs**:
- Dapr installation on Minikube
- Redis deployment (Pub/Sub + State Store)
- Extended Helm chart with scheduler, redis, dapr-components
- Updated backend deployment with Dapr annotations
- Kubernetes Secrets for sensitive config
- Cron binding manifests

**Dependencies**: Phase E (all services functional)

**Acceptance Criteria**:
- [ ] `dapr init -k` succeeds on Minikube
- [ ] Redis deployed and accessible within cluster
- [ ] Dapr Pub/Sub component configured with Redis
- [ ] Dapr State Store component configured with Redis
- [ ] Dapr Secrets component configured with Kubernetes Secrets
- [ ] Dapr Cron bindings configured (recurring-task-trigger, reminder-check-trigger)
- [ ] Backend deployment includes Dapr annotations (`dapr.io/enabled: true`)
- [ ] Scheduler deployment includes Dapr annotations
- [ ] `helm install` completes without errors
- [ ] All pods reach Running state within 5 minutes

---

### Phase G: End-to-End Validation

**Goal**: Verify complete event-driven flow works correctly.

**Inputs**:
- Deployed system from Phase F
- Acceptance scenarios from spec (Section 4)

**Outputs**:
- Validation test results
- Debugging documentation (if issues found)

**Dependencies**: Phase F (complete deployment)

**Acceptance Criteria**:
- [ ] Create task with priority → TaskCreated event observed
- [ ] Update task → TaskUpdated event observed
- [ ] Complete task → TaskCompleted event observed, reminders cancelled
- [ ] Delete task → TaskDeleted event observed, schedules removed
- [ ] Create recurring task → Scheduler receives and stores schedule
- [ ] Wait for cron trigger → RecurringTaskScheduled event, new task created
- [ ] Set reminder → Scheduler receives and stores reminder
- [ ] Wait for reminder time → ReminderTriggered event observed
- [ ] Search and filter work with extended fields
- [ ] System recovers from single pod restart

---

## Event-Driven Flow Planning

### User Actions → Events

| User Action | Endpoint | Event Emitted | Topic |
|-------------|----------|---------------|-------|
| Create task | POST /api/tasks | TaskCreated | tasks |
| Update task | PATCH /api/tasks/{id} | TaskUpdated | tasks |
| Complete task | POST /api/tasks/{id}/complete | TaskCompleted | tasks |
| Delete task | DELETE /api/tasks/{id} | TaskDeleted | tasks |
| Create recurring task | POST /api/tasks (with recurrence) | TaskCreated (with recurrence data) | tasks |
| Set reminder | PATCH /api/tasks/{id} (with reminders) | TaskUpdated (with reminders data) | tasks |

### Service Subscriptions

| Service | Topic | Event Types Handled |
|---------|-------|---------------------|
| Scheduler | tasks | TaskCreated, TaskUpdated, TaskCompleted, TaskDeleted |
| Backend | tasks | RecurringTaskScheduled |
| Backend | notifications | ReminderTriggered |

### Incremental Pub/Sub Introduction

**Step 1** (Phase C): Backend publishes TaskCreated events only
- Verify events appear in Redis Streams
- No consumers yet

**Step 2** (Phase D): Scheduler subscribes to TaskCreated
- Verify scheduler receives events
- Add TaskUpdated, TaskCompleted, TaskDeleted subscriptions

**Step 3** (Phase D): Scheduler publishes ReminderTriggered
- Test with manual cron trigger
- Verify event appears in notifications topic

**Step 4** (Phase E): Backend subscribes to ReminderTriggered
- Complete the event cycle
- Test full flow

### Synchronous Logic Refactoring

**Current (Synchronous)**:
```
User → API → Database → Response
```

**Target (Event-Driven)**:
```
User → API → Database → Response
              ↓
         Publish Event → Dapr Pub/Sub → Scheduler (async)
                                            ↓
                                     State Store update
```

**Key Principle**: The synchronous user request path remains unchanged. Event publishing is **fire-and-forget** after successful database operation. This ensures:
- No user-facing latency increase
- Eventual consistency for cross-service state
- Graceful degradation if Dapr unavailable

---

## Dapr Component Planning

### Pub/Sub Component

**When Introduced**: Phase C (Backend event publishing)

**Why Introduced**: Enables decoupled, asynchronous communication between Backend and Scheduler without direct service dependencies.

**What It Replaces**: Nothing (new capability). Without Dapr, would require custom message broker integration code.

**Validation Strategy**:
1. Deploy Pub/Sub component YAML
2. Use `dapr publish` CLI to send test event
3. Verify event appears in Redis Streams (`redis-cli XREAD`)
4. Subscribe test endpoint, verify delivery

**Component Configuration**:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
  namespace: todo-app
spec:
  type: pubsub.redis
  version: v1
  metadata:
    - name: redisHost
      value: redis-svc.todo-app.svc.cluster.local:6379
    - name: redisPassword
      value: ""
```

---

### State Store Component

**When Introduced**: Phase D (Scheduler service creation)

**Why Introduced**: Provides persistent storage for scheduler metadata (recurring schedules, reminder state) without introducing another database.

**What It Replaces**: Would otherwise require PostgreSQL tables in Scheduler service, creating database coupling.

**Validation Strategy**:
1. Deploy State Store component YAML
2. Use `dapr invoke` to save test state
3. Verify key exists in Redis (`redis-cli GET`)
4. Retrieve state, verify round-trip

**Component Configuration**:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
  namespace: todo-app
spec:
  type: state.redis
  version: v1
  metadata:
    - name: redisHost
      value: redis-svc.todo-app.svc.cluster.local:6379
    - name: redisPassword
      value: ""
    - name: actorStateStore
      value: "false"
```

---

### Bindings Component (Cron)

**When Introduced**: Phase D (Scheduler cron triggers)

**Why Introduced**: Provides time-based triggers for recurring task checks and reminder checks without implementing custom scheduler logic.

**What It Replaces**: Would otherwise require APScheduler or Celery beat for cron-like scheduling.

**Validation Strategy**:
1. Deploy Cron binding with short interval (e.g., every 30 seconds for testing)
2. Check Scheduler logs for trigger invocation
3. Verify trigger payload contains expected data
4. Restore production interval (every minute)

**Component Configuration**:
```yaml
# recurring-task-trigger.yaml
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
    - name: route
      value: /triggers/recurring
  scopes:
    - scheduler

# reminder-check-trigger.yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: reminder-check-trigger
  namespace: todo-app
spec:
  type: bindings.cron
  version: v1
  metadata:
    - name: schedule
      value: "@every 1m"
    - name: route
      value: /triggers/reminders
  scopes:
    - scheduler
```

---

### Secrets Component

**When Introduced**: Phase C (Backend secrets retrieval)

**Why Introduced**: Provides runtime secrets retrieval without mounting files or environment variables, enabling secret rotation without pod restart.

**What It Replaces**: Environment variable injection from Kubernetes Secrets.

**Validation Strategy**:
1. Create Kubernetes Secret with test value
2. Deploy Secrets component YAML
3. Use `dapr invoke` to retrieve secret
4. Verify correct value returned
5. Update secret, verify new value retrieved (no restart)

**Component Configuration**:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kubernetes-secrets
  namespace: todo-app
spec:
  type: secretstores.kubernetes
  version: v1
```

---

### Service Invocation Component

**When Introduced**: Phase D (Scheduler → Backend communication)

**Why Introduced**: Enables synchronous inter-service calls with automatic retries, timeouts, and service discovery.

**What It Replaces**: Direct HTTP calls to ClusterIP service (still works but without retry logic).

**Validation Strategy**:
1. Deploy both services with Dapr sidecars
2. Call Backend health endpoint via `dapr invoke --app-id backend --method health`
3. From Scheduler, invoke Backend using Dapr client
4. Verify request received and response returned

**Usage Example**:
```python
# In Scheduler service
from dapr.clients import DaprClient

with DaprClient() as d:
    response = d.invoke_method(
        app_id="backend",
        method_name="api/tasks/123",
        http_verb="GET"
    )
```

---

## Local Deployment Plan (Minikube)

### Prerequisites

```bash
# Required tools with versions
minikube version >= 1.30.0
kubectl version >= 1.28.0
helm version >= 3.12.0
dapr version >= 1.12.0
docker version >= 24.0.0
```

### Step 1: Minikube Setup

```bash
# Start Minikube with adequate resources
minikube start --cpus=4 --memory=8192 --driver=docker

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

### Step 2: Dapr Installation

```bash
# Initialize Dapr on Kubernetes
dapr init -k --wait

# Verify Dapr control plane
dapr status -k

# Expected output:
#   NAME                   NAMESPACE    HEALTHY  STATUS   REPLICAS
#   dapr-operator          dapr-system  True     Running  1
#   dapr-sentry            dapr-system  True     Running  1
#   dapr-placement-server  dapr-system  True     Running  1
#   dapr-sidecar-injector  dapr-system  True     Running  1
```

### Step 3: Namespace and Secrets

```bash
# Create application namespace
kubectl create namespace todo-app

# Create Kubernetes secrets
kubectl create secret generic app-secrets \
  --from-literal=jwt-secret=your-local-dev-secret-minimum-32-chars \
  --from-literal=database-url=postgresql://user:pass@host:5432/db \
  -n todo-app
```

### Step 4: Helm Chart Deployment Order

1. **Redis** (no dependencies)
2. **Dapr Components** (depends on Redis)
3. **Backend** (depends on Dapr components)
4. **Scheduler** (depends on Dapr components)
5. **Frontend** (depends on Backend)

```bash
# Single Helm install handles ordering via dependencies
helm install todo-chatbot ./helm/todo-chatbot \
  -f ./helm/todo-chatbot/values-local.yaml \
  -n todo-app

# Monitor rollout
kubectl rollout status deployment/backend -n todo-app
kubectl rollout status deployment/scheduler -n todo-app
```

### Step 5: Verification

```bash
# Check all pods running
kubectl get pods -n todo-app

# Check Dapr sidecars injected
kubectl get pods -n todo-app -o jsonpath='{range .items[*]}{.metadata.name}{": "}{range .spec.containers[*]}{.name}{" "}{end}{"\n"}{end}'

# Verify Dapr components
dapr components -n todo-app

# Access Dapr dashboard
dapr dashboard -k
```

### Helm vs Manifest Decision

**Decision**: Use Helm with templated manifests

**Rationale**:
- Existing Helm chart provides foundation
- Values files enable local vs production configuration
- Templating avoids duplication (e.g., namespace, labels)
- Single `helm install` deploys entire stack

**Structure**:
- Dapr component YAMLs under `templates/dapr-components/`
- All resources share `values.yaml` configuration
- `values-local.yaml` overrides for Minikube specifics

### Rollback Strategy

```bash
# If deployment fails
helm rollback todo-chatbot 1 -n todo-app

# If Dapr issues
dapr uninstall -k
# Fix issues, then:
dapr init -k --wait

# If complete reset needed
helm uninstall todo-chatbot -n todo-app
kubectl delete namespace todo-app
dapr uninstall -k
# Start from Step 1
```

---

## Validation & Checkpoints

### Checkpoint A: Model Extensions Complete

**Manual Validation Steps**:
1. Run database migration: `alembic upgrade head`
2. Create task via API with priority and tags
3. Verify fields persisted: `SELECT * FROM tasks WHERE id = ...`
4. Update task via MCP tool with new fields
5. Run existing test suite: `pytest tests/`

**Stop & Fix Conditions**:
- Any existing test fails → Fix before proceeding
- Migration fails → Debug migration, do not modify application code
- API rejects valid priority/tags → Fix schema validation

---

### Checkpoint B: Event Schemas Validated

**Manual Validation Steps**:
1. Import event models in Python REPL
2. Create sample TaskCreated event, serialize to JSON
3. Validate JSON against CloudEvents spec (check required fields)
4. Deserialize back, verify round-trip

**Stop & Fix Conditions**:
- Event missing required CloudEvents fields → Add fields
- Serialization loses data → Fix Pydantic model

---

### Checkpoint C: Backend Publishes Events

**Manual Validation Steps**:
1. Start Backend locally with Dapr sidecar: `dapr run --app-id backend ...`
2. Create task via API
3. Check Redis Streams: `redis-cli XRANGE tasks - + COUNT 10`
4. Verify TaskCreated event in stream

**Stop & Fix Conditions**:
- No event in Redis → Check Dapr logs, verify pubsub component
- Event malformed → Fix event serialization
- Sidecar not injecting → Check Dapr annotations

---

### Checkpoint D: Scheduler Receives Events

**Manual Validation Steps**:
1. Start Scheduler with Dapr sidecar
2. Create task via Backend
3. Check Scheduler logs: `kubectl logs deployment/scheduler -n todo-app`
4. Verify "TaskCreated received" log message
5. Check State Store: `redis-cli GET scheduler||recurring::{task_id}`

**Stop & Fix Conditions**:
- Event not received → Check subscription endpoint, topic name
- State not saved → Check statestore component, key format
- Cron not triggering → Check binding schedule, scopes

---

### Checkpoint E: Full Event Cycle Works

**Manual Validation Steps**:
1. Create recurring task (daily recurrence)
2. Wait for cron trigger (max 2 minutes)
3. Verify RecurringTaskScheduled event published
4. Verify new task instance in PostgreSQL
5. Verify TaskCreated event for new instance

**Stop & Fix Conditions**:
- RecurringTaskScheduled not published → Debug scheduler trigger handler
- Task not created in DB → Check Backend subscription handler
- TaskCreated not emitted → Check Backend event publishing

---

### Checkpoint F: Minikube Deployment Healthy

**Manual Validation Steps**:
1. All pods Running: `kubectl get pods -n todo-app`
2. Dapr sidecars present: Check container count (should be 2 for backend, scheduler)
3. Services accessible: `kubectl get svc -n todo-app`
4. Frontend reachable: `minikube service frontend-svc -n todo-app`
5. API health: `curl http://$(minikube ip):30080/api/health`

**Stop & Fix Conditions**:
- Pod CrashLoopBackOff → Check logs, fix application error
- ImagePullBackOff → Verify image built, pushed to Minikube registry
- Sidecar not injected → Check namespace labels, Dapr installation

---

### Checkpoint G: Acceptance Scenarios Pass

**Manual Validation Steps**:
1. Execute each acceptance scenario from spec Section 4
2. Use Dapr Dashboard to observe events
3. Use Redis CLI to verify state store entries
4. Document any deviations

**Stop & Fix Conditions**:
- User story fails → Debug specific component
- Performance outside bounds → Profile and optimize
- Events not idempotent → Fix consumer logic

---

## Risk & Complexity Control

### High-Risk Steps

| Step | Risk | Mitigation |
|------|------|------------|
| Dapr sidecar injection | Pod may not start if sidecar fails | Test with single service first; check Dapr logs immediately |
| Database migration | May break existing data | Backup before migration; test on empty DB first |
| Event subscription wiring | Topic/route mismatch causes silent failure | Use Dapr Dashboard to verify subscriptions |
| Cron binding scheduling | Misconfigured schedule may not trigger | Start with 30s interval for testing, verify triggers |
| Secrets retrieval | Missing secret causes startup failure | Create secrets before deploying services |

### First-Time Concepts

| Concept | Learning Strategy |
|---------|-------------------|
| Dapr Pub/Sub | Start with CLI (`dapr publish`), then SDK |
| Dapr State Store | Use Dapr Dashboard to inspect state |
| Cron bindings | Test with short intervals first |
| CloudEvents | Use online validator before implementing |
| Service Invocation | Test with `dapr invoke` CLI first |

### Gradual Complexity Introduction

1. **Week 1**: Model extensions + event schemas (no Dapr yet)
2. **Week 2**: Backend event publishing (Dapr Pub/Sub only)
3. **Week 3**: Scheduler service (add State Store, Bindings)
4. **Week 4**: Backend subscriptions (complete event cycle)
5. **Week 5**: Kubernetes deployment (add Secrets, finalize)

### Local Debugging Toolkit

| Issue | Debug Tool | Command |
|-------|-----------|---------|
| Events not published | Dapr sidecar logs | `kubectl logs <pod> -c daprd` |
| Events not received | Dapr Dashboard | `dapr dashboard -k` |
| State not persisted | Redis CLI | `kubectl exec redis -- redis-cli KEYS "*"` |
| Cron not triggering | Binding logs | `kubectl logs <pod> -c daprd \| grep binding` |
| Secrets not found | Dapr CLI | `dapr invoke --app-id backend --method dapr/secrets/kubernetes-secrets/app-secrets` |
| Service invocation fails | Dapr traces | Check sidecar logs for retry/timeout |

---

## Final Deliverables

### Specification Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Feature Specification | `specs/009-dapr-event-driven/spec.md` | ✅ Complete |
| Implementation Plan | `specs/009-dapr-event-driven/plan.md` | ✅ This document |
| Research Document | `specs/009-dapr-event-driven/research.md` | 📋 Phase 0 |
| Data Model | `specs/009-dapr-event-driven/data-model.md` | 📋 Phase 1 |
| Event Contracts | `specs/009-dapr-event-driven/contracts/events.yaml` | 📋 Phase 1 |
| Scheduler API | `specs/009-dapr-event-driven/contracts/scheduler-api.yaml` | 📋 Phase 1 |
| Quickstart Guide | `specs/009-dapr-event-driven/quickstart.md` | 📋 Phase 1 |
| Tasks | `specs/009-dapr-event-driven/tasks.md` | 📋 Phase 2 (/sp.tasks) |

### Code Changes

| Change | Location | Type |
|--------|----------|------|
| Task model extension | `backend/src/models/task.py` | Modify |
| Reminder model | `backend/src/models/reminder.py` | New |
| Recurrence model | `backend/src/models/recurrence.py` | New |
| Event schemas | `backend/src/events/schemas.py` | New |
| Event publisher | `backend/src/events/publisher.py` | New |
| Dapr client wrapper | `backend/src/dapr/client.py` | New |
| Task routes (event emit) | `backend/src/api/routes/tasks.py` | Modify |
| Event subscription routes | `backend/src/api/routes/events.py` | New |
| MCP tools (event emit) | `backend/src/mcp_server/tools/*.py` | Modify |
| Scheduler service | `scheduler/` | New directory |

### Kubernetes/Dapr Configurations

| Config | Path | Type |
|--------|------|------|
| Pub/Sub component | `helm/todo-chatbot/templates/dapr-components/pubsub.yaml` | New |
| State Store component | `helm/todo-chatbot/templates/dapr-components/statestore.yaml` | New |
| Secrets component | `helm/todo-chatbot/templates/dapr-components/secrets.yaml` | New |
| Cron bindings | `helm/todo-chatbot/templates/dapr-components/bindings.yaml` | New |
| Backend deployment | `helm/todo-chatbot/templates/backend/deployment.yaml` | Modify |
| Scheduler deployment | `helm/todo-chatbot/templates/scheduler/deployment.yaml` | New |
| Scheduler service | `helm/todo-chatbot/templates/scheduler/service.yaml` | New |
| Redis deployment | `helm/todo-chatbot/templates/redis/deployment.yaml` | New |
| Redis service | `helm/todo-chatbot/templates/redis/service.yaml` | New |
| Local values | `helm/todo-chatbot/values-local.yaml` | Modify |

---

## Scope Boundaries

### In Scope (Phase V - Part 1)

- ✅ Task model extensions (priority, tags, recurrence, reminders)
- ✅ Event-driven architecture with Dapr Pub/Sub
- ✅ Scheduler service for recurring tasks and reminders
- ✅ All 5 Dapr building blocks
- ✅ Local Minikube deployment
- ✅ Helm chart extensions
- ✅ Manual validation procedures

### Deferred to Phase V - Part 2

- ❌ Cloud provider deployment (AKS, GKE, OCI, AWS)
- ❌ Managed Kafka services (Confluent, Redpanda Cloud, Amazon MSK)
- ❌ CI/CD pipeline integration (GitHub Actions, GitLab CI)
- ❌ Monitoring stacks (Prometheus, Grafana, Jaeger)
- ❌ Production scaling (HPA, load balancing)
- ❌ Ingress controllers (NGINX, Traefik)
- ❌ TLS/HTTPS certificate management
- ❌ Multi-cluster deployment
- ❌ Real-time notifications (WebSocket/SSE)
- ❌ Email/push notification delivery

---

## Complexity Tracking

> No constitution violations detected. Architecture follows all principles.

| Consideration | Justification |
|---------------|---------------|
| New Scheduler microservice | Required for time-based triggers; cannot be added to stateless Backend |
| Redis infrastructure | Single component serves both Pub/Sub and State Store; simpler than separate systems |
| Dapr sidecars | Mandatory for Dapr functionality; adds container but simplifies application code |
| Event-driven pattern | Explicitly requested in spec; enables decoupling and future scaling |

---

**Plan Status**: Ready for Phase 0 research and Phase 1 design artifacts.
