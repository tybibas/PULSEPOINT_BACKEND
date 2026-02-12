-- Migration: Monitoring Refinements & Queue Updates
-- Compatible with Bolt's plan

-- 1. Update Email Queue Status to allow 'draft'
ALTER TABLE public.pulsepoint_email_queue 
DROP CONSTRAINT IF EXISTS pulsepoint_email_queue_status_check;

ALTER TABLE public.pulsepoint_email_queue 
ADD CONSTRAINT pulsepoint_email_queue_status_check 
CHECK (status IN ('pending', 'processing', 'sent', 'failed', 'draft'));

-- 2. Add Source column to Email Queue
ALTER TABLE public.pulsepoint_email_queue 
ADD COLUMN IF NOT EXISTS source text DEFAULT 'manual'; 

-- 3. Ensure Monitoring Columns exist on triggered_companies
ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS monitoring_status text DEFAULT 'paused';

ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS monitoring_frequency text DEFAULT 'weekly';

ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS last_monitored_at timestamptz;

-- 4. NEW: Client Context (The Missing Link)
-- Allows us to distinguish if this company is being monitored for Mike Ecker vs PulsePoint
ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS client_context text DEFAULT 'pulsepoint_strategic'; 
-- Values: 'mike_ecker', 'pulsepoint_strategic', 'sourcepass', 'quantifire'

-- 5. Create Index on monitoring_status
CREATE INDEX IF NOT EXISTS idx_companies_monitoring_status 
ON public.triggered_companies(monitoring_status);

-- 6. Add Website column
ALTER TABLE public.triggered_companies
ADD COLUMN IF NOT EXISTS website text;
