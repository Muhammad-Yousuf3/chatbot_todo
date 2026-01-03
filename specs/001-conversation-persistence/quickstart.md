# Quickstart: Conversation Persistence

**Feature Branch**: `001-conversation-persistence`
**Date**: 2026-01-02

## Overview

This guide shows how to use the Conversation Persistence API to create
and manage chat conversations in a stateless manner.

## Prerequisites

- PostgreSQL database (Neon or local)
- Better Auth JWT token for authentication
- Python 3.11+ with FastAPI dependencies

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message (creates conversation if needed) |
| GET | `/api/conversations` | List user's conversations |
| GET | `/api/conversations/{id}` | Get conversation with messages |

## Quick Examples

### 1. Start a New Conversation

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, I need help with my tasks"
  }'
```

**Response**:
```json
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": {
    "id": "789e0123-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Hello, I need help with my tasks",
    "created_at": "2026-01-02T10:30:00Z"
  },
  "messages": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174000",
      "role": "user",
      "content": "Hello, I need help with my tasks",
      "created_at": "2026-01-02T10:30:00Z"
    }
  ]
}
```

### 2. Continue Existing Conversation

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "content": "Add a task to buy groceries"
  }'
```

**Response** includes full message history:
```json
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": {
    "id": "abc12345-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Add a task to buy groceries",
    "created_at": "2026-01-02T10:31:00Z"
  },
  "messages": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174000",
      "role": "user",
      "content": "Hello, I need help with my tasks",
      "created_at": "2026-01-02T10:30:00Z"
    },
    {
      "id": "abc12345-e89b-12d3-a456-426614174000",
      "role": "user",
      "content": "Add a task to buy groceries",
      "created_at": "2026-01-02T10:31:00Z"
    }
  ]
}
```

### 3. List All Conversations

```bash
curl http://localhost:8000/api/conversations \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response**:
```json
{
  "conversations": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Hello, I need help with my...",
      "updated_at": "2026-01-02T10:31:00Z",
      "message_count": 2
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### 4. Get Full Conversation History

```bash
curl http://localhost:8000/api/conversations/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response**:
```json
{
  "conversation": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Hello, I need help with my...",
    "created_at": "2026-01-02T10:30:00Z",
    "updated_at": "2026-01-02T10:31:00Z"
  },
  "messages": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174000",
      "role": "user",
      "content": "Hello, I need help with my tasks",
      "created_at": "2026-01-02T10:30:00Z"
    },
    {
      "id": "abc12345-e89b-12d3-a456-426614174000",
      "role": "user",
      "content": "Add a task to buy groceries",
      "created_at": "2026-01-02T10:31:00Z"
    }
  ]
}
```

## Error Handling

### Validation Error (Empty Message)
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": ""}'
```

**Response** (HTTP 422):
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Message content cannot be empty"
  }
}
```

### Conversation Not Found
```bash
curl http://localhost:8000/api/conversations/invalid-uuid \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response** (HTTP 400):
```json
{
  "error": {
    "code": "INVALID_ID_FORMAT",
    "message": "Conversation ID must be a valid UUID"
  }
}
```

## Statelessness Verification

To verify the system is truly stateless:

1. Send a message to create a conversation
2. Restart the server
3. Continue the conversation with the same `conversation_id`
4. All previous messages should be available

```bash
# Step 1: Create conversation
CONV_ID=$(curl -s -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "First message"}' | jq -r '.conversation_id')

echo "Created conversation: $CONV_ID"

# Step 2: Restart server (manually)
# ...

# Step 3: Continue conversation (should work after restart)
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"conversation_id\": \"$CONV_ID\", \"content\": \"Message after restart\"}"
```

## Next Steps

After implementing this spec, the following specs will build on this foundation:

1. **AI Agent Integration**: AI agents will use conversation history for context
2. **MCP Tools**: Todo management tools will be accessible through conversations
3. **Task Persistence**: Todo items will be stored and managed via the chat interface
