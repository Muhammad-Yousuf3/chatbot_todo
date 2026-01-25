# Feature Specification: Phase V Part 1 - Cloud-Native Event-Driven Todo Chatbot

**Feature Branch**: `009-dapr-event-driven`
**Created**: 2026-01-20
**Status**: Draft
**Input**: User description: "Transform Todo Chatbot into cloud-native event-driven application using Dapr building blocks and local Minikube deployment"

---

## 1. Objective & Non-Goals

### Objective

Transform the existing Todo Chatbot into a **cloud-native, event-driven application** that:

1. Uses **message-based communication** for decoupled service interactions
2. Leverages **Dapr building blocks** for vendor-agnostic infrastructure abstraction
3. Deploys locally on **Minikube** for development and validation
4. Adds **intermediate and advanced task management features** (priorities, tags, recurring tasks, reminders)

This phase focuses on **architecture correctness**, not production scale.

### Non-Goals (Explicitly Out of Scope)

The following are **NOT** part of Phase V Part 1:

- **Cloud Providers**: No AKS, GKE, OCI, AWS, or any managed cloud service
- **Managed Message Brokers**: No Confluent Cloud, Redpanda Cloud, Amazon MSK
- **CI/CD Pipelines**: No GitHub Actions, GitLab CI, Jenkins, or automated deployment
- **Monitoring Stacks**: No Prometheus, Grafana, Jaeger, or OpenTelemetry collectors
- **Production Scaling**: No horizontal pod autoscaling, load balancing strategies
- **Ingress Controllers**: No NGINX Ingress, Traefik, or Ambassador
- **TLS/HTTPS**: No certificate management or encrypted traffic
- **Multi-cluster deployment**: Single Minikube cluster only

> **Cloud deployment is deferred to Phase V – Part 2**

---

## 2. Vocabulary Definitions

The following terms are used throughout this specification:

| Term              | Definition                                                                                                                                                                                                                  |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Event**         | An immutable record of something that happened in the system at a specific point in time. Events are facts, not commands. Example: "TaskCreated" means a task was created, not a request to create one.                    |
| **Pub/Sub**       | A messaging pattern where publishers emit events to topics without knowing who consumes them, and subscribers receive events from topics without knowing who published them. Enables loose coupling.                        |
| **Binding**       | A Dapr component that connects the application to external systems (input bindings trigger the app, output bindings let the app trigger external systems). Cron binding is a time-based input binding.                      |
| **State Store**   | A key-value storage abstraction that persists data with consistency guarantees. Used for storing scheduler metadata and reminder state.                                                                                     |
| **Sidecar**       | A Dapr process that runs alongside each application container, handling infrastructure concerns (messaging, state, secrets) so the app code remains simple.                                                                 |
| **Service Invocation** | Direct synchronous communication between services through Dapr, with built-in retry, timeout, and service discovery.                                                                                                   |

---

## 3. Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MINIKUBE CLUSTER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         DAPR CONTROL PLANE                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │   Dapr      │  │   Dapr      │  │   Dapr      │  │   Dapr     │  │   │
│  │  │  Operator   │  │   Sentry    │  │  Placement  │  │ Dashboard  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────┐          ┌──────────────────────┐                │
│  │   BACKEND SERVICE    │          │  SCHEDULER SERVICE   │                │
│  │  ┌────────────────┐  │          │  ┌────────────────┐  │                │
│  │  │   Backend App  │  │          │  │  Scheduler App │  │                │
│  │  └───────┬────────┘  │          │  └───────┬────────┘  │                │
│  │          │           │          │          │           │                │
│  │  ┌───────┴────────┐  │          │  ┌───────┴────────┐  │                │
│  │  │  Dapr Sidecar  │  │          │  │  Dapr Sidecar  │  │                │
│  │  └───────┬────────┘  │          │  └───────┬────────┘  │                │
│  └──────────┼───────────┘          └──────────┼───────────┘                │
│             │                                 │                             │
│             │         PUB/SUB BROKER          │                             │
│             │  ┌──────────────────────────┐   │                             │
│             └──┤    Redis (In-Memory)     ├───┘                             │
│                │    Message Broker        │                                 │
│                └──────────────────────────┘                                 │
│                                                                             │
│  ┌──────────────────────┐          ┌──────────────────────┐                │
│  │  FRONTEND SERVICE    │          │     STATE STORE      │                │
│  │  ┌────────────────┐  │          │  ┌────────────────┐  │                │
│  │  │  Frontend App  │  │          │  │     Redis      │  │                │
│  │  └────────────────┘  │          │  │  (Key-Value)   │  │                │
│  └──────────────────────┘          └──────────────────────┘                │
│                                                                             │
│  ┌──────────────────────┐          ┌──────────────────────┐                │
│  │    SECRET STORE      │          │   CRON BINDINGS      │                │
│  │  ┌────────────────┐  │          │  ┌────────────────┐  │                │
│  │  │   Kubernetes   │  │          │  │ Recurring Task │  │                │
│  │  │    Secrets     │  │          │  │   Scheduler    │  │                │
│  │  └────────────────┘  │          │  │ Reminder Check │  │                │
│  └──────────────────────┘          └──────────────────────┘                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          DATABASE                                    │   │
│  │                    PostgreSQL (External)                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Responsibilities

