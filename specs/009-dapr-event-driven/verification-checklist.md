# Verification Checklist: Phase V Part 1 - Event-Driven Todo Chatbot

**Branch**: `009-dapr-event-driven` | **Date**: 2026-01-22

---

## Phase 9: Infrastructure Verification (T112-T117)

### T112: Minikube Setup Verification

```bash
# Start Minikube with required resources
minikube start --cpus=4 --memory=8192 --driver=docker

# Verify cluster is running
kubectl cluster-info
kubectl get nodes
```

**Expected**:
- [ ] Minikube starts without errors
- [ ] Single node shows `Ready` status
- [ ] Kubernetes API server accessible

---

### T113: Dapr Installation Verification

```bash
# Initialize Dapr on Kubernetes
dapr init -k --wait

# Verify Dapr status
dapr status -k
```

**Expected**:
- [ ] `dapr-operator` is Running and Healthy
- [ ] `dapr-sentry` is Running and Healthy
- [ ] `dapr-placement-server` is Running and Healthy
- [ ] `dapr-sidecar-injector` is Running and Healthy
- [ ] `dapr-dashboard` is Running and Healthy

---

### T114: Docker Image Build Verification

```bash
# Point docker to Minikube
eval $(minikube docker-env)

# Build images
docker build -t todo-backend:local ./backend
docker build -t todo-scheduler:local ./scheduler
docker build -t todo-frontend:local ./frontend

# Verify images
docker images | grep todo-
```

**Expected**:
- [ ] `todo-backend:local` image built successfully
- [ ] `todo-scheduler:local` image built successfully
- [ ] `todo-frontend:local` image built successfully (if frontend exists)

---

### T115: Helm Deployment Verification

```bash
# Create namespace and secrets first
kubectl create namespace todo-chatbot

kubectl create secret generic backend-secrets \
  --from-literal=DATABASE_URL="<your-db-url>" \
  --from-literal=JWT_SECRET="<your-jwt-secret-min-32-chars>" \
  --from-literal=GEMINI_API_KEY="<your-api-key>" \
  -n todo-chatbot

# Deploy with Helm
helm install todo-chatbot ./helm/todo-chatbot \
  -f ./helm/todo-chatbot/values-local.yaml \
  -n todo-chatbot

# Monitor deployment
kubectl get pods -n todo-chatbot -w
```

**Expected**:
- [ ] Helm install completes without errors
- [ ] All pods start within 5 minutes
- [ ] No CrashLoopBackOff or ImagePullBackOff errors

---

### T116: Pod Status Verification

```bash
# Check all pods running with correct container count
kubectl get pods -n todo-chatbot

# Verify Dapr sidecars
kubectl get pods -n todo-chatbot -o jsonpath='{range .items[*]}{.metadata.name}{": "}{range .spec.containers[*]}{.name}{" "}{end}{"\n"}{end}'
```

**Expected**:
- [ ] Backend pod shows `2/2` Ready (app + daprd)
- [ ] Scheduler pod shows `2/2` Ready (app + daprd)
- [ ] Redis pod shows `1/1` Ready
- [ ] Frontend pod shows `1/1` Ready (if deployed)
- [ ] All pods in `Running` status

---

### T117: Dapr Components Verification

```bash
# List Dapr components in namespace
dapr components -n todo-chatbot

# Verify each component
kubectl get component -n todo-chatbot
```

**Expected**:
- [ ] `pubsub` component (pubsub.redis) loaded
- [ ] `statestore` component (state.redis) loaded
- [ ] `kubernetes-secrets` component (secretstores.kubernetes) loaded
- [ ] `recurring-task-trigger` binding (bindings.cron) loaded with scheduler scope
- [ ] `reminder-check-trigger` binding (bindings.cron) loaded with scheduler scope

---

## Phase 10: Acceptance Scenario Verification (T126)

### User Story 1: Task Priority Management

**Scenario 1.1**: Create task with priority
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"title": "High priority task", "priority": "high"}'
```
- [ ] Task created with priority field
- [ ] Priority defaults to "medium" when not specified

**Scenario 1.2**: Filter by priority
```bash
curl "http://localhost:8000/api/tasks?priority=high" \
  -H "Authorization: Bearer <token>"
```
- [ ] Only high-priority tasks returned

**Scenario 1.3**: Update priority emits event
```bash
curl -X PATCH http://localhost:8000/api/tasks/<task-id> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"priority": "low"}'

# Check Redis for TaskUpdated event
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli XRANGE tasks - + COUNT 5
```
- [ ] TaskUpdated event emitted
- [ ] Event includes priority change with old/new values

---

### User Story 2: Tag-Based Organization

**Scenario 2.1**: Create task with tags
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"title": "Tagged task", "tags": ["work", "urgent"]}'
```
- [ ] Task created with tags array

**Scenario 2.2**: Filter by tag
```bash
curl "http://localhost:8000/api/tasks?tag=work" \
  -H "Authorization: Bearer <token>"
```
- [ ] Only tasks with "work" tag returned

**Scenario 2.3**: Tag validation
```bash
# Try to add more than 10 tags or tags > 50 chars
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"title": "Test", "tags": ["1","2","3","4","5","6","7","8","9","10","11"]}'
```
- [ ] Validation error returned for > 10 tags
- [ ] Tags limited to 50 characters each

---

### User Story 3: Task Search and Filtering

**Scenario 3.1**: Keyword search
```bash
curl "http://localhost:8000/api/tasks?search=review" \
  -H "Authorization: Bearer <token>"
```
- [ ] Tasks with "review" in title or description returned
- [ ] Response within 2 seconds

