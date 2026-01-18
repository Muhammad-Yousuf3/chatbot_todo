# Research: Phase IV - Local Kubernetes Deployment

**Feature**: 008-local-k8s-deployment
**Date**: 2026-01-16
**Status**: Complete

---

## Research Questions

### RQ-001: Backend Dockerfile Strategy

**Question**: What is the optimal Dockerfile approach for the FastAPI backend?

**Decision**: Multi-stage build with Python 3.11-slim base

**Rationale**:
- Multi-stage builds separate dependency installation from runtime, reducing image size
- Python 3.11-slim provides minimal footprint (~40MB) while maintaining compatibility
- Project uses `pyproject.toml` with hatchling, so pip install works directly
- uvicorn is already in dependencies for production-ready ASGI server

**Alternatives Considered**:
- Alpine-based image: Rejected due to potential musl vs glibc compatibility issues with some Python packages
- Full Python image: Rejected due to unnecessary size overhead
- Distroless: Rejected as too complex for local development use case

**Implementation Notes**:
- Build stage: Install dependencies from pyproject.toml
- Runtime stage: Copy installed packages and source code only
- Health check via /health endpoint (already exists in main.py:94)

---

### RQ-002: Frontend Dockerfile Strategy

**Question**: What is the optimal Dockerfile approach for the Next.js frontend?

**Decision**: Multi-stage build with Node.js 20 for build, nginx:alpine for runtime

**Rationale**:
- Next.js requires Node.js for build phase (`next build`)
- Static export can be served by lightweight nginx
- Node.js 20 LTS provides stable foundation
- nginx:alpine is ~5MB, highly optimized for static serving

**Alternatives Considered**:
- Node.js runtime with `next start`: Rejected due to larger image size and resource overhead for simple frontend
- Serve via Node's http-server: Rejected as nginx is more production-ready
- Standalone Next.js output: Valid alternative but nginx approach is simpler for Phase IV

**Implementation Notes**:
- Build stage: `npm ci && npm run build`
- Export static files: Next.js 14 supports `output: 'export'` in next.config.ts
- Runtime stage: Copy build output to nginx html directory
- Configure nginx for SPA routing (fallback to index.html)
- Backend URL must be configurable at runtime via environment variable

---

### RQ-003: Kubernetes Service Communication

**Question**: How should frontend and backend communicate within the cluster?

**Decision**: Internal ClusterIP service for backend, NodePort for frontend

**Rationale**:
- Backend does not need external access; frontend calls it via internal DNS
- Kubernetes DNS provides `<service-name>.<namespace>.svc.cluster.local`
- Frontend serves static files; API calls proxied through backend service
- NodePort exposes frontend to host machine without ingress complexity

**Alternatives Considered**:
- LoadBalancer for both: Overkill for local Minikube
- Ingress controller: Explicitly out of scope per spec
- Port-forward only: Less realistic deployment pattern

**Implementation Notes**:
- Backend Service: ClusterIP, port 8000
- Frontend Service: NodePort, port 80 (mapped to high port on host)
- Frontend must know backend URL: Configurable via environment variable at build time or runtime injection

---

### RQ-004: Helm Chart Organization

**Question**: Single chart or multiple charts for the application?

**Decision**: Single umbrella chart with subcomponents

**Rationale**:
- Single `helm install` deploys entire application
- Simplified management for local development
- Values file controls both services
- Matches spec requirement for unified deployment

**Alternatives Considered**:
- Separate charts per service: More complex for local use, better for microservices at scale
- Kustomize instead of Helm: Valid but Helm provides templating benefits specified in requirements

**Implementation Notes**:
- Chart name: `todo-chatbot`
- Templates organized by service: backend/, frontend/
- Shared _helpers.tpl for labels and naming
- values.yaml with service-specific sections

---

### RQ-005: Secret Management for Local Development

**Question**: How should secrets (DB URL, JWT secret, API keys) be managed in Kubernetes?

**Decision**: Kubernetes Secrets with values in values.yaml (base64 encoded in templates)

**Rationale**:
- Local development does not require external secret managers
- Helm templating handles secret creation
- Values can be overridden via --set or values-local.yaml
- Matches Kubernetes native patterns