| Service               | Responsibility                                                                                                                           |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Backend Service**   | Handles all task CRUD operations, user authentication (JWT), emits task lifecycle events, responds to reminder notifications             |
| **Scheduler Service** | Manages recurring task scheduling, processes due date reminders, consumes cron binding triggers, maintains scheduler state               |
| **Frontend Service**  | Provides user interface, calls backend through Minikube NodePort/port-forward                                                            |

---

## 4. User Scenarios & Testing

### User Story 1 - Task Priority Management (Priority: P1)

A user needs to organize tasks by importance to focus on what matters most.

**Why this priority**: Priority is a fundamental organizational feature that affects how users view and manage all tasks. It's core to the task management experience.

**Independent Test**: Can be tested by creating tasks with different priorities and verifying they display and filter correctly.

**Acceptance Scenarios**:

1. **Given** a user is creating a new task, **When** they select a priority level (high/medium/low), **Then** the task is created with that priority and displays a visual indicator
2. **Given** a user has multiple tasks, **When** they filter by "high priority", **Then** only high-priority tasks are displayed
3. **Given** a user has a task, **When** they change its priority, **Then** a TaskUpdated event is emitted and the change persists

---

### User Story 2 - Tag-Based Organization (Priority: P1)

A user needs to categorize tasks with tags for flexible organization.

**Why this priority**: Tags enable cross-cutting organization that complements priority. Essential for users managing diverse task types.

**Independent Test**: Can be tested by adding tags to tasks and filtering/searching by tag.

**Acceptance Scenarios**:

1. **Given** a user is creating a task, **When** they add one or more tags, **Then** the task is saved with those tags
2. **Given** a user has tasks with various tags, **When** they filter by a specific tag, **Then** only tasks with that tag are shown
3. **Given** a user wants to find tasks, **When** they search by tag name, **Then** matching tasks are returned

---

### User Story 3 - Task Search and Filtering (Priority: P1)

A user needs to quickly find specific tasks among many.

**Why this priority**: Search and filter are essential usability features that become critical as task volume grows.

**Independent Test**: Can be tested by creating multiple tasks and using search/filter to locate specific ones.

**Acceptance Scenarios**:

1. **Given** a user has many tasks, **When** they search by keyword in task title or description, **Then** matching tasks are returned within 2 seconds
2. **Given** a user wants to see incomplete tasks, **When** they filter by status "pending", **Then** only pending tasks are shown
3. **Given** a user wants organized results, **When** they sort by due date, **Then** tasks are ordered by due date ascending

---

### User Story 4 - Recurring Task Scheduling (Priority: P2)

A user needs tasks that automatically recreate on a schedule (daily, weekly, custom).

**Why this priority**: Recurring tasks are advanced but highly valuable for routine task management. Depends on core task features being stable.

**Independent Test**: Can be tested by creating a recurring task, waiting for schedule trigger, and verifying new task instance is created.

**Acceptance Scenarios**:

1. **Given** a user creates a task with daily recurrence, **When** the scheduled time occurs, **Then** a new instance of the task is created and RecurringTaskScheduled event is emitted
2. **Given** a user has a weekly recurring task, **When** the task completes, **Then** the recurrence schedule remains active for the next occurrence
3. **Given** a user wants custom recurrence, **When** they specify a cron expression (e.g., "every Monday and Wednesday"), **Then** the system schedules accordingly

