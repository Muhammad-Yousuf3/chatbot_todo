# Data Model: Conversation Persistence

**Feature Branch**: `001-conversation-persistence`
**Date**: 2026-01-02
**Status**: Complete

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL                                   │
│  ┌─────────────┐                                                     │
│  │    User     │  (Better Auth - not managed by this spec)          │
│  │─────────────│                                                     │
│  │ id: string  │                                                     │
│  └──────┬──────┘                                                     │
└─────────┼───────────────────────────────────────────────────────────┘
          │
          │ 1
          │
          ▼ *
┌─────────────────────┐
│    Conversation     │
│─────────────────────│
│ id: UUID [PK]       │
│ user_id: string [FK]│───── References external User
│ title: string       │
│ created_at: datetime│
│ updated_at: datetime│
└──────────┬──────────┘
           │
           │ 1
           │
           ▼ *
┌─────────────────────┐
│      Message        │
│─────────────────────│
│ id: UUID [PK]       │
│ conversation_id: UUID [FK]
│ role: enum          │
│ content: text       │
│ created_at: datetime│
└─────────────────────┘
```

## Entities

### Conversation

Represents a chat session between a user and the AI assistant.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique conversation identifier |
| `user_id` | VARCHAR(255) | NOT NULL, INDEX | Reference to Better Auth user ID |
| `title` | VARCHAR(255) | NOT NULL, DEFAULT '' | Conversation title/summary |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | When conversation was created |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last activity timestamp |

**Indexes**:
- `conversation_pkey`: PRIMARY KEY on `id`
- `idx_conversation_user_updated`: INDEX on `(user_id, updated_at DESC)` for listing

**Validation Rules**:
- `user_id` must be non-empty string
- `title` max length 255 characters
- `updated_at` >= `created_at`

### Message

Represents a single message within a conversation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique message identifier |
| `conversation_id` | UUID | NOT NULL, FOREIGN KEY → conversation.id, INDEX | Parent conversation |
| `role` | VARCHAR(20) | NOT NULL, CHECK IN ('user', 'assistant', 'system') | Message sender role |
| `content` | TEXT | NOT NULL | Message text content |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | When message was created |

**Indexes**:
- `message_pkey`: PRIMARY KEY on `id`
- `idx_message_conversation_created`: INDEX on `(conversation_id, created_at ASC)` for history

**Validation Rules**:
- `content` must be non-empty (length > 0)
- `content` max length 32,000 characters
- `role` must be one of: 'user', 'assistant', 'system'

**Foreign Key Constraints**:
- `conversation_id` REFERENCES `conversation(id)` ON DELETE CASCADE

## Relationships

### User → Conversation (1:N)
- One user can have many conversations
- Each conversation belongs to exactly one user
- User deletion handling: External to this spec (Better Auth manages users)

### Conversation → Message (1:N)
- One conversation contains many messages
- Each message belongs to exactly one conversation
- Conversation deletion cascades to messages (ON DELETE CASCADE)

## State Transitions

### Conversation States

```
                  ┌──────────────┐
  First message   │              │
  ───────────────►│    ACTIVE    │
                  │              │
                  └──────┬───────┘
                         │
                         │ (Future: archive/delete)
                         ▼
                  ┌──────────────┐
                  │   ARCHIVED   │  (Out of scope for this spec)
                  └──────────────┘
```

Note: This spec only implements ACTIVE state. Archive/delete is out of scope.

### Message Lifecycle

```
  Create request    Validate    Persist    Return
  ─────────────────►─────────►──────────►─────────►
       │               │           │          │
       │               │           │          │
   Input data    Check length   INSERT    Response
                 Check role    in DB     with ID
                 Check empty
```

## SQLModel Schema (Reference)

```python
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(SQLModel, table=True):
    """Chat conversation between user and AI assistant."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True, max_length=255)
    title: str = Field(default="", max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    messages: list["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    """Single message within a conversation."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversation.id", index=True)
    role: MessageRole = Field(max_length=20)
    content: str = Field(max_length=32000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
```

## Database Migration Notes

1. **UUID Extension**: Ensure `uuid-ossp` extension is enabled in PostgreSQL
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   ```

2. **Index Creation**: Create indexes after table creation for performance
   ```sql
   CREATE INDEX idx_conversation_user_updated
   ON conversation (user_id, updated_at DESC);

   CREATE INDEX idx_message_conversation_created
   ON message (conversation_id, created_at ASC);
   ```

3. **Cascade Behavior**: Messages cascade delete with conversation
   ```sql
   ALTER TABLE message
   ADD CONSTRAINT fk_message_conversation
   FOREIGN KEY (conversation_id) REFERENCES conversation(id)
   ON DELETE CASCADE;
   ```
