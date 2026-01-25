-- Migration: Create recurrences table
-- Date: 2026-01-20
-- Description: Creates recurrences table for recurring task schedules

-- Create recurrences table
CREATE TABLE IF NOT EXISTS recurrences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE UNIQUE,
    recurrence_type VARCHAR(20) NOT NULL,
    cron_expression VARCHAR(100),
    next_occurrence TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_recurrences_task_id ON recurrences (task_id);
CREATE INDEX IF NOT EXISTS idx_recurrences_next_occurrence ON recurrences (next_occurrence);
CREATE INDEX IF NOT EXISTS idx_recurrences_active ON recurrences (active);
