# Implementation Plan: Phase IV - Local Kubernetes Deployment

**Branch**: `008-local-k8s-deployment` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-local-k8s-deployment/spec.md`

---

## Summary

Deploy the existing Todo Chatbot application (FastAPI backend + Next.js frontend) to a local Minikube Kubernetes cluster using Docker containerization and Helm charts. This is an infrastructure-only phase with no application code changes.

---

## Technical Context

**Language/Version**: Python 3.11 (backend), Node.js 20 LTS (frontend build), nginx (frontend runtime)
**Primary Dependencies**: Docker, Minikube, kubectl, Helm 3.x
**Storage**: PostgreSQL (Neon) - external, no changes required
**Testing**: Manual validation via kubectl and browser
**Target Platform**: Local Minikube cluster (Linux/macOS/Windows with Docker Desktop)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Deploy in under 5 minutes, pods Running within 2 minutes
**Constraints**: Local development only, single replica, no ingress, no TLS
**Scale/Scope**: Single developer workstation, 2 services, 1 Helm chart

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Development | ✅ PASS | Following specify → plan → tasks → implement sequence |
| II. Stateless Backend | ✅ PASS | No changes to backend architecture; containerization preserves statelessness |
| III. Clear Responsibility Boundaries | ✅ PASS | Infrastructure layer only; no mixing with application logic |
| IV. AI Safety Through MCP | ✅ N/A | No AI agent changes; deployment infrastructure only |
| V. Simplicity Over Cleverness | ✅ PASS | Single Helm chart, minimal configuration, standard patterns |
| VI. Deterministic Behavior | ✅ PASS | Reproducible deployments via Helm; explicit configuration |

**Technical Constraints Compliance**:
- ✅ Backend uses FastAPI, SQLModel, Pydantic (unchanged)
- ✅ Database uses PostgreSQL (Neon) - external access from pods
- ✅ Authentication uses JWT (unchanged, secrets managed via K8s)
- ✅ No direct database access patterns introduced
- ✅ No hardcoded secrets (K8s Secrets + Helm values)

**Gate Result**: PASS - Proceeding with implementation planning.

---

## Project Structure

### Documentation (this feature)

```text
specs/008-local-k8s-deployment/
├── spec.md                              # Feature specification
├── plan.md                              # This file
├── research.md                          # Phase 0: Technical research
├── data-model.md                        # Phase 1: K8s resource model
├── quickstart.md                        # Phase 1: Developer guide
├── contracts/
│   └── helm-values-schema.md            # Helm values contract
├── checklists/
│   └── requirements.md                  # Spec quality checklist
└── tasks.md                             # Phase 2: Task breakdown (created by /sp.tasks)
```

### Source Code (repository root)

```text
Chatbot_TODO/
├── backend/
│   ├── Dockerfile                       # NEW: Backend container definition
│   └── src/                             # Existing source (unchanged)
├── frontend/
│   ├── Dockerfile                       # NEW: Frontend container definition
│   ├── nginx.conf                       # NEW: nginx configuration for SPA
│   └── app/                             # Existing source (unchanged)
└── helm/
    └── todo-chatbot/                    # NEW: Helm chart
        ├── Chart.yaml
        ├── values.yaml
        ├── values-local.yaml
        └── templates/
            ├── _helpers.tpl
            ├── namespace.yaml
            ├── backend/
            │   ├── deployment.yaml
            │   ├── service.yaml
            │   ├── configmap.yaml
            │   └── secret.yaml
            └── frontend/
                ├── deployment.yaml
                ├── service.yaml
                └── configmap.yaml
