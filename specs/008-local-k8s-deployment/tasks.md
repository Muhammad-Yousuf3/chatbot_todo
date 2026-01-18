# Tasks: Phase IV - Local Kubernetes Deployment

**Input**: Design documents from `/specs/008-local-k8s-deployment/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/helm-values-schema.md

**Tests**: Not explicitly requested in specification. Manual validation steps are included instead.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/` (existing source unchanged)
- **Frontend**: `frontend/` (existing source unchanged)
- **Helm Chart**: `helm/todo-chatbot/`
- **New Dockerfiles**: `backend/Dockerfile`, `frontend/Dockerfile`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Environment verification and Helm chart structure initialization

- [X] T001 Verify Docker is installed and running via `docker --version`
- [X] T002 Verify Minikube is installed (1.30+) via `minikube version`
- [X] T003 Verify kubectl is installed (1.28+) via `kubectl version --client`
- [X] T004 Verify Helm 3.x is installed via `helm version`
- [ ] T005 Start Minikube cluster with `minikube start --cpus=2 --memory=4096` (Docker daemon not running)
- [ ] T006 Verify cluster connectivity via `kubectl cluster-info` (Docker daemon not running)
- [X] T007 Create Helm chart directory structure at helm/todo-chatbot/
- [X] T008 Create Chart.yaml with name: todo-chatbot, version: 0.1.0 in helm/todo-chatbot/Chart.yaml
- [X] T009 Create _helpers.tpl with common template functions in helm/todo-chatbot/templates/_helpers.tpl

**Checkpoint**: Environment ready, Helm chart skeleton exists

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Docker images and base Helm configuration that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Backend Containerization

- [X] T010 Create backend Dockerfile with multi-stage build in backend/Dockerfile
- [ ] T011 Verify backend Dockerfile builds successfully via `docker build -t todo-backend:dev backend/` (Docker daemon not running)
- [ ] T012 Verify backend image size is under 500MB via `docker images todo-backend:dev` (Docker daemon not running)

### Frontend Containerization

- [X] T013 [P] Update next.config.ts to enable static export with output: 'export' in frontend/next.config.ts
- [X] T014 [P] Create nginx.conf for SPA routing (fallback to index.html) in frontend/nginx.conf
- [X] T015 Create frontend Dockerfile with Node.js build + nginx runtime in frontend/Dockerfile
- [ ] T016 Verify frontend Dockerfile builds successfully via `docker build -t todo-frontend:dev frontend/` (Docker daemon not running)
- [ ] T017 Verify frontend image size is under 100MB via `docker images todo-frontend:dev` (Docker daemon not running)

### Helm Base Configuration

- [X] T018 Create values.yaml with all configurable parameters per helm-values-schema.md in helm/todo-chatbot/values.yaml
- [X] T019 Create values-local.yaml with Minikube-specific defaults in helm/todo-chatbot/values-local.yaml
- [X] T020 Verify Helm chart lints successfully via `helm lint helm/todo-chatbot`

**Checkpoint**: Foundation ready - Docker images build, Helm values defined - user story implementation can now begin

---

## Phase 3: User Story 1 - Deploy Application to Local Cluster (Priority: P1) 🎯 MVP

**Goal**: Deploy complete Todo Chatbot to Minikube with both pods Running and accessible endpoints

**Independent Test**: Run `helm install` and verify both pods reach Running state; access frontend via Minikube service URL

### Backend Kubernetes Resources for US1

- [X] T021 [US1] Create backend deployment template with probes in helm/todo-chatbot/templates/backend/deployment.yaml
- [X] T022 [US1] Create backend service template (ClusterIP) in helm/todo-chatbot/templates/backend/service.yaml
- [X] T023 [P] [US1] Create backend configmap template in helm/todo-chatbot/templates/backend/configmap.yaml
- [X] T024 [P] [US1] Create backend secret template (base64 encoded) in helm/todo-chatbot/templates/backend/secret.yaml

### Frontend Kubernetes Resources for US1

