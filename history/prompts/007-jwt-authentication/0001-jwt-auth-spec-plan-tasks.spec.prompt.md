---
id: "0001"
title: JWT Auth Spec Plan Tasks
stage: spec
date: 2026-01-10
surface: agent
model: claude-opus-4-5-20251101
feature: 007-jwt-authentication
branch: 006-frontend-chat-ui
user: muhammad-yousuf
command: /sp.analyze (then user request for Better Auth migration)
labels: ["authentication", "jwt", "security", "migration", "spec", "plan", "tasks"]
links:
  spec: specs/007-jwt-authentication/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-jwt-authentication/spec.md (created)
  - specs/007-jwt-authentication/plan.md (created)
  - specs/007-jwt-authentication/tasks.md (created)
  - .specify/memory/constitution.md (modified - Better Auth → JWT)
  - CLAUDE.md (modified - added 007 to Active Technologies)
tests:
  - none (spec/plan/tasks only)
---

## Prompt

User requested: "I want Better Auth migration for previous authentication, change previous authentication to Better Auth and it is for backend not frontend."

After clarification that Better Auth is TypeScript-only (incompatible with Python/FastAPI backend), user chose: **FastAPI JWT Auth (Recommended)**.

Full context: Migrate from insecure X-User-Id header authentication to production-ready JWT tokens. User ID must be:
- Stable
- Available to agent layer (DecisionContext.user_id)
- Available to MCP tools
- Logged in observability

## Response snapshot

Created complete SDD artifacts for JWT authentication migration:

1. **spec.md** - 22 functional requirements covering:
   - Token issuance (signup/signin return JWT)
   - Token validation (Authorization: Bearer header)
   - Protected routes (tasks, chat, conversations)
   - User ID propagation to agent/MCP/observability
   - CORS preflight handling

2. **plan.md** - Architecture and migration strategy:
   - Using python-jose[cryptography] for JWT
   - HS256 symmetric signing
   - 24-hour token expiration
   - In-place migration (no parallel systems)

3. **tasks.md** - 25 executable tasks in 6 phases:
   - Phase 1: Dependencies & Configuration (4 tasks)
   - Phase 2: Token Generation (4 tasks)
   - Phase 3: Token Validation (5 tasks)
   - Phase 4: CORS & Preflight (2 tasks)
   - Phase 5: Verification & Cleanup (8 tasks)
   - Phase 6: Constitution & Documentation (2 tasks)

4. **Constitution updated**: Changed "Better Auth" to "JWT (python-jose)" in Technical Constraints (v1.0.0 → v1.1.0)

## Outcome

- ✅ Impact: Complete spec/plan/tasks for secure JWT authentication
- 🧪 Tests: None yet (spec phase)
- 📁 Files: 5 files created/modified
- 🔁 Next prompts: /sp.implement to execute tasks
- 🧠 Reflection: Better Auth is JS-only; discovered incompatibility early and pivoted to appropriate Python solution (JWT with python-jose)

## Evaluation notes (flywheel)

- Failure modes observed: User requested incompatible technology (Better Auth for Python); resolved via clarification
- Graders run and results (PASS/FAIL): PASS - artifacts complete and consistent
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Implement Phase 1 (add python-jose dependency)
