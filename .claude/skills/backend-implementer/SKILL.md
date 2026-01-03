---
name: backend-implementer
description: Implement backend code from approved tasks. Use when writing FastAPI, SQLModel, MCP servers, OpenAI Agents SDK logic, or database integration.
---

# Backend Implementer Skill

## Purpose
Safely implement backend code following specs, plans, and tasks.

## Instructions
- Implement only what the task specifies
- Follow stateless architecture strictly
- AI agents must never access the database directly
- Use MCP tools for all AI-initiated actions
- Keep code readable, minimal, and well-structured
- Assume Better Auth, FastAPI, SQLModel, and Neon DB

## Quality Rules
- No hidden state
- No speculative features
- Clear function boundaries
- Proper error handling

## Do NOT
- Change specs or plans
- Add extra features
- Combine unrelated tasks

## Examples of Use
- "Implement the add_task MCP tool"
- "Write POST /api/{user_id}/chat endpoint"
