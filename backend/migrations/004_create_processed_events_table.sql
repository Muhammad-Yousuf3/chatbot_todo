-- Migration: Create processed_events table for idempotency
-- Date: 2026-01-22
-- Description: Creates processed_events table for event idempotency tracking
-- Reference: data-model.md Section 1.4

-- Create processed_events table for idempotency
CREATE TABLE IF NOT EXISTS processed_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(100) NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    processed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_processed_events_event_id ON processed_events (event_id);
CREATE INDEX IF NOT EXISTS idx_processed_events_event_type ON processed_events (event_type);

-- Create index for cleanup queries (can delete old events after TTL)
CREATE INDEX IF NOT EXISTS idx_processed_events_processed_at ON processed_events (processed_at);

-- Comment on table
COMMENT ON TABLE processed_events IS 'Tracks processed events for idempotency - prevents duplicate event handling';