---

### User Story 5 - Due Date Reminders (Priority: P2)

A user needs notifications before tasks are due to avoid missing deadlines.

**Why this priority**: Reminders prevent missed deadlines and improve task completion rates. Requires scheduler infrastructure.

**Independent Test**: Can be tested by creating a task with a due date and reminder, then verifying notification is triggered at the correct time.

**Acceptance Scenarios**:

1. **Given** a user sets a due date with a reminder (e.g., 1 hour before), **When** that time arrives, **Then** a ReminderTriggered event is emitted and the user is notified
2. **Given** a task has multiple reminders configured, **When** each reminder time occurs, **Then** each reminder is triggered independently
3. **Given** a user marks a task complete, **When** a reminder was scheduled, **Then** pending reminders for that task are cancelled

---

### User Story 6 - Event-Driven Task Lifecycle (Priority: P2)

The system must emit events for all task state changes to enable decoupled processing.

**Why this priority**: Event emission is the foundation of the event-driven architecture. All future integrations depend on it.

**Independent Test**: Can be tested by performing task operations and verifying corresponding events appear in the message broker.

**Acceptance Scenarios**:

1. **Given** a user creates a task, **When** the task is persisted, **Then** a TaskCreated event is published with task details
2. **Given** a user completes a task, **When** status changes to "completed", **Then** a TaskCompleted event is published
3. **Given** a user deletes a task, **When** deletion succeeds, **Then** a TaskDeleted event is published

---

### Edge Cases

- What happens when a recurring task's cron expression is invalid? System rejects with validation error.
- How does the system handle reminder triggers when the backend is temporarily unavailable? Events are retained in the message broker and processed when backend recovers.
- What happens when a user deletes a task that has pending reminders? All pending reminders for that task are cancelled.
- How does the system handle duplicate event processing? Consumers implement idempotency using event IDs.
- What happens when the state store is unavailable? Scheduler service enters degraded mode; existing schedules continue based on in-memory state.

---

## 5. Event Model & Event Flow

### What is an Event?

In this system, an **event** is:
- An **immutable fact** about something that happened
- Contains a **timestamp** and **unique identifier**
- Carries all data needed for consumers to act without callbacks
- Published to a **topic** in the pub/sub broker
- Consumed by one or more services asynchronously

### Event Catalog

| Event Type              | Trigger                         | Topic           | Producers | Consumers                              |
| ----------------------- | ------------------------------- | --------------- | --------- | -------------------------------------- |
| TaskCreated             | User creates a task             | `tasks`         | Backend   | Scheduler (for recurring/reminders)    |
| TaskUpdated             | User modifies task              | `tasks`         | Backend   | Scheduler (if due date/recurrence changes) |
| TaskCompleted           | User marks task done            | `tasks`         | Backend   | Scheduler (cancel reminders)           |
| TaskDeleted             | User deletes task               | `tasks`         | Backend   | Scheduler (remove schedules)           |
| ReminderTriggered       | Reminder time reached           | `notifications` | Scheduler | Backend (notify user)                  |
| RecurringTaskScheduled  | Recurring task instantiated     | `tasks`         | Scheduler | Backend (create new task instance)     |

### Event Flow Diagrams

**Flow 1: Task Creation with Recurring Schedule**

```
User → Frontend → Backend → [Persist Task] → Publish TaskCreated
                                                      ↓
                                               PUB/SUB (tasks topic)
                                                      ↓
                                               Scheduler Service
                                                      ↓
                                         [Parse recurrence, store in State Store]
                                                      ↓
                                         [Schedule cron binding trigger]
```

**Flow 2: Reminder Trigger**

```
Cron Binding (time trigger) → Scheduler Service
                                    ↓
                           [Check State Store for due reminders]
                                    ↓
                           [Publish ReminderTriggered event]
                                    ↓
                            PUB/SUB (notifications topic)
                                    ↓
                             Backend Service
                                    ↓
                           [Notify user via API response / WebSocket future]
```

**Flow 3: Recurring Task Instantiation**