- [X] T025 [P] [US1] Create frontend deployment template with probes in helm/todo-chatbot/templates/frontend/deployment.yaml
- [X] T026 [P] [US1] Create frontend service template (NodePort) in helm/todo-chatbot/templates/frontend/service.yaml
- [X] T027 [P] [US1] Create frontend configmap template in helm/todo-chatbot/templates/frontend/configmap.yaml

### Helm Template Validation for US1

- [X] T028 [US1] Verify all templates render correctly via `helm template todo-app helm/todo-chatbot`
- [X] T029 [US1] Verify all .Values references exist in values.yaml

### Minikube Deployment for US1

- [ ] T030 [US1] Configure shell to use Minikube Docker daemon via `eval $(minikube docker-env)`
- [ ] T031 [US1] Build backend image in Minikube Docker via `docker build -t todo-backend:dev backend/`
- [ ] T032 [US1] Build frontend image in Minikube Docker via `docker build -t todo-frontend:dev frontend/`
- [ ] T033 [US1] Create namespace via `kubectl create namespace todo-chatbot`
- [ ] T034 [US1] Install Helm release with secrets via `helm install todo-app ./helm/todo-chatbot --namespace todo-chatbot --set backend.secrets.databaseUrl=... --set backend.secrets.jwtSecret=... --set backend.secrets.geminiApiKey=...`
- [ ] T035 [US1] Verify both pods reach Running state via `kubectl get pods -n todo-chatbot`
- [ ] T036 [US1] Verify backend health check passes via `kubectl exec -n todo-chatbot deploy/todo-backend -- curl -s localhost:8000/health`

### End-to-End Validation for US1

- [ ] T037 [US1] Access frontend via `minikube service todo-frontend -n todo-chatbot`
- [ ] T038 [US1] Verify chat interface loads in browser
- [ ] T039 [US1] Verify chat message sends and receives AI response
- [ ] T040 [US1] Verify task creation and listing works

**Checkpoint**: User Story 1 complete - Application deployed and fully functional in Minikube

---

## Phase 4: User Story 2 - Configure Deployment Parameters (Priority: P2)

**Goal**: Enable Helm value customization without template modification

**Independent Test**: Modify values.yaml, run `helm upgrade`, verify changes reflected in pods

### Configuration Flexibility for US2

- [ ] T041 [US2] Verify image tag override works via `helm upgrade todo-app ./helm/todo-chatbot --set backend.image.tag=v1`
- [ ] T042 [US2] Verify replica count override works via `helm upgrade todo-app ./helm/todo-chatbot --set backend.replicas=2`
- [ ] T043 [US2] Verify resource limit override works via `helm upgrade todo-app ./helm/todo-chatbot --set backend.resources.limits.memory=1Gi`
- [ ] T044 [US2] Verify log level configuration works via `helm upgrade todo-app ./helm/todo-chatbot --set backend.config.logLevel=DEBUG`
- [ ] T045 [US2] Verify secret update triggers pod restart via `helm upgrade todo-app ./helm/todo-chatbot --set backend.secrets.jwtSecret=new-secret`
- [ ] T046 [US2] Verify rollback works via `helm rollback todo-app 1`

**Checkpoint**: User Story 2 complete - Helm configuration is flexible and operational

---

## Phase 5: User Story 3 - Troubleshoot Deployment Issues (Priority: P3)

**Goal**: Health checks report correctly and pod logs provide diagnostic information

**Independent Test**: Misconfigure a value, verify error visibility in pod logs and probe status

### Health Check Validation for US3

- [ ] T047 [US3] Verify backend liveness probe reports correctly via `kubectl describe pod -n todo-chatbot -l app=todo-backend`
- [ ] T048 [US3] Verify backend readiness probe reports correctly via `kubectl get pod -n todo-chatbot -l app=todo-backend -o jsonpath='{.items[0].status.conditions}'`
- [ ] T049 [US3] Verify frontend probes report correctly via `kubectl describe pod -n todo-chatbot -l app=todo-frontend`

### Logging and Diagnostics for US3