**Scenario 3.2**: Status filter
```bash
curl "http://localhost:8000/api/tasks?status=pending" \
  -H "Authorization: Bearer <token>"
```
- [ ] Only pending tasks returned

**Scenario 3.3**: Combined filters with sorting
```bash
curl "http://localhost:8000/api/tasks?priority=high&status=pending&sort_by=due_date&sort_order=asc" \
  -H "Authorization: Bearer <token>"
```
- [ ] Filters combined correctly
- [ ] Results sorted by due_date ascending

---

### User Story 4: Recurring Task Scheduling

**Scenario 4.1**: Create daily recurring task
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "title": "Daily standup notes",
    "recurrence": {"recurrence_type": "daily"}
  }'

# Check State Store
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli KEYS "scheduler||recurring:*"
```
- [ ] Recurring schedule stored in State Store
- [ ] next_occurrence calculated correctly

**Scenario 4.2**: Recurring task triggers new instance
```bash
# Wait for cron trigger (up to 2 minutes) and check logs
kubectl logs deployment/scheduler -n todo-chatbot -c scheduler -f | grep "trigger"

# Check for new task instance
curl "http://localhost:8000/api/tasks" -H "Authorization: Bearer <token>"
```
- [ ] New task instance created when scheduled time reached
- [ ] RecurringTaskScheduled event emitted

**Scenario 4.3**: Delete source task stops recurrence
```bash
curl -X DELETE http://localhost:8000/api/tasks/<recurring-task-id> \
  -H "Authorization: Bearer <token>"

# Verify State Store entry removed
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli KEYS "scheduler||recurring:*"
```
- [ ] Recurring schedule removed from State Store
- [ ] No more instances created

---

### User Story 5: Due Date Reminders

**Scenario 5.1**: Create task with reminder
```bash
TRIGGER_TIME=$(date -u -d "+2 minutes" +"%Y-%m-%dT%H:%M:%SZ")
DUE_TIME=$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ")

curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d "{
    \"title\": \"Reminder test\",
    \"due_date\": \"$DUE_TIME\",
    \"reminders\": [{\"trigger_at\": \"$TRIGGER_TIME\"}]
  }"

# Check State Store
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli KEYS "scheduler||reminder:*"
```
- [ ] Reminder stored in State Store
- [ ] trigger_at validated to be before due_date

**Scenario 5.2**: Reminder triggers at scheduled time
```bash
# Wait for trigger time and check
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli XRANGE notifications - + COUNT 5
```
- [ ] ReminderTriggered event published within 2 minutes of trigger_at
- [ ] Reminder marked as fired in State Store

**Scenario 5.3**: Complete task cancels reminders
```bash
curl -X POST http://localhost:8000/api/tasks/<task-id>/complete \
  -H "Authorization: Bearer <token>"

# Check reminder cancelled
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli GET "scheduler||reminder:<reminder-id>"
```
- [ ] Pending reminders cancelled when task completed
- [ ] cancelled=true in State Store

---

### User Story 6: Event-Driven Task Lifecycle

**Scenario 6.1**: TaskCreated event
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"title": "Event test"}'

# Check event in Redis
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli XRANGE tasks - + COUNT 1
```
- [ ] TaskCreated event published within 1 second
- [ ] Event includes all task fields

**Scenario 6.2**: TaskUpdated event with change tracking
```bash
curl -X PATCH http://localhost:8000/api/tasks/<task-id> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"title": "Updated title", "priority": "high"}'

kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli XRANGE tasks - + COUNT 5 | grep "task.updated"
```
- [ ] TaskUpdated event includes changes dict
- [ ] Changes show old_value and new_value

**Scenario 6.3**: TaskCompleted event
```bash
curl -X POST http://localhost:8000/api/tasks/<task-id>/complete \
  -H "Authorization: Bearer <token>"

kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli XRANGE tasks - + COUNT 5 | grep "task.completed"
```
- [ ] TaskCompleted event published
- [ ] Event includes completed_at timestamp

**Scenario 6.4**: TaskDeleted event
```bash
curl -X DELETE http://localhost:8000/api/tasks/<task-id> \
  -H "Authorization: Bearer <token>"

kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli XRANGE tasks - + COUNT 5 | grep "task.deleted"
```
- [ ] TaskDeleted event published
- [ ] Scheduler removes related schedules/reminders

**Scenario 6.5**: Event idempotency
```bash
# Simulate duplicate event by checking processed_events table
# Events with same ID should not be processed twice
```
- [ ] Duplicate events identified by event_id
- [ ] No duplicate actions from replayed events

---

## Quick Verification Commands

```bash
# Overall system health
kubectl get pods -n todo-chatbot
dapr components -n todo-chatbot

# Health endpoints
kubectl port-forward svc/todo-backend-svc 8000:8000 -n todo-chatbot &
curl http://localhost:8000/health
curl http://localhost:8000/health/dapr

# Redis inspection
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli
> KEYS *
> XRANGE tasks - + COUNT 10
> XRANGE notifications - + COUNT 10
```

---

## Summary Checklist

### Infrastructure (T112-T117)
- [ ] T112: Minikube running with adequate resources
- [ ] T113: Dapr control plane healthy
- [ ] T114: All Docker images built
- [ ] T115: Helm deployment successful
- [ ] T116: All pods Running with correct containers
- [ ] T117: All Dapr components loaded

### Acceptance Scenarios (T126)
- [ ] US1: Priority management working
- [ ] US2: Tag-based organization working
- [ ] US3: Search and filtering working
- [ ] US4: Recurring task scheduling working
- [ ] US5: Due date reminders working
- [ ] US6: Event-driven lifecycle complete

**Verification Status**: Ready for manual testing
