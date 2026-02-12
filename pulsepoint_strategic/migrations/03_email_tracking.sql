-- Migration: Add Email Tracking Columns
-- Run this in Supabase SQL Editor

-- Add tracking columns to pulsepoint_email_queue
ALTER TABLE pulsepoint_email_queue 
ADD COLUMN IF NOT EXISTS tracking_id uuid DEFAULT gen_random_uuid(),
ADD COLUMN IF NOT EXISTS opened_at timestamptz,
ADD COLUMN IF NOT EXISTS open_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS clicked_at timestamptz,
ADD COLUMN IF NOT EXISTS click_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS replied_at timestamptz,
ADD COLUMN IF NOT EXISTS gmail_message_id text,
ADD COLUMN IF NOT EXISTS gmail_thread_id text;

-- Create index for tracking lookups (tracking pixel requests)
CREATE INDEX IF NOT EXISTS idx_email_queue_tracking_id 
ON pulsepoint_email_queue(tracking_id);

-- Create index for reply checking (CRON job)
CREATE INDEX IF NOT EXISTS idx_email_queue_gmail_thread 
ON pulsepoint_email_queue(gmail_thread_id) 
WHERE replied_at IS NULL AND status = 'sent';

-- Create index for sent emails without replies (for CRON efficiency)
CREATE INDEX IF NOT EXISTS idx_email_queue_pending_replies
ON pulsepoint_email_queue(sent_at)
WHERE replied_at IS NULL AND status = 'sent';

COMMENT ON COLUMN pulsepoint_email_queue.tracking_id IS 'UUID used in tracking pixel URL';
COMMENT ON COLUMN pulsepoint_email_queue.opened_at IS 'First time the email was opened';
COMMENT ON COLUMN pulsepoint_email_queue.open_count IS 'Total number of opens';
COMMENT ON COLUMN pulsepoint_email_queue.replied_at IS 'When recipient replied';
COMMENT ON COLUMN pulsepoint_email_queue.gmail_message_id IS 'Gmail API message ID for the sent email';
COMMENT ON COLUMN pulsepoint_email_queue.gmail_thread_id IS 'Gmail thread ID for reply tracking';