```
Cron Binding (schedule trigger) → Scheduler Service
                                       ↓
                              [Check State Store for recurring tasks]
                                       ↓
                              [Publish RecurringTaskScheduled event]
                                       ↓
                               PUB/SUB (tasks topic)
                                       ↓
                                Backend Service
                                       ↓
                              [Create new task instance in DB]
                                       ↓
                              [Publish TaskCreated event]
```

### Event Payload Schemas

**TaskCreated Event**

```json
{
  "event_id": "uuid-v4",
  "event_type": "TaskCreated",
  "timestamp": "2026-01-20T10:30:00Z",
  "data": {
    "task_id": "uuid-v4",
    "user_id": "uuid-v4",
    "title": "string",
    "description": "string | null",
    "status": "pending | in_progress | completed",
    "priority": "high | medium | low",
    "tags": ["string"],
    "due_date": "ISO8601 | null",
    "reminders": [
      {
        "reminder_id": "uuid-v4",
        "trigger_at": "ISO8601"
      }
    ],
    "recurrence": {
      "type": "daily | weekly | custom",
      "cron_expression": "string | null",
      "next_occurrence": "ISO8601 | null"
    }
  }
}
```

**TaskUpdated Event**

```json
{
  "event_id": "uuid-v4",
  "event_type": "TaskUpdated",
  "timestamp": "ISO8601",
  "data": {
    "task_id": "uuid-v4",
    "user_id": "uuid-v4",
    "changes": {
      "field_name": {
        "old_value": "any",
        "new_value": "any"
      }
    }
  }
}
```

**TaskCompleted Event**

```json
{
  "event_id": "uuid-v4",
  "event_type": "TaskCompleted",
  "timestamp": "ISO8601",
  "data": {
    "task_id": "uuid-v4",
    "user_id": "uuid-v4",
    "completed_at": "ISO8601"
  }
}
```

**TaskDeleted Event**

```json
{
  "event_id": "uuid-v4",
  "event_type": "TaskDeleted",
  "timestamp": "ISO8601",
  "data": {
    "task_id": "uuid-v4",
    "user_id": "uuid-v4"
  }
}
```

**ReminderTriggered Event**

```json
{
  "event_id": "uuid-v4",
  "event_type": "ReminderTriggered",
  "timestamp": "ISO8601",
  "data": {
    "reminder_id": "uuid-v4",
    "task_id": "uuid-v4",
    "user_id": "uuid-v4",
    "task_title": "string",
    "due_date": "ISO8601"
  }
}
```

**RecurringTaskScheduled Event**

```json
{
  "event_id": "uuid-v4",
  "event_type": "RecurringTaskScheduled",
  "timestamp": "ISO8601",
  "data": {
    "source_task_id": "uuid-v4",
    "new_task_id": "uuid-v4",
    "user_id": "uuid-v4",
    "title": "string",
    "recurrence_type": "daily | weekly | custom",
    "scheduled_for": "ISO8601"
  }
}
```

---

## 6. Dapr Component Design

### Required Dapr Building Blocks

This specification uses **ALL** required Dapr building blocks:

#### 6.1 Pub/Sub Component

**Purpose**: Provides Kafka-style messaging abstraction for event-driven communication.

**Configuration**: Uses Redis Streams as the local broker (vendor-agnostic; swappable to Kafka, RabbitMQ, etc.)

**Topics**:
- `tasks` - All task lifecycle events (TaskCreated, TaskUpdated, TaskCompleted, TaskDeleted, RecurringTaskScheduled)
- `notifications` - Reminder and alert events (ReminderTriggered)

**Behavior**:
- At-least-once delivery guarantee
- Dead-letter queue for failed messages (local debugging)
- Consumer groups for horizontal scaling (future Phase V Part 2)

---

#### 6.2 State Store Component

**Purpose**: Persistent key-value storage for scheduler metadata.

**Use Cases**:
- Store recurring task schedules (key: `recurring:{task_id}`)
- Store reminder state (key: `reminder:{reminder_id}`)
- Store scheduler checkpoint data

**Configuration**: Uses Redis as state backend (consistent with pub/sub for simplicity in local deployment)

**Behavior**:
- Strong consistency for writes
- Supports TTL for automatic cleanup of stale data

---

#### 6.3 Bindings Component (Cron)

**Purpose**: Time-based triggers for scheduled operations.

**Bindings**:

