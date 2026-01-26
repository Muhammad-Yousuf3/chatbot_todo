# Data Model: Midnight AI Glass UI Theme

**Feature**: 011-midnight-glass-ui
**Date**: 2026-01-25
**Status**: N/A (UI-only feature)

## Overview

This feature is a **UI-only enhancement**. No new data entities, database changes, or API modifications are required.

## Existing Entities (Read-Only Reference)

The following existing entities will be **displayed** with enhanced styling but are **not modified**:

### Task Entity (Existing)
```typescript
interface Task {
  id: string;
  title: string;
  description: string | null;
  status: 'pending' | 'completed';
  priority: 'low' | 'medium' | 'high';
  tags: string[];
  due_date: string | null;  // ISO 8601
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  reminders: Reminder[];
  recurrence: Recurrence | null;
}
```

### Reminder Entity (Existing)
```typescript
interface Reminder {
  id: string;
  trigger_at: string;
  fired: boolean;
  cancelled: boolean;
  created_at: string;
}
```

### Recurrence Entity (Existing)
```typescript
interface Recurrence {
  id: string;
  recurrence_type: 'daily' | 'weekly' | 'custom';
  cron_expression: string | null;
  next_occurrence: string | null;
  active: boolean;
  created_at: string;
}
```

### Chat Message Entity (Existing)
```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  createdAt: string;
}
```

## UI Component Models (New - Frontend Only)

These are **TypeScript interfaces for UI components**, not database entities:

### Design Tokens
```typescript
interface MidnightTheme {
  colors: {
    background: '#0B0F1A';
    surface: '#12182B';
    surfaceGlass: 'rgba(18, 24, 43, 0.8)';
    accent: {
      start: '#5B8CFF';
      end: '#8B5CF6';
    };
    success: '#22C55E';
    warning: '#FACC15';
    danger: '#EF4444';
    text: {
      primary: '#E5E7EB';
      secondary: '#9CA3AF';
    };
  };
  effects: {
    blur: '12px' | '16px';
    transitionDuration: '150ms' | '200ms' | '250ms';
    hoverLift: '-2px';
  };
}
```

### Glass Card Props
```typescript
interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;  // Enable lift + glow on hover
  padding?: 'none' | 'sm' | 'md' | 'lg';
}
```

### Priority Badge Props
```typescript
interface PriorityBadgeProps {
  priority: 'low' | 'medium' | 'high';
  size?: 'sm' | 'md';
}
```

### Tag Chip Props
```typescript
interface TagChipProps {
  tag: string;
  removable?: boolean;
  onRemove?: () => void;
}
```

## Schema Changes

**None required.** This feature does not modify:
- Database schemas
- API request/response formats
- Backend models
- Authentication/authorization

## Validation Rules

**No new validation rules.** Existing validation in `frontend/lib/utils.ts` remains unchanged:
- TITLE_MIN_LENGTH: 1
- TITLE_MAX_LENGTH: 200
- DESCRIPTION_MAX_LENGTH: 2000
- MAX_TAGS: 10
- MAX_TAG_LENGTH: 50
- MAX_REMINDERS: 5

## State Transitions

**No new state transitions.** Task status flow remains:
- `pending` → `completed` (via complete action)
- `completed` → `pending` (via uncomplete action)
