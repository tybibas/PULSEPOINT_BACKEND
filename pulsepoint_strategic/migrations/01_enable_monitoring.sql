-- Migration: Enable Real-Time Monitoring
-- Adds tracking columns to triggered_companies table

-- 1. Add Monitoring Status (active, paused, disabled)
ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS monitoring_status text DEFAULT 'paused';

-- 2. Add Frequency (daily, biweekly, weekly)
ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS monitoring_frequency text DEFAULT 'weekly';

-- 3. Add Last Monitored Timestamp
ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS last_monitored_at timestamptz;

-- 4. Add Search Queries (Array of custom keywords)
ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS search_queries text[];

-- 5. Add Index for performance (Worker queries by status)
CREATE INDEX IF NOT EXISTS idx_monitoring_status ON public.triggered_companies(monitoring_status);

-- 6. Add Contacts column (optional, for CSV storage)
-- If we want to store raw CSV contact data in the company row for simplicity
ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS contact_info jsonb;