**Alternatives Considered**:
- External Secrets Operator: Overkill for local development
- ConfigMaps for all config: Insecure for actual secrets
- Sealed Secrets: Adds complexity without benefit for local use

**Implementation Notes**:
- Backend secrets: DATABASE_URL, JWT_SECRET, GEMINI_API_KEY
- Use Kubernetes Secret type Opaque
- Mount as environment variables in pod spec
- Document that production would use proper secret management

---

### RQ-006: Health Check Configuration

**Question**: What health check strategy for Kubernetes probes?

**Decision**: HTTP probes using existing /health endpoint for backend, TCP/HTTP for frontend

**Rationale**:
- Backend already has /health endpoint (main.py:94)
- HTTP probes are more reliable than exec probes
- Readiness probe ensures traffic only routes to ready pods
- Liveness probe enables automatic restart on failure

**Alternatives Considered**:
- Exec probes with curl: More overhead, less Kubernetes-native
- TCP probes only: Less informative about application health
- No probes: Against best practices and spec requirements

**Implementation Notes**:
- Backend:
  - Liveness: GET /health, initialDelaySeconds: 10, periodSeconds: 10
  - Readiness: GET /health, initialDelaySeconds: 5, periodSeconds: 5
- Frontend:
  - Liveness: TCP check on port 80, initialDelaySeconds: 5, periodSeconds: 10
  - Readiness: HTTP GET / on port 80

---

### RQ-007: Minikube Image Loading Strategy

**Question**: How to load locally built images into Minikube?

**Decision**: Build directly in Minikube's Docker daemon using `eval $(minikube docker-env)`

**Rationale**:
- No registry required (explicitly out of scope)
- Images immediately available to Minikube
- Standard documented approach for local Minikube development
- Requires `imagePullPolicy: Never` or `IfNotPresent` in deployments

**Alternatives Considered**:
- `minikube image load`: Valid but slower for iterative development
- Local registry: Adds complexity beyond scope
- Docker Desktop Kubernetes: Different product, not specified

**Implementation Notes**:
- Document shell configuration step in quickstart
- Set imagePullPolicy: IfNotPresent in Helm values
- Image tags should be explicit (not relying on registry)

---

### RQ-008: Frontend Runtime Configuration

**Question**: How does frontend know the backend API URL at runtime?

**Decision**: Build-time environment variable baked into static assets

**Rationale**:
- Next.js static export doesn't support runtime env vars
- Backend URL is known at build time for Minikube (internal service DNS)
- Simpler than runtime config injection
- Acceptable for local development where rebuild is trivial

**Alternatives Considered**:
- Runtime config.js injection: More complex, unnecessary for local
- Kubernetes ConfigMap mounted as file: Doesn't work well with static assets
- Server-side rendering: Overkill for this frontend

**Implementation Notes**:
- Define NEXT_PUBLIC_API_URL at build time
- For Minikube: backend accessible via ClusterIP service from frontend pod
- Frontend fetcher.ts already uses configurable base URL

---

## Technology Decisions Summary

| Decision Area | Choice | Key Reason |
|---------------|--------|------------|
| Backend Base Image | python:3.11-slim | Balance of size and compatibility |
| Frontend Base Image | node:20 + nginx:alpine | Optimal for static Next.js |
| Service Type Backend | ClusterIP | Internal-only access |
| Service Type Frontend | NodePort | Host access without ingress |
| Chart Structure | Single umbrella chart | Simplified local deployment |
| Secret Management | K8s native Secrets | Appropriate for local dev |
| Health Checks | HTTP probes | Existing /health endpoint |
| Image Loading | Minikube Docker env | No registry needed |
| Frontend API Config | Build-time env var | Static export constraint |

---

## Unknowns Resolved

All technical unknowns from the specification have been resolved. No NEEDS CLARIFICATION items remain.

---

## References

- [Docker multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Kubernetes probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Helm chart best practices](https://helm.sh/docs/chart_best_practices/)
- [Minikube handbook](https://minikube.sigs.k8s.io/docs/handbook/)
- [Next.js static export](https://nextjs.org/docs/pages/building-your-application/deploying/static-exports)