- [ ] T050 [US3] Verify backend logs are accessible via `kubectl logs -n todo-chatbot deploy/todo-backend`
- [ ] T051 [US3] Verify frontend logs are accessible via `kubectl logs -n todo-chatbot deploy/todo-frontend`
- [ ] T052 [US3] Verify pod events show meaningful errors on misconfiguration via `kubectl describe pod -n todo-chatbot`
- [ ] T053 [US3] Test failure scenario: Remove required secret and verify clear error message in logs

**Checkpoint**: User Story 3 complete - Troubleshooting tools operational

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and final validation

- [X] T054 [P] Update quickstart.md with final deployment commands in specs/008-local-k8s-deployment/quickstart.md
- [X] T055 [P] Add .dockerignore for backend to exclude .venv and __pycache__ in backend/.dockerignore
- [X] T056 [P] Add .dockerignore for frontend to exclude node_modules in frontend/.dockerignore
- [ ] T057 Run complete quickstart.md validation from fresh state
- [ ] T058 Verify helm uninstall cleanly removes all resources via `helm uninstall todo-app -n todo-chatbot`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T009) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T010-T020)
- **User Story 2 (Phase 4)**: Depends on User Story 1 deployment (T034)
- **User Story 3 (Phase 5)**: Depends on User Story 1 deployment (T034)
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Core deployment
- **User Story 2 (P2)**: Can start after US1 deployment (T034) - Tests configuration changes
- **User Story 3 (P3)**: Can start after US1 deployment (T034) - Tests health checks and logs

### Within Each User Story

- Backend templates can be created in parallel (T023, T024)
- Frontend templates can be created in parallel (T025, T026, T027)
- Image builds must precede Helm install
- Helm install must precede validation tasks

### Parallel Opportunities

**Phase 1 (Setup)**:
- T001-T004 environment checks can run in parallel

**Phase 2 (Foundational)**:
- T013, T014 can run in parallel (different files)
- Backend and frontend Dockerfiles are independent

**Phase 3 (US1)**:
- T023, T024 can run in parallel (configmap, secret)
- T025, T026, T027 can run in parallel (frontend templates)

**Phase 6 (Polish)**:
- T054, T055, T056 can run in parallel (different files)

---

## Parallel Example: User Story 1 Templates

```bash
# Launch all backend config templates together:
Task: "Create backend configmap template in helm/todo-chatbot/templates/backend/configmap.yaml"
Task: "Create backend secret template in helm/todo-chatbot/templates/backend/secret.yaml"

# Launch all frontend templates together:
Task: "Create frontend deployment template in helm/todo-chatbot/templates/frontend/deployment.yaml"
Task: "Create frontend service template in helm/todo-chatbot/templates/frontend/service.yaml"
Task: "Create frontend configmap template in helm/todo-chatbot/templates/frontend/configmap.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T009)
2. Complete Phase 2: Foundational (T010-T020)
3. Complete Phase 3: User Story 1 (T021-T040)
4. **STOP and VALIDATE**: Test full deployment independently
5. Application should be fully functional at this point

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test deployment → **MVP Complete!**
3. Add User Story 2 → Test configuration → Enhanced flexibility
4. Add User Story 3 → Test diagnostics → Production-ready observability
5. Each story adds value without breaking previous functionality

### Suggested MVP Scope

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1)**

This delivers:
- Working Docker images for both services
- Complete Helm chart with all templates
- Deployed application in Minikube
- Functional chat and task management

---

## Summary

| Phase | Task Count | Parallel Tasks | Story |
|-------|------------|----------------|-------|
| Setup | 9 | 4 | - |
| Foundational | 11 | 4 | - |
| User Story 1 | 20 | 7 | P1 (MVP) |
| User Story 2 | 6 | 0 | P2 |
| User Story 3 | 7 | 0 | P3 |
| Polish | 5 | 3 | - |
| **Total** | **58** | **18** | |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- No automated tests specified; validation is manual via kubectl and browser
- All file paths are relative to repository root
- Helm install requires valid secrets for DATABASE_URL, JWT_SECRET, GEMINI_API_KEY
- Images must be built in Minikube's Docker daemon (not host Docker)