1. **recurring-task-trigger**
   - Schedule: Every minute (checks for tasks due to recur)
   - Target: Scheduler Service `/triggers/recurring`

2. **reminder-check-trigger**
   - Schedule: Every minute (checks for reminders to fire)
   - Target: Scheduler Service `/triggers/reminders`

**Behavior**:
- Triggers are inputs that invoke HTTP endpoints on the service
- Scheduler service processes triggers and emits events as needed

---

#### 6.4 Secrets Component

**Purpose**: Secure storage and retrieval of sensitive configuration.

**Secrets Managed**:
- `jwt-secret` - Secret key for JWT token signing
- `database-url` - PostgreSQL connection string (Neon or local)
- `api-keys` - Any external API keys (if applicable)

**Configuration**: Uses Kubernetes Secrets as the backend (native to Minikube)

**Behavior**:
- Secrets are fetched at runtime via Dapr sidecar
- Application code never reads secrets from files or environment directly
- Supports secret rotation (future enhancement)

---

#### 6.5 Service Invocation Component

**Purpose**: Direct synchronous communication between services.

**Use Cases**:
- Scheduler → Backend: Request task details when processing recurrence
- Backend → Scheduler: Query schedule status (health checks)

**Behavior**:
- Automatic service discovery via Dapr naming
- Built-in retries with exponential backoff
- Timeout configuration per call

---

## 7. Local Deployment Architecture (Minikube)

### Deployment Target

**Platform**: Minikube (single-node Kubernetes cluster for local development)

**Prerequisites**:
- Minikube installed and running
- kubectl configured
- Dapr CLI installed
- Helm 3.x installed

### Kubernetes Resources

#### Namespaces

- `todo-app` - Application workloads
- `dapr-system` - Dapr control plane (auto-created by Dapr install)

#### Deployments

| Deployment | Replicas | Image                 | Dapr Annotations                  |
| ---------- | -------- | --------------------- | --------------------------------- |
| backend    | 1        | `todo-backend:local`  | enabled, app-id: backend          |
| scheduler  | 1        | `todo-scheduler:local`| enabled, app-id: scheduler        |
| frontend   | 1        | `todo-frontend:local` | disabled (no Dapr needed)         |
| redis      | 1        | `redis:7-alpine`      | n/a (infrastructure)              |

#### Services

| Service       | Type      | Ports       |
| ------------- | --------- | ----------- |
| backend-svc   | ClusterIP | 8000        |
| scheduler-svc | ClusterIP | 8001        |
| frontend-svc  | NodePort  | 3000:30080  |
| redis-svc     | ClusterIP | 6379        |

#### ConfigMaps

- `dapr-components` - Dapr component YAML files
- `app-config` - Non-sensitive application configuration

#### Secrets

- `app-secrets` - JWT secret, database URL

### Helm Chart Structure

```
helm/
└── todo-chatbot/
    ├── Chart.yaml
    ├── values.yaml
    ├── values-local.yaml
    ├── templates/
    │   ├── namespace.yaml
    │   ├── backend-deployment.yaml
    │   ├── scheduler-deployment.yaml
    │   ├── frontend-deployment.yaml
    │   ├── redis-deployment.yaml
    │   ├── services.yaml
    │   ├── secrets.yaml
    │   ├── configmaps.yaml
    │   └── dapr-components/
    │       ├── pubsub.yaml
    │       ├── statestore.yaml
    │       ├── secrets.yaml
    │       └── bindings.yaml
    └── README.md
```

### Deployment Commands

```bash
# Start Minikube
minikube start --cpus=4 --memory=8192

# Install Dapr
dapr init -k

# Deploy application
helm install todo-chatbot ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml

# Access frontend
minikube service frontend-svc -n todo-app
```

---

## 8. Configuration & Secrets Strategy

### Configuration Hierarchy

1. **Default values** - Hardcoded in application
2. **ConfigMap values** - Override defaults
3. **Environment variables** - Override ConfigMap
4. **Secrets** - Sensitive values via Dapr secrets API

### Configuration Items

