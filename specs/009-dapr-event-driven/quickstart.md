# Quickstart: Phase V Part 1 - Local Deployment Guide

**Branch**: `009-dapr-event-driven` | **Date**: 2026-01-20 | **Plan**: [plan.md](./plan.md)

---

## Overview

This guide provides step-by-step instructions for deploying the event-driven Todo Chatbot on **local Minikube** with Dapr. By the end, you will have:

- Minikube cluster running
- Dapr control plane installed
- Redis (Pub/Sub + State Store) deployed
- Backend service with Dapr sidecar
- Scheduler service with Dapr sidecar
- Frontend accessible via NodePort
- All Dapr components configured

---

## Prerequisites

### Required Tools

| Tool | Minimum Version | Installation |
|------|-----------------|--------------|
| Docker | 24.0.0+ | [docker.com](https://docs.docker.com/get-docker/) |
| Minikube | 1.30.0+ | `brew install minikube` or [minikube.sigs.k8s.io](https://minikube.sigs.k8s.io/docs/start/) |
| kubectl | 1.28.0+ | `brew install kubectl` or [kubernetes.io](https://kubernetes.io/docs/tasks/tools/) |
| Helm | 3.12.0+ | `brew install helm` or [helm.sh](https://helm.sh/docs/intro/install/) |
| Dapr CLI | 1.12.0+ | `brew install dapr/tap/dapr-cli` or [dapr.io](https://docs.dapr.io/getting-started/install-dapr-cli/) |

### Verify Installations

```bash
# Verify all tools are installed
docker --version     # Docker version 24.x.x
minikube version     # minikube version: v1.30.x
kubectl version --client  # Client Version: v1.28.x
helm version         # version.BuildInfo{Version:"v3.12.x"}
dapr --version       # CLI version: 1.12.x
```

### System Requirements

- **CPU**: 4 cores minimum (for Minikube)
- **RAM**: 8GB minimum allocated to Minikube
- **Disk**: 20GB free space

---

## Step 1: Start Minikube

```bash
# Start Minikube with adequate resources
minikube start \
  --cpus=4 \
  --memory=8192 \
  --driver=docker \
  --kubernetes-version=v1.28.0

# Verify cluster is running
kubectl cluster-info
kubectl get nodes

# Expected output:
# NAME       STATUS   ROLES           AGE   VERSION
# minikube   Ready    control-plane   1m    v1.28.0
```

### Enable Minikube Docker Environment

```bash
# Point Docker CLI to Minikube's Docker daemon
eval $(minikube docker-env)

# Verify
docker ps  # Should show Minikube containers
```

---

## Step 2: Install Dapr on Kubernetes

```bash
# Initialize Dapr on the Kubernetes cluster
dapr init -k --wait

# Verify Dapr installation
dapr status -k

# Expected output:
#   NAME                   NAMESPACE    HEALTHY  STATUS   REPLICAS
#   dapr-operator          dapr-system  True     Running  1
#   dapr-sentry            dapr-system  True     Running  1
#   dapr-placement-server  dapr-system  True     Running  1
#   dapr-sidecar-injector  dapr-system  True     Running  1
#   dapr-dashboard         dapr-system  True     Running  1
```

### Access Dapr Dashboard (Optional)

```bash
# Open Dapr Dashboard in browser
dapr dashboard -k

# Dashboard URL: http://localhost:8080
```

---

## Step 3: Create Namespace and Secrets

```bash
# Create application namespace
kubectl create namespace todo-chatbot

# Create Kubernetes secrets for sensitive configuration
kubectl create secret generic backend-secrets \
  --from-literal=DATABASE_URL="postgresql+asyncpg://user:password@host:5432/dbname" \
  --from-literal=JWT_SECRET="your-local-development-secret-key-minimum-32-characters" \
  --from-literal=GEMINI_API_KEY="your-gemini-api-key" \
  -n todo-chatbot

# Verify secret created
kubectl get secrets -n todo-chatbot

# Expected output:
# NAME              TYPE     DATA   AGE
# backend-secrets   Opaque   3      5s
```

### Secret Configuration

| Secret Key | Description | Example |
|------------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (Neon or local) | `postgresql+asyncpg://user:pass@host:5432/db` |
| `JWT_SECRET` | JWT signing key (minimum 32 characters) | `your-super-secret-jwt-signing-key-here` |
| `GEMINI_API_KEY` | Google Gemini API key for AI features | `AIza...` |

> **Note**: For production, use proper secret management (HashiCorp Vault, AWS Secrets Manager, etc.)

---

## Step 4: Build Docker Images

From the repository root:

```bash
# Ensure Docker points to Minikube
eval $(minikube docker-env)

# Build Backend image
docker build -t todo-backend:local ./backend

# Build Scheduler image
docker build -t todo-scheduler:local ./scheduler

# Build Frontend image
docker build -t todo-frontend:local ./frontend

# Verify images
docker images | grep todo-

# Expected output:
# todo-backend    local   abc123   1 minute ago   200MB
# todo-scheduler  local   def456   1 minute ago   150MB
# todo-frontend   local   ghi789   1 minute ago   50MB
```

---

## Step 5: Deploy with Helm

```bash
# Navigate to repository root
cd /path/to/Chatbot_TODO

# Install the Helm chart with local values
helm install todo-chatbot ./helm/todo-chatbot \
  -f ./helm/todo-chatbot/values-local.yaml \
  -n todo-chatbot

# Monitor deployment progress
kubectl get pods -n todo-chatbot -w

# Wait for all pods to be Running (press Ctrl+C to exit watch)
```

### Expected Pod Status

```
NAME                         READY   STATUS    RESTARTS   AGE
backend-xxx-yyy              2/2     Running   0          2m
scheduler-xxx-yyy            2/2     Running   0          2m
frontend-xxx-yyy             1/1     Running   0          2m
redis-xxx-yyy                1/1     Running   0          2m
```

> **Note**: Backend and Scheduler should show `2/2` (app + Dapr sidecar)

---

## Step 6: Verify Deployment

### Check Dapr Components

```bash
# List Dapr components in the namespace
dapr components -n todo-chatbot

# Expected output:
# NAMESPACE  NAME                     TYPE               VERSION  SCOPES
# todo-app   pubsub                   pubsub.redis       v1
# todo-app   statestore               state.redis        v1
# todo-app   kubernetes-secrets       secretstores.k8s   v1
# todo-app   recurring-task-trigger   bindings.cron      v1       scheduler
# todo-app   reminder-check-trigger   bindings.cron      v1       scheduler
```

### Check Services

```bash
kubectl get svc -n todo-chatbot

# Expected output:
# NAME           TYPE        CLUSTER-IP      PORT(S)          AGE
# backend-svc    ClusterIP   10.96.x.x       8000/TCP         3m
# scheduler-svc  ClusterIP   10.96.x.x       8001/TCP         3m
# frontend-svc   NodePort    10.96.x.x       80:30080/TCP     3m
# redis-svc      ClusterIP   10.96.x.x       6379/TCP         3m
```

### Verify Dapr Sidecars

```bash
# Check Backend has Dapr sidecar
kubectl get pods -n todo-chatbot -l app=backend -o jsonpath='{.items[*].spec.containers[*].name}'
# Expected: backend daprd

# Check Scheduler has Dapr sidecar
kubectl get pods -n todo-chatbot -l app=scheduler -o jsonpath='{.items[*].spec.containers[*].name}'
# Expected: scheduler daprd
```

---

## Step 7: Access the Application

### Frontend (Browser)

```bash
# Open frontend in default browser
minikube service frontend-svc -n todo-chatbot

# Or get the URL manually
minikube service frontend-svc -n todo-chatbot --url
# Example output: http://192.168.49.2:30080
```

### Backend API (Terminal)

```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

# Test Backend health endpoint
curl http://$MINIKUBE_IP:30080/api/health

# Expected response:
# {"status":"healthy","timestamp":"2026-01-20T..."}
```

### Dapr Dashboard

```bash
# Open Dapr Dashboard
dapr dashboard -k

# Navigate to: http://localhost:8080
# - View Components
# - View Applications (backend, scheduler)
# - View Configurations
```

---

## Step 8: Validate Event Flow

### Test Task Creation with Event

```bash
# 1. Create a user and login (if using JWT auth)
# ... (use your existing auth flow)

# 2. Create a task via API
curl -X POST http://$MINIKUBE_IP:30080/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d '{
    "title": "Test event flow",
    "priority": "high",
    "tags": ["test", "dapr"]
  }'

# 3. Check Redis for TaskCreated event
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli XRANGE tasks - + COUNT 5

# 4. Check Scheduler received event
kubectl logs deployment/scheduler -n todo-chatbot -c scheduler | grep "TaskCreated"
```

### Test Recurring Task

```bash
# 1. Create task with recurrence
curl -X POST http://$MINIKUBE_IP:30080/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d '{
    "title": "Daily standup notes",
    "recurrence": {
      "recurrence_type": "daily"
    }
  }'

# 2. Check State Store for recurring schedule
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli KEYS "recurring:*"

# 3. Wait for cron trigger (up to 1 minute) and check logs
kubectl logs deployment/scheduler -n todo-chatbot -c scheduler -f | grep "trigger"
```

### Test Reminder

```bash
# 1. Create task with reminder (trigger 2 minutes from now)
TRIGGER_TIME=$(date -u -d "+2 minutes" +"%Y-%m-%dT%H:%M:%SZ")

curl -X POST http://$MINIKUBE_IP:30080/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d "{
    \"title\": \"Reminder test\",
    \"due_date\": \"$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ")\",
    \"reminders\": [
      {\"trigger_at\": \"$TRIGGER_TIME\"}
    ]
  }"

# 2. Check State Store for reminder
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli KEYS "reminder:*"

# 3. Wait for reminder trigger and check notifications topic
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli XRANGE notifications - + COUNT 5
```

---

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n todo-chatbot

# Check container logs
kubectl logs <pod-name> -n todo-chatbot -c <container-name>

# For Dapr sidecar issues
kubectl logs <pod-name> -n todo-chatbot -c daprd
```

### Dapr Sidecar Not Injected

```bash
# Verify Dapr annotations on deployment
kubectl get deployment backend -n todo-chatbot -o yaml | grep -A5 "annotations"

# Required annotations:
#   dapr.io/enabled: "true"
#   dapr.io/app-id: "backend"
#   dapr.io/app-port: "8000"

# Verify Dapr sidecar injector is running
kubectl get pods -n dapr-system | grep sidecar-injector
```

### Events Not Publishing

```bash
# Check Dapr sidecar logs for publish errors
kubectl logs <pod-name> -n todo-chatbot -c daprd | grep -i "error\|pub"

# Verify pubsub component is loaded
dapr components -n todo-chatbot | grep pubsub

# Test direct publish via Dapr CLI
dapr publish --app-id backend --pubsub pubsub --topic tasks --data '{"test":"data"}'
```

### State Not Persisting

```bash
# Verify state store component
dapr components -n todo-chatbot | grep statestore

# Test state store directly via Redis CLI
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli KEYS "*"

# Check for Dapr state key prefix (default: app-id||)
kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli KEYS "scheduler||*"
```

### Cron Binding Not Triggering

```bash
# Check binding component is loaded
dapr components -n todo-chatbot | grep bindings

# Check binding scopes (should include scheduler)
kubectl get component recurring-task-trigger -n todo-chatbot -o yaml | grep -A3 scopes

# Check Scheduler logs for binding invocation
kubectl logs deployment/scheduler -n todo-chatbot -c daprd | grep -i "binding"
```

---

## Cleanup

### Uninstall Application

```bash
# Remove Helm release
helm uninstall todo-chatbot -n todo-chatbot

# Delete namespace (removes all resources)
kubectl delete namespace todo-app
```

### Uninstall Dapr

```bash
# Remove Dapr from Kubernetes
dapr uninstall -k
```

### Stop Minikube

```bash
# Stop the cluster (preserves state)
minikube stop

# Or delete the cluster entirely
minikube delete
```

---

## Quick Reference

### Useful Commands

| Task | Command |
|------|---------|
| View pods | `kubectl get pods -n todo-chatbot` |
| View logs (app) | `kubectl logs deployment/backend -n todo-chatbot -c backend` |
| View logs (Dapr) | `kubectl logs deployment/backend -n todo-chatbot -c daprd` |
| Open Dapr Dashboard | `dapr dashboard -k` |
| Open Frontend | `minikube service frontend-svc -n todo-chatbot` |
| Redis CLI | `kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli` |
| Helm status | `helm status todo-chatbot -n todo-chatbot` |
| Upgrade deployment | `helm upgrade todo-chatbot ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml -n todo-chatbot` |

### Port Reference

| Service | Port | NodePort | Access |
|---------|------|----------|--------|
| Backend | 8000 | - | ClusterIP only |
| Scheduler | 8001 | - | ClusterIP only |
| Frontend | 80 | 30080 | `http://$(minikube ip):30080` |
| Redis | 6379 | - | ClusterIP only |
| Dapr Dashboard | 8080 | - | `dapr dashboard -k` |

---

**Quickstart Status**: Complete. System ready for development and testing.
