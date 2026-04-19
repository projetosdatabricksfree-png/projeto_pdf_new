-- Migration 002: Add preset_id and profile_id to jobs table
ALTER TABLE jobs 
ADD COLUMN IF NOT EXISTS preset_id TEXT DEFAULT 'business_card',
ADD COLUMN IF NOT EXISTS profile_id TEXT DEFAULT 'printing_standard';

-- Add timestamps for state transitions tracking
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS queued_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE;