| Config Key       | Source      | Description                              |
| ---------------- | ----------- | ---------------------------------------- |
| `LOG_LEVEL`      | ConfigMap   | Logging verbosity (DEBUG, INFO, WARN)    |
| `DATABASE_URL`   | Secret      | PostgreSQL connection string             |
| `JWT_SECRET`     | Secret      | JWT signing key                          |
| `DAPR_HTTP_PORT` | Environment | Dapr sidecar HTTP port (default: 3500)   |
| `APP_PORT`       | Environment | Application HTTP port                    |
| `PUBSUB_NAME`    | ConfigMap   | Name of pub/sub component                |
| `STATESTORE_NAME`| ConfigMap   | Name of state store component            |

### Secrets Management

**For Local Development**:
- Secrets stored in Kubernetes Secrets
- Created via kubectl or Helm
- Accessed via Dapr secrets API

**Example Secret Creation**:
```bash
kubectl create secret generic app-secrets \
  --from-literal=jwt-secret=local-dev-secret-change-in-prod \
  --from-literal=database-url=postgresql://user:pass@host:5432/db \
  -n todo-app
```

---

## 9. Failure Scenarios & Local Debugging

### Failure Scenarios

| Scenario                  | Impact                                 | Mitigation                                                     |
| ------------------------- | -------------------------------------- | -------------------------------------------------------------- |
| Redis unavailable         | Pub/sub and state store fail           | Services return 503; events buffered in Dapr sidecar briefly   |
| Scheduler service down    | Reminders and recurring tasks not processed | Backend continues; events queue in Redis; processed on recovery |
| Backend service down      | API unavailable                        | Frontend shows error; scheduler events queue                   |
| Database unavailable      | Task CRUD fails                        | Backend returns 503; read-through cache if implemented         |
| Dapr sidecar crash        | Service loses Dapr capabilities        | Kubernetes restarts pod; brief service interruption            |

### Local Debugging Tools

| Tool            | Purpose                         | Usage                                                          |
| --------------- | ------------------------------- | -------------------------------------------------------------- |
| `dapr dashboard`| Visual Dapr component inspection| `dapr dashboard -k`                                            |
| `kubectl logs`  | Service and sidecar logs        | `kubectl logs -f deployment/backend -c backend -n todo-app`    |
| `kubectl exec`  | Interactive debugging           | `kubectl exec -it deployment/backend -- sh`                    |
| `dapr invoke`   | Test service invocation         | `dapr invoke --app-id backend --method health`                 |
| `dapr publish`  | Test pub/sub                    | `dapr publish --pubsub pubsub --topic tasks --data '{...}'`    |
| Redis CLI       | Inspect state/messages          | `kubectl exec -it deployment/redis -- redis-cli`               |

### Debugging Checklist

1. **Service not receiving events?**
   - Check Dapr sidecar logs for subscription errors
   - Verify topic name matches in publisher and subscriber
   - Confirm Dapr component is properly applied

2. **State not persisting?**
   - Verify state store component is configured
   - Check Redis connectivity
   - Inspect key format in Redis CLI

3. **Cron binding not triggering?**
   - Verify binding YAML schedule syntax
   - Check scheduler service endpoint is correct
   - Review Dapr sidecar logs for binding errors

---

## 10. Requirements

### Functional Requirements

#### Task Management (Core)

- **FR-001**: System MUST allow users to create tasks with title, optional description, priority (high/medium/low), and optional tags
- **FR-002**: System MUST allow users to update any task field (title, description, status, priority, tags, due date)
- **FR-003**: System MUST allow users to delete tasks
- **FR-004**: System MUST allow users to mark tasks as completed
- **FR-005**: System MUST persist all task data reliably

#### Search and Filter

- **FR-006**: System MUST allow users to search tasks by keyword (matching title or description)
- **FR-007**: System MUST allow users to filter tasks by status (pending, in_progress, completed)
- **FR-008**: System MUST allow users to filter tasks by priority
- **FR-009**: System MUST allow users to filter tasks by tag
- **FR-010**: System MUST allow users to sort tasks by due date, priority, or name

#### Due Dates and Reminders

- **FR-011**: System MUST allow users to set a due date on tasks
- **FR-012**: System MUST allow users to configure reminders (time before due date)
- **FR-013**: System MUST trigger reminders at the configured time
- **FR-014**: System MUST cancel pending reminders when a task is completed or deleted

#### Recurring Tasks

