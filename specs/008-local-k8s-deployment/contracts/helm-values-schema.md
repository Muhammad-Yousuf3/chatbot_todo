# Helm Values Contract: Todo Chatbot

**Feature**: 008-local-k8s-deployment
**Date**: 2026-01-16

---

## Overview

This document defines the contract for Helm values configuration. All values are optional except where marked REQUIRED.

---

## Schema Definition

### Global Configuration

```yaml
global:
  # Kubernetes namespace for all resources
  # Type: string
  # Default: "todo-chatbot"
  namespace: "todo-chatbot"

  # Default image pull policy for all deployments
  # Type: enum [Always, IfNotPresent, Never]
  # Default: "IfNotPresent"
  imagePullPolicy: "IfNotPresent"
```

---

### Backend Configuration

```yaml
backend:
  # Enable/disable backend deployment
  # Type: boolean
  # Default: true
  enabled: true

  image:
    # Container image repository
    # Type: string
    # Default: "todo-backend"
    repository: "todo-backend"

    # Container image tag
    # Type: string
    # Default: "dev"
    tag: "dev"

    # Override global imagePullPolicy
    # Type: enum [Always, IfNotPresent, Never]
    # Default: (uses global.imagePullPolicy)
    pullPolicy: ""

  # Number of pod replicas
  # Type: integer
  # Default: 1
  # Minimum: 1
  replicas: 1

  service:
    # Kubernetes service type
    # Type: enum [ClusterIP, NodePort, LoadBalancer]
    # Default: "ClusterIP"
    type: "ClusterIP"

    # Service port
    # Type: integer
    # Default: 8000
    # Range: 1-65535
    port: 8000

  config:
    # Logging level
    # Type: enum [DEBUG, INFO, WARNING, ERROR]
    # Default: "INFO"
    logLevel: "INFO"

    # Frontend URL for CORS
    # Type: string (URL)
    # Default: "http://todo-frontend:80"
    frontendUrl: "http://todo-frontend:80"

  secrets:
    # REQUIRED: PostgreSQL connection string
    # Type: string
    # Format: postgresql://user:password@host:port/database
    # Default: "" (must be provided)
    databaseUrl: ""

    # REQUIRED: JWT signing secret
    # Type: string
    # Minimum length: 32 characters recommended
    # Default: "" (must be provided)
    jwtSecret: ""

    # REQUIRED: Google Gemini API key
    # Type: string
    # Format: AIza...
    # Default: "" (must be provided)
    geminiApiKey: ""

  resources:
    requests:
      # CPU request
      # Type: string (Kubernetes resource quantity)
      # Default: "100m"
      cpu: "100m"

      # Memory request
      # Type: string (Kubernetes resource quantity)
      # Default: "128Mi"
      memory: "128Mi"

    limits:
      # CPU limit
      # Type: string (Kubernetes resource quantity)
      # Default: "500m"
      cpu: "500m"

      # Memory limit
      # Type: string (Kubernetes resource quantity)
      # Default: "512Mi"
      memory: "512Mi"

  probes:
    liveness:
      # Seconds before first liveness check
      # Type: integer
      # Default: 10
      # Minimum: 0
      initialDelaySeconds: 10

      # Seconds between checks
      # Type: integer
      # Default: 10
      # Minimum: 1
      periodSeconds: 10

      # Failures before pod restart
      # Type: integer
      # Default: 3
      # Minimum: 1
      failureThreshold: 3

    readiness:
      # Seconds before first readiness check
      # Type: integer
      # Default: 5
      # Minimum: 0
      initialDelaySeconds: 5

      # Seconds between checks
      # Type: integer
      # Default: 5
      # Minimum: 1
      periodSeconds: 5

      # Failures before marking unready
      # Type: integer
      # Default: 3
      # Minimum: 1
      failureThreshold: 3
```

---

### Frontend Configuration

```yaml
frontend:
  # Enable/disable frontend deployment
  # Type: boolean
  # Default: true
  enabled: true

  image:
    # Container image repository
    # Type: string
    # Default: "todo-frontend"
    repository: "todo-frontend"

    # Container image tag
    # Type: string
    # Default: "dev"
    tag: "dev"

    # Override global imagePullPolicy
    # Type: enum [Always, IfNotPresent, Never]
    # Default: (uses global.imagePullPolicy)
    pullPolicy: ""

  # Number of pod replicas
  # Type: integer
  # Default: 1
  # Minimum: 1
  replicas: 1

  service:
    # Kubernetes service type
    # Type: enum [ClusterIP, NodePort, LoadBalancer]
    # Default: "NodePort"
    type: "NodePort"

    # Service port
    # Type: integer
    # Default: 80
    # Range: 1-65535
    port: 80

    # NodePort (when type is NodePort)
    # Type: integer
    # Range: 30000-32767
    # Default: (auto-assigned)
    nodePort: null

  config:
    # Backend API URL (used at build time)
    # Type: string (URL)
    # Default: "http://todo-backend:8000"
    apiUrl: "http://todo-backend:8000"

  resources:
    requests:
      # CPU request
      # Type: string (Kubernetes resource quantity)
      # Default: "50m"
      cpu: "50m"

      # Memory request
      # Type: string (Kubernetes resource quantity)
      # Default: "64Mi"
      memory: "64Mi"

    limits:
      # CPU limit
      # Type: string (Kubernetes resource quantity)
      # Default: "200m"
      cpu: "200m"

      # Memory limit
      # Type: string (Kubernetes resource quantity)
      # Default: "128Mi"
      memory: "128Mi"
```

---

## Validation Rules

### Required Values

The following values MUST be provided at install time:

| Path | Validation | Error Message |
|------|------------|---------------|
| `backend.secrets.databaseUrl` | Non-empty string | "DATABASE_URL is required" |
| `backend.secrets.jwtSecret` | Non-empty string | "JWT_SECRET is required" |
| `backend.secrets.geminiApiKey` | Non-empty string | "GEMINI_API_KEY is required" |

### Value Constraints

| Path | Constraint | Default Behavior |
|------|------------|------------------|
| `backend.replicas` | >= 1 | Set to 1 |
| `frontend.replicas` | >= 1 | Set to 1 |
| `backend.service.port` | 1-65535 | Fail template |
| `frontend.service.port` | 1-65535 | Fail template |
| `frontend.service.nodePort` | 30000-32767 or null | Auto-assign |

---

## Usage Examples

### Minimal Install (with required secrets)

```bash
helm install todo-app ./helm/todo-chatbot \
  --namespace todo-chatbot \
  --create-namespace \
  --set backend.secrets.databaseUrl="postgresql://..." \
  --set backend.secrets.jwtSecret="my-secret" \
  --set backend.secrets.geminiApiKey="AIza..."
```

### Using values file

```bash
# Create values-local.yaml with your secrets
helm install todo-app ./helm/todo-chatbot \
  --namespace todo-chatbot \
  --create-namespace \
  -f ./helm/todo-chatbot/values-local.yaml
```

### Override resources

```bash
helm install todo-app ./helm/todo-chatbot \
  --namespace todo-chatbot \
  --set backend.resources.limits.memory="1Gi" \
  --set backend.resources.limits.cpu="1000m"
```

### Debug mode

```bash
helm install todo-app ./helm/todo-chatbot \
  --namespace todo-chatbot \
  --set backend.config.logLevel="DEBUG"
```
