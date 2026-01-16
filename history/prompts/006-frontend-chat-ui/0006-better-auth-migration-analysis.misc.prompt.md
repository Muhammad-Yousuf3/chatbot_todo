---
id: "0006"
title: Better Auth Migration Analysis
stage: misc
date: 2026-01-10
surface: agent
model: claude-opus-4-5-20251101
feature: 006-frontend-chat-ui
branch: 006-frontend-chat-ui
user: muhammad-yousuf
command: /sp.analyze
labels: ["authentication", "better-auth", "analysis", "constitution-violation"]
links:
  spec: specs/006-frontend-chat-ui/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-frontend-chat-ui/spec.md (read)
  - specs/006-frontend-chat-ui/plan.md (read)
  - specs/006-frontend-chat-ui/tasks.md (read)
  - .specify/memory/constitution.md (read)
  - backend/src/api/deps.py (read)
tests:
  - none (analysis only)
---

## Prompt

You are an expert backend authentication engineer with experience in FastAPI, modern auth systems, and production-grade security.

Goal:
Migrate my existing authentication system to **Better Auth** as the primary authentication provider.

Context:
- Backend: FastAPI (async)
- Database: Neon Postgres
- ORM: SQLModel
- Current auth is either:
  - basic / placeholder auth
  - custom JWT logic
  - or incomplete auth hooks
- Project already has:
  - Agent system
  - MCP tools
  - Observability logging
- Frontend will rely on this auth cleanly (no hacks)

Requirements:
1. Replace existing authentication with **Better Auth**
2. Use Better Auth as:
   - Source of truth for user identity
   - Token/session validation
3. Ensure compatibility with:
   - FastAPI dependencies
   - Async request lifecycle
4. User ID must be:
   - Stable
   - Available to agent layer (DecisionContext.user_id)
   - Available to MCP tools
   - Logged in observability

Tasks:
- Analyze current auth implementation and dependencies
- Identify all places where user identity is assumed or injected
- Propose a clean Better Auth integration architecture
- Define:
  - Auth middleware / dependency
  - Request lifecycle flow
  - Token validation strategy
- Update:
  - API routes
  - Agent engine context creation
  - Observability logging (user_id propagation)
- Ensure unauthenticated requests:
  - Are rejected cleanly
  - Never crash the app
- Ensure OPTIONS / CORS preflight requests bypass auth

Constraints:
- Do NOT break existing API contracts
- Do NOT hardcode secrets
- Read secrets from environment variables
- Prefer composable FastAPI dependencies
- Keep solution production-grade but hackathon-friendly

Deliverables:
1. High-level auth architecture diagram (textual)
2. List of files to modify and why
3. Step-by-step migration plan
4. Risks & edge cases
5. Final checklist before enabling auth in production

Important:
- This is ANALYSIS + PLAN only
- Do NOT implement yet

## Response snapshot

Cross-artifact analysis completed for 006-frontend-chat-ui feature. Found 2 CRITICAL constitution violations:

1. **C1**: Constitution mandates "Better Auth" (L125) but plan implements "Mock Auth with localStorage" (ADR-006-005)
2. **C2**: Spec assumes mock auth acceptable while constitution requires Better Auth

Key findings:
- 28 functional requirements with 100% task coverage (76 tasks)
- 2 ambiguities related to auth persistence and response timing
- 2 underspecification issues (session expiry, auth state detection)
- User's Better Auth request is NOT addressed by current 006-frontend-chat-ui feature

Recommendations:
1. Amend constitution to allow mock auth for hackathon OR create separate 007-better-auth-integration feature
2. Create dedicated spec for Better Auth migration covering FastAPI dependencies, token validation, agent/MCP integration
3. Current backend uses simple X-User-Id header (backend/src/api/deps.py) - needs complete replacement with Better Auth JWT validation

## Outcome

- ✅ Impact: Identified critical constitution violation blocking proper auth implementation
- 🧪 Tests: None (analysis only)
- 📁 Files: 5 files analyzed, 0 modified
- 🔁 Next prompts: /sp.specify for 007-better-auth-integration, OR constitution amendment
- 🧠 Reflection: User's request about Better Auth migration doesn't match current feature (frontend chat UI). Need separate feature spec or constitution amendment to proceed.

## Evaluation notes (flywheel)

- Failure modes observed: User request scope mismatch with active feature
- Graders run and results (PASS/FAIL): Analysis PASS, no implementation
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Create dedicated auth migration feature spec