```

**Structure Decision**: Web application structure with separate backend and frontend directories. Helm chart added at repository root for deployment configuration. No changes to existing source directories.

---

## Phase IV Execution Plan

### Stage 1: Environment Verification

**Goal**: Confirm all prerequisites are installed and Minikube cluster is operational.

**Actions**:
1. Verify Docker is installed and running
2. Verify Minikube is installed (version 1.30+)
3. Verify kubectl is installed and configured
4. Verify Helm 3.x is installed
5. Start Minikube cluster with appropriate resources (2 CPU, 4GB RAM)
6. Verify cluster connectivity via kubectl

**Validation / Exit Criteria**:
- [ ] `docker --version` returns version info
- [ ] `minikube version` returns 1.30+
- [ ] `kubectl version --client` returns 1.28+
- [ ] `helm version` returns 3.x
- [ ] `minikube status` shows Running
- [ ] `kubectl cluster-info` shows cluster endpoint

---

### Stage 2: Backend Containerization

**Goal**: Create a Docker image for the FastAPI backend that builds and runs correctly.

**Actions**:
1. Create `backend/Dockerfile` with multi-stage build:
   - Build stage: Install dependencies from pyproject.toml
   - Runtime stage: Python 3.11-slim with only necessary files
2. Configure container to expose port 8000
3. Set uvicorn as the entrypoint
4. Build image locally to verify Dockerfile correctness

**Validation / Exit Criteria**:
- [ ] `docker build -t todo-backend:dev backend/` completes without errors
- [ ] Image size is reasonable (< 500MB)
- [ ] `docker run --rm todo-backend:dev --help` shows uvicorn help
- [ ] `/health` endpoint is defined in application (already exists)

---

### Stage 3: Frontend Containerization

**Goal**: Create a Docker image for the Next.js frontend that builds static assets and serves via nginx.

**Actions**:
1. Update `frontend/next.config.ts` to enable static export (if not already)
2. Create `frontend/nginx.conf` for SPA routing
3. Create `frontend/Dockerfile` with multi-stage build:
   - Build stage: Node.js 20 with `npm ci && npm run build`
   - Runtime stage: nginx:alpine with static assets
4. Configure nginx to serve on port 80
5. Build image locally to verify correctness

**Validation / Exit Criteria**:
- [ ] `docker build -t todo-frontend:dev frontend/` completes without errors
- [ ] Image size is minimal (< 100MB)
- [ ] `docker run --rm -p 8080:80 todo-frontend:dev` serves the app at localhost:8080
- [ ] SPA routing works (refresh on /chat doesn't 404)

---

### Stage 4: Helm Chart Structure

**Goal**: Create the Helm chart directory structure with metadata files.

**Actions**:
1. Create `helm/todo-chatbot/` directory
2. Create `Chart.yaml` with:
   - Name: todo-chatbot
   - Version: 0.1.0
   - App Version: 1.0.0
   - Description: Todo Chatbot Kubernetes deployment
3. Create `values.yaml` with all configurable values (per contracts/helm-values-schema.md)
4. Create `values-local.yaml` with Minikube-specific defaults
5. Create `templates/_helpers.tpl` with common template functions

**Validation / Exit Criteria**:
- [ ] `helm lint helm/todo-chatbot` passes with no errors
- [ ] Chart.yaml contains required fields
- [ ] values.yaml documents all configuration options

---

### Stage 5: Backend Kubernetes Resources

**Goal**: Create Helm templates for backend deployment, service, configmap, and secret.

**Actions**:
1. Create `templates/backend/deployment.yaml`:
   - Single replica
   - Image from values
   - Environment variables from ConfigMap and Secret
   - Liveness and readiness probes on /health
   - Resource limits
2. Create `templates/backend/service.yaml`:
   - ClusterIP type
   - Port 8000
3. Create `templates/backend/configmap.yaml`:
   - Non-sensitive configuration
4. Create `templates/backend/secret.yaml`:
   - DATABASE_URL, JWT_SECRET, GEMINI_API_KEY

**Validation / Exit Criteria**:
- [ ] `helm template` renders valid YAML for backend resources
- [ ] All {{ .Values.* }} references exist in values.yaml
- [ ] Secret data is base64 encoded in template
- [ ] Probes point to correct endpoint and port

---

### Stage 6: Frontend Kubernetes Resources

**Goal**: Create Helm templates for frontend deployment, service, and configmap.

**Actions**:
1. Create `templates/frontend/deployment.yaml`:
   - Single replica
   - Image from values
   - Liveness (TCP) and readiness (HTTP) probes
   - Resource limits
2. Create `templates/frontend/service.yaml`:
   - NodePort type
   - Port 80
3. Create `templates/frontend/configmap.yaml`:
   - Build-time configuration (for documentation)

**Validation / Exit Criteria**:
- [ ] `helm template` renders valid YAML for frontend resources
- [ ] NodePort service correctly exposes port 80
- [ ] All template variables resolve to values

---

### Stage 7: Image Loading to Minikube

**Goal**: Build Docker images directly in Minikube's Docker daemon.

**Actions**:
1. Configure shell to use Minikube's Docker: `eval $(minikube docker-env)`
2. Build backend image: `docker build -t todo-backend:dev backend/`
3. Build frontend image: `docker build -t todo-frontend:dev frontend/`
4. Verify images are available in Minikube

**Validation / Exit Criteria**:
- [ ] `docker images` (in Minikube env) shows both todo-backend:dev and todo-frontend:dev
- [ ] Images have correct tags matching values.yaml defaults

---

### Stage 8: Helm Deployment

**Goal**: Deploy the complete application to Minikube using Helm.

**Actions**:
1. Create namespace: `kubectl create namespace todo-chatbot`
2. Prepare secrets (DATABASE_URL, JWT_SECRET, GEMINI_API_KEY)
3. Install Helm release with secrets:
   ```
   helm install todo-app ./helm/todo-chatbot \
     --namespace todo-chatbot \
     --set backend.secrets.databaseUrl="..." \
     --set backend.secrets.jwtSecret="..." \
     --set backend.secrets.geminiApiKey="..."
   ```
4. Wait for pods to reach Running state

**Validation / Exit Criteria**:
- [ ] `helm list -n todo-chatbot` shows todo-app as deployed
- [ ] `kubectl get pods -n todo-chatbot` shows both pods Running
- [ ] `kubectl get svc -n todo-chatbot` shows both services
- [ ] Pod events show successful image pull and container start

---

### Stage 9: End-to-End Validation

**Goal**: Verify the deployed application works correctly.

**Actions**:
1. Access frontend via Minikube service URL
2. Verify frontend loads in browser
3. Verify backend health check passes
4. Test chat functionality (send message, receive response)
5. Test task management (create, list, complete task)
6. Verify logs are accessible via kubectl

**Validation / Exit Criteria**:
- [ ] `minikube service todo-frontend -n todo-chatbot` opens browser
- [ ] Chat interface loads without errors
- [ ] Can send a message and receive AI response
- [ ] Can create and manage tasks
- [ ] `kubectl logs -n todo-chatbot deploy/todo-backend` shows request logs
- [ ] Application behaves identically to non-containerized version

---

### Stage 10: Configuration Validation

**Goal**: Verify Helm value overrides work correctly.

**Actions**:
1. Test upgrading release with modified values
2. Verify pod restarts with new configuration
3. Test rollback capability
4. Document common configuration changes

**Validation / Exit Criteria**:
- [ ] `helm upgrade` applies configuration changes
- [ ] Pods restart and reflect new configuration
- [ ] `helm rollback` restores previous state
- [ ] quickstart.md documents configuration patterns

---

## Assumptions

1. Minikube can be started with default driver (Docker Desktop on macOS/Windows, native on Linux)
2. External Neon PostgreSQL database is accessible from within Minikube cluster (outbound internet)
3. User has valid GEMINI_API_KEY for AI functionality
4. Docker Desktop or equivalent is installed and running
5. No firewall or network policies block Minikube networking

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| External DB connectivity from Minikube | Medium | High | Test connectivity early; document network requirements |
| Image build failures due to dependencies | Low | Medium | Pin dependency versions; test builds before Helm deployment |
| Minikube resource constraints | Medium | Medium | Document minimum requirements; provide troubleshooting guide |
| Frontend build fails (Next.js export) | Low | Medium | Verify static export configuration before containerization |
| Secret exposure in logs | Low | High | Use Kubernetes Secrets; avoid logging sensitive values |

---

## Ready-for-Implementation Checklist

Before proceeding to `/sp.tasks`:

- [x] Specification approved (spec.md complete)
- [x] Research complete (research.md)
- [x] Resource model defined (data-model.md)
- [x] Quickstart guide drafted (quickstart.md)
- [x] Helm values contract defined (contracts/helm-values-schema.md)
- [x] Constitution check passed
- [x] All NEEDS CLARIFICATION items resolved
- [x] Risks identified with mitigations
- [x] Exit criteria defined for all stages

**Plan Status**: READY FOR TASK BREAKDOWN

---

## Complexity Tracking

No complexity violations. This implementation follows Constitution Principle V (Simplicity):
- Single Helm chart (not multiple charts)
- Standard Kubernetes patterns (Deployment, Service, ConfigMap, Secret)
- No custom operators or CRDs
- No external dependencies beyond what's specified
