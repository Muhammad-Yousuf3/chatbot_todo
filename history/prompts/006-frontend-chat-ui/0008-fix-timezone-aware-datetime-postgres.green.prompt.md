---
id: 0008
title: Fix Timezone-Aware Datetime Postgres Error
stage: green
date: 2026-01-16
surface: agent
model: claude-opus-4-5-20251101
feature: 006-frontend-chat-ui
branch: 006-frontend-chat-ui
user: muhammad-yousuf
command: /sp.analyze
labels: ["debugging", "datetime", "postgres", "fastapi"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/api/routes/auth.py
tests:
  - null
---

## Prompt

You are debugging a FastAPI + SQLModel + asyncpg backend.

Problem:
All POST/PUT/DELETE endpoints return 500.
GET works.
Error shown in logs:
"TypeError: can't subtract offset-naive and offset-aware datetimes"

Task:
1. Find where timezone-aware datetimes (tzinfo=UTC) are being written to Postgres.
2. Postgres columns use TIMESTAMP WITHOUT TIME ZONE, so ONLY naive UTC datetimes must be saved.
3. Fix this by ensuring all created_at / updated_at / completed_at values are naive UTC.
4. If needed, add ONE small helper (e.g. utc_now_naive()) and use it.
5. Do NOT change:
   - database schema
   - migrations
   - auth logic
   - API contracts
   - frontend
6. Make the MINIMUM possible code changes.
7. After fix, auth, tasks, chat POST endpoints must work.

Explain briefly what you changed and why.

## Response snapshot

Found the root cause: `backend/src/api/routes/auth.py:130` used `datetime.now(timezone.utc)` which returns a timezone-aware datetime, while all models use `default_factory=datetime.utcnow` (naive UTC). The mix of aware and naive datetimes caused the error when asyncpg/SQLModel processed them.

Fixed by changing 2 lines in auth.py:
1. Removed `timezone` from import
2. Changed `datetime.now(timezone.utc)` to `datetime.utcnow()`

No helper function needed - this was the only location using timezone-aware datetimes for DB storage.

## Outcome

- Impact: Fixed 500 errors on POST/PUT/DELETE endpoints for auth, tasks, and chat
- Tests: No new tests (minimal fix to existing code)
- Files: 1 file modified (backend/src/api/routes/auth.py)
- Next prompts: Verify endpoints work, run test suite
- Reflection: Always use naive UTC datetimes with TIMESTAMP WITHOUT TIME ZONE columns

## Evaluation notes (flywheel)

- Failure modes observed: Mixing timezone-aware and naive datetimes in same codebase
- Graders run and results (PASS/FAIL): Manual code review PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
