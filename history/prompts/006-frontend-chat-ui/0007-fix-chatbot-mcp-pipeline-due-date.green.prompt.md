---
id: "0007"
title: "Fix chatbot MCP pipeline and due date"
stage: green
date: 2026-01-11
surface: agent
model: claude-opus-4-5
feature: 006-frontend-chat-ui
branch: 006-frontend-chat-ui
user: muhammad-yousuf
command: /sp.implement
labels: ["mcp", "chatbot", "task", "due-date", "bug-fix"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/mcp_server/tools/add_task.py (modified - optional ctx, due_date support)
  - backend/src/mcp_server/tools/list_tasks.py (modified - optional ctx)
  - backend/src/mcp_server/tools/complete_task.py (modified - optional ctx)
  - backend/src/mcp_server/tools/update_task.py (modified - optional ctx)
  - backend/src/mcp_server/tools/delete_task.py (modified - optional ctx)
  - backend/src/mcp_server/schemas.py (modified - due_date in TaskData)
  - backend/src/models/task.py (modified - due_date field)
  - backend/src/api/schemas/tasks.py (modified - due_date in schemas)
  - backend/src/api/routes/tasks.py (modified - due_date handling)
  - backend/src/llm_runtime/executor.py (modified - due_date in tool declaration)
  - frontend/types/index.ts (modified - due_date in Task type)
  - frontend/lib/api.ts (modified - due_date in createTask/updateTask)
  - frontend/hooks/useTasks.ts (modified - due_date in createTask)
  - frontend/app/tasks/page.tsx (modified - date picker, due date display)
  - frontend/components/layout/Header.tsx (modified - removed dashboard)
  - frontend/app/dashboard/ (deleted)
  - frontend/components/dashboard/ (deleted)
tests:
  - Manual MCP tool invocation tests (PASS)
  - Backend import verification (PASS)
  - ToolExecutor tool loading (PASS)
---

## Prompt

Analyze and FIX the chatbot to task creation pipeline end-to-end.

Current Problems:
1. Tasks created via chatbot are NOT saved in database
2. MCP tools exist but are NOT actually invoked by the chatbot agent
3. Dashboard/metrics page needs to be removed from the app
4. Task date (due_date) is NOT supported

Tasks:
A. Fix Chatbot to MCP to Database flow
B. Add DATE support properly
C. Remove dashboard/metrics UI
D. Validation

## Response snapshot

Fixed the chatbot to task creation pipeline by identifying and resolving the MCP tool context issue:

**ROOT CAUSE:**
MCP tools required `ctx: Context` parameter to get database engine, but ToolExecutor called them directly without providing context. The `ctx` was only available via MCP protocol, not direct Python calls.

**SOLUTION:**
1. Made `ctx: Context` optional (default `None`) in all 5 MCP tools
2. Added `_get_db_engine()` helper that falls back to `get_engine()` when ctx is None
3. This allows tools to work both via MCP protocol AND direct ToolExecutor calls

**CHANGES:**
- All MCP tools (add_task, list_tasks, complete_task, update_task, delete_task) now work without ctx
- Added `due_date` field to Task model, MCP schemas, API schemas, frontend types
- Updated add_task tool and ToolExecutor declaration to accept due_date
- LLM can now extract dates from user messages (e.g., "15 January" -> "2026-01-15")
- Task page now shows due dates with visual indicators (overdue=red, due soon=yellow)
- Added date picker to manual task creation form
- Removed Dashboard from navigation and deleted dashboard pages/components
- Added database migration for due_date column

## Outcome

- Impact: Critical - enables core chatbot functionality
- Tests: All manual MCP tests PASS
- Files: 17 (15 modified, 2 deleted)
- Next prompts: Integration testing with actual Gemini API calls
- Reflection: MCP tools designed for protocol-based access need graceful fallbacks when called directly

## Evaluation notes (flywheel)

- Failure modes observed: MCP Context not available when calling tools directly from ToolExecutor
- Graders run and results (PASS/FAIL): PASS - tools execute, database writes succeed
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test with live Gemini API to verify date extraction works
