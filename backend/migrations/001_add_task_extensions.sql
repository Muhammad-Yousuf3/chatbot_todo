-- Migration: Add task extensions for Phase V Part 1 (Dapr Event-Driven)
-- Date: 2026-01-20
-- Description: Adds priority, tags, updated_at columns to tasks table
--              Creates reminders and recurrences tables

-- Add new columns to tasks table
-- Note: We add title as a new column, keeping description for backwards compatibility
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS title VARCHAR(200),
ADD COLUMN IF NOT EXISTS priority VARCHAR(10) NOT NULL DEFAULT 'medium',
ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]',
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW();

-- Migrate existing description to title if title is null
UPDATE tasks SET title = LEFT(description, 200) WHERE title IS NULL;

-- Make title NOT NULL after migration
ALTER TABLE tasks ALTER COLUMN title SET NOT NULL;

-- Create index for tags (GIN for JSONB array queries)
CREATE INDEX IF NOT EXISTS idx_tasks_tags ON tasks USING GIN (tags);

-- Create index for priority
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (priority);

-- Create index for status (if not exists)
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);

-- Create index for due_date (if not exists)
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks (due_date);

-- Update existing tasks to have default priority if null
UPDATE tasks SET priority = 'medium' WHERE priority IS NULL;

-- Update existing tasks to have empty tags array if null
UPDATE tasks SET tags = '[]'::jsonb WHERE tags IS NULL;