- **FR-015**: System MUST allow users to create recurring tasks with daily, weekly, or custom (cron-based) schedules
- **FR-016**: System MUST automatically create new task instances based on recurrence schedule
- **FR-017**: System MUST maintain recurrence even after individual task instances are completed

#### Event-Driven Architecture

- **FR-018**: System MUST emit TaskCreated event when a task is created
- **FR-019**: System MUST emit TaskUpdated event when a task is modified
- **FR-020**: System MUST emit TaskCompleted event when a task is marked complete
- **FR-021**: System MUST emit TaskDeleted event when a task is deleted
- **FR-022**: System MUST emit ReminderTriggered event when a reminder time is reached
- **FR-023**: System MUST emit RecurringTaskScheduled event when a recurring task instance is created
- **FR-024**: System MUST process events idempotently (duplicate events do not cause duplicate actions)

#### Dapr Integration

- **FR-025**: System MUST use Dapr Pub/Sub for all inter-service event communication
- **FR-026**: System MUST use Dapr State Store for scheduler metadata persistence
- **FR-027**: System MUST use Dapr Cron Bindings for time-based triggers
- **FR-028**: System MUST use Dapr Secrets for sensitive configuration
- **FR-029**: System MUST use Dapr Service Invocation for synchronous inter-service calls

#### Deployment

- **FR-030**: System MUST deploy successfully on Minikube
- **FR-031**: System MUST include all Dapr components configured for local operation
- **FR-032**: System MUST provide Helm charts or Kubernetes manifests for deployment

### Key Entities

- **Task**: Represents a user's todo item with title, description, status, priority, tags, due date, reminders, and recurrence settings
- **Reminder**: A scheduled notification associated with a task's due date
- **RecurrenceSchedule**: Defines when recurring task instances should be created (daily, weekly, or cron expression)
- **Event**: Immutable record of a system occurrence with unique ID, type, timestamp, and payload

---

## 11. Success Criteria

### Measurable Outcomes

- **SC-001**: Users can create, update, and delete tasks within 3 seconds per operation
- **SC-002**: Search results return within 2 seconds for a dataset of 1000 tasks
- **SC-003**: Task filter and sort operations complete within 1 second
- **SC-004**: Recurring task instances are created within 2 minutes of scheduled time
- **SC-005**: Reminders are triggered within 2 minutes of configured time
- **SC-006**: All task lifecycle events (create, update, complete, delete) are published within 1 second of operation
- **SC-007**: System recovers from single service failure within 60 seconds (Kubernetes restart)
- **SC-008**: All 5 Dapr building blocks (Pub/Sub, State Store, Bindings, Secrets, Service Invocation) are utilized and functional
- **SC-009**: Full deployment on Minikube completes within 10 minutes from clean state
- **SC-010**: Zero cloud provider dependencies in deployed artifacts

---

## 12. Assumptions

The following reasonable defaults and assumptions guide this specification:

1. **PostgreSQL Database**: Assumes existing PostgreSQL database (Neon or local) is available; no database provisioning in this spec
2. **JWT Authentication**: Assumes existing JWT authentication from Phase 007 is integrated
3. **User Notifications**: Reminders trigger events; actual notification delivery (email, push) is deferred to future phase
4. **Single User Focus**: Initial implementation focuses on single-user scenarios; multi-user event isolation is a future enhancement
5. **Local Development**: All testing and validation occurs on developer machines using Minikube
6. **Redis for Local**: Redis is used for pub/sub and state store locally; production may use different backends via Dapr abstraction
7. **Cron Precision**: Cron bindings have 1-minute granularity; sub-minute precision is not required
8. **Event Ordering**: Events within a topic may be processed out of order; consumers handle this via timestamps and idempotency

---

## 13. Boundary Statement

> **Cloud deployment is deferred to Phase V – Part 2**
>
> This specification (Phase V – Part 1) covers **local development architecture only**. The following are explicitly excluded and will be addressed in a separate Phase V – Part 2 specification:
>
> - Cloud provider deployment (AKS, GKE, OCI, AWS)
> - Managed Kafka services (Confluent, Redpanda Cloud)
> - CI/CD pipeline integration
> - Production monitoring and observability
> - Horizontal scaling and auto-scaling
> - Ingress controllers and TLS termination
> - Multi-region or multi-cluster deployment
