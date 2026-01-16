---
id: 0004
title: Backend DB Startup Analysis
stage: misc
date: 2026-01-10
surface: agent
model: claude-opus-4-5-20251101
feature: 006-frontend-chat-ui
branch: 006-frontend-chat-ui
user: muhammad-yousuf
command: sp.analyze
labels: ["backend", "database", "postgres", "sqlite", "startup", "debugging"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/main.py (analyzed)
  - backend/src/db/session.py (analyzed)
  - backend/src/db/engine.py (analyzed)
  - backend/src/db/__init__.py (analyzed)
  - backend/src/db/config.py (analyzed)
  - backend/src/api/routes/chat.py (analyzed)
  - backend/src/api/routes/observability.py (analyzed)
  - backend/src/api/routes/conversations.py (analyzed)
  - backend/src/observability/database.py (analyzed)
  - backend/src/observability/query_service.py (analyzed)
  - backend/src/models/conversation.py (analyzed)
  - backend/src/models/task.py (analyzed)
tests:
  - None (analysis only)
---

## Prompt

You are an expert FastAPI + SQLModel backend engineer.

Analyze my entire backend startup, database initialization, and request handling.

Context:
- Backend uses FastAPI, SQLModel, async DB engine
- Database is Neon Postgres
- Neon database currently has NO TABLES
- No Alembic migrations are set up

Symptoms:
- Database initialization fails with: ConnectionRefusedError [Errno 111]
- App starts without DB
- OPTIONS requests to /api/chat and /api/observability/* return 400
- Observability and chat endpoints fail when frontend loads
- Even when DB connects, tables do not exist

Your task:
1. Determine whether DB connection or missing tables are causing startup/runtime failures
2. Identify where schema initialization is missing
3. Decide the best approach:
   - SQLModel.metadata.create_all(engine) OR
   - Alembic migrations (explain tradeoffs)
4. Ensure tables are created automatically if missing
5. Ensure app can start even if DB is unavailable
6. Ensure OPTIONS (CORS preflight) requests NEVER depend on DB
7. Propose a corrected startup + dependency architecture
8. List exact files that need modification and why

Important constraints:
- Do NOT implement yet
- Analysis + fix plan only
- Backend must tolerate empty Neon database and self-heal by creating tables

Analyze all startup hooks, DB engine setup, dependencies, and routers.

## Response snapshot

Comprehensive analysis identified 5 root causes:
1. **Missing model imports in init_db()** - SQLModel.metadata doesn't see table models
2. **SQLite observability DB never initialized** - init_log_db() not called in lifespan
3. **No retry logic for Neon cold starts** - ConnectionRefusedError on startup
4. **Duplicate engine instances** - session.py and engine.py create separate engines
5. **No graceful degradation** - Routes fail with 500 instead of 503 when DB unavailable

Recommended approach: Use SQLModel.metadata.create_all with proper model imports (not Alembic for hackathon speed).

Files requiring modification:
- src/db/__init__.py - Import all SQLModel models
- src/db/session.py - Import models, add retry logic
- src/main.py - Add init_log_db() call in lifespan
- src/api/routes/observability.py - Add error handling
- src/api/routes/chat.py - Add DB error handling
- src/api/routes/conversations.py - Add DB error handling
- src/db/engine.py - Consolidate or remove duplicate

## Outcome

- Impact: Identified architectural flaws blocking frontend integration
- Tests: N/A - analysis only
- Files: 12 files analyzed, 7 require modification
- Next prompts: Implement the fixes per the plan
- Reflection: The model import issue is a common SQLModel pitfall; init_db must see all table classes before create_all

## Evaluation notes (flywheel)

- Failure modes observed: SQLModel metadata not populated, SQLite init never called
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add model imports to db/__init__.py and verify tables are created
