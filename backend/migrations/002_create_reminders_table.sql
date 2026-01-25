-- Migration: Create reminders table
-- Date: 2026-01-20
-- Description: Creates reminders table for task due date notifications

-- Create reminders table
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    trigger_at TIMESTAMP NOT NULL,
    fired BOOLEAN NOT NULL DEFAULT false,
    cancelled BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_reminders_task_id ON reminders (task_id);
CREATE INDEX IF NOT EXISTS idx_reminders_trigger_at ON reminders (trigger_at);

-- Partial index for pending reminders (efficient querying)
CREATE INDEX IF NOT EXISTS idx_reminders_pending ON reminders (fired, cancelled)
WHERE fired = false AND cancelled = false;
