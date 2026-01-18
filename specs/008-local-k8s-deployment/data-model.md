# Data Model: Phase IV - Local Kubernetes Deployment

**Feature**: 008-local-k8s-deployment
**Date**: 2026-01-16
**Status**: Complete

---

## Overview

This document defines the Kubernetes resource model for the Todo Chatbot application. Unlike traditional data models, this describes infrastructure entities and their relationships within the cluster.

---

## Resource Model

### 1. Namespace

**Name**: `todo-chatbot` (default, configurable)

**Purpose**: Logical isolation of all application resources

**Attributes**:
- Provides DNS scoping for service discovery
- Enables resource quotas (not used in Phase IV)
- Simplifies cleanup via `kubectl delete namespace`

---

### 2. Backend Resources

#### 2.1 Backend Deployment

| Field | Value | Notes |
|-------|-------|-------|
| Name | `todo-backend` | |
| Replicas | 1 | Single replica for local dev |
| Image | `todo-backend:dev` | Built locally in Minikube |
| Port | 8000 | FastAPI/uvicorn default |
| imagePullPolicy | IfNotPresent | Use local image |

**Container Environment Variables**:
| Variable | Source | Required |
|----------|--------|----------|
| DATABASE_URL | Secret | Yes |
| JWT_SECRET | Secret | Yes |
| GEMINI_API_KEY | Secret | Yes |
| FRONTEND_URL | ConfigMap | No |
| LOG_LEVEL | ConfigMap | No |

**Probes**:
| Probe | Type | Path | Initial Delay | Period |
|-------|------|------|---------------|--------|
| Liveness | HTTP GET | /health | 10s | 10s |
| Readiness | HTTP GET | /health | 5s | 5s |

**Resource Limits** (recommended for local):
| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 100m | 500m |
| Memory | 128Mi | 512Mi |

---

#### 2.2 Backend Service

| Field | Value | Notes |
|-------|-------|-------|
| Name | `todo-backend` | |
| Type | ClusterIP | Internal access only |
| Port | 8000 | Maps to container port |
| Target Port | 8000 | |

**DNS Name**: `todo-backend.todo-chatbot.svc.cluster.local`

---

#### 2.3 Backend ConfigMap

**Name**: `todo-backend-config`

| Key | Default Value | Description |
|-----|---------------|-------------|
| FRONTEND_URL | http://todo-frontend:80 | For CORS configuration |
| LOG_LEVEL | INFO | Logging verbosity |

---

#### 2.4 Backend Secret

**Name**: `todo-backend-secrets`
**Type**: Opaque

| Key | Description | Required |
|-----|-------------|----------|
| DATABASE_URL | PostgreSQL connection string (Neon) | Yes |
| JWT_SECRET | HS256 signing key | Yes |
| GEMINI_API_KEY | Google Gemini API key | Yes |

**Note**: Values provided via Helm values.yaml or --set flags.

---

### 3. Frontend Resources

#### 3.1 Frontend Deployment

| Field | Value | Notes |
|-------|-------|-------|
| Name | `todo-frontend` | |
| Replicas | 1 | Single replica for local dev |
| Image | `todo-frontend:dev` | Built locally in Minikube |
| Port | 80 | nginx default |
| imagePullPolicy | IfNotPresent | Use local image |

**Probes**:
| Probe | Type | Path/Port | Initial Delay | Period |
|-------|------|-----------|---------------|--------|
| Liveness | TCP | 80 | 5s | 10s |
| Readiness | HTTP GET | / | 3s | 5s |

**Resource Limits** (recommended for local):
| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 50m | 200m |
| Memory | 64Mi | 128Mi |

---

#### 3.2 Frontend Service

| Field | Value | Notes |
|-------|-------|-------|
| Name | `todo-frontend` | |
| Type | NodePort | External access via Minikube |
| Port | 80 | Service port |
| Target Port | 80 | Container port |
| NodePort | (auto-assigned) | 30000-32767 range |

**Access**: `minikube service todo-frontend -n todo-chatbot`

---

#### 3.3 Frontend ConfigMap

**Name**: `todo-frontend-config`

| Key | Default Value | Description |
|-----|---------------|-------------|
| NEXT_PUBLIC_API_URL | http://todo-backend:8000 | Backend API endpoint (build-time) |

**Note**: This is used at Docker build time, not runtime.

---

## Resource Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                    Namespace: todo-chatbot                       │
│                                                                  │
│  ┌─────────────────┐                  ┌─────────────────────┐   │
│  │ ConfigMap:      │                  │ ConfigMap:          │   │
│  │ frontend-config │                  │ backend-config      │   │
│  └────────┬────────┘                  └──────────┬──────────┘   │
│           │                                      │               │
│           │ (build-time)                         │ (mounted)     │
│           ▼                                      ▼               │
│  ┌─────────────────┐   ┌──────────┐   ┌─────────────────────┐   │
│  │ Deployment:     │   │ Service: │   │ Deployment:         │   │
│  │ todo-frontend   │◀──│ frontend │   │ todo-backend        │   │
│  │  (nginx:80)     │   │ NodePort │   │  (uvicorn:8000)     │   │
│  └────────┬────────┘   └──────────┘   └──────────┬──────────┘   │
│           │                                      │               │
│           │                           ┌──────────┴──────────┐   │
│           │                           │ Service:            │   │
│           └──────────────────────────▶│ todo-backend        │   │
│                 (internal DNS)        │ ClusterIP           │   │
│                                       └──────────┬──────────┘   │
│                                                  │               │
│                                       ┌──────────┴──────────┐   │
│                                       │ Secret:             │   │
│                                       │ backend-secrets     │   │
│                                       │ (DB, JWT, API keys) │   │
│                                       └─────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼ (external)
               ┌─────────────────────┐
               │   Neon PostgreSQL   │
               │   (External DB)     │
               └─────────────────────┘
```

---

## Helm Values Structure

```yaml
# values.yaml structure (not actual content)
global:
  namespace: todo-chatbot
  imagePullPolicy: IfNotPresent

backend:
  image:
    repository: todo-backend
    tag: dev
  replicas: 1
  service:
    type: ClusterIP
    port: 8000
  config:
    logLevel: INFO
  secrets:
    databaseUrl: ""      # REQUIRED
    jwtSecret: ""        # REQUIRED
    geminiApiKey: ""     # REQUIRED
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  probes:
    liveness:
      initialDelaySeconds: 10
      periodSeconds: 10
    readiness:
      initialDelaySeconds: 5
      periodSeconds: 5

frontend:
  image:
    repository: todo-frontend
    tag: dev
  replicas: 1
  service:
    type: NodePort
    port: 80
  config:
    apiUrl: "http://todo-backend:8000"
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 200m
      memory: 128Mi
```

---

## Validation Rules

### Deployment Validation
- [ ] Image exists in Minikube Docker daemon
- [ ] Required secrets are provided (non-empty)
- [ ] Resource limits are within Minikube capacity
- [ ] Probes target correct endpoints

### Service Validation
- [ ] Backend ClusterIP resolves within cluster
- [ ] Frontend NodePort is accessible from host
- [ ] Port mappings are consistent

### Secret Validation
- [ ] DATABASE_URL is valid PostgreSQL connection string
- [ ] JWT_SECRET is non-empty
- [ ] GEMINI_API_KEY is valid (application will fail gracefully if invalid)

---

## State Transitions

### Pod Lifecycle

```
Pending → ContainerCreating → Running → Ready
                                │
                                ├──▶ CrashLoopBackOff (if probes fail)
                                │
                                └──▶ Terminated (on delete/scale down)
```

### Helm Release Lifecycle

```
Not Installed → Deployed → Updated → Uninstalled
                  │            │
                  ▼            ▼
               Failed      Rolled Back
```
