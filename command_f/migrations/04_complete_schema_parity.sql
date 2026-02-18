-- Add remaining missing columns to Command F leads table for full parity
-- Based on comparison with PULSEPOINT_STRATEGIC and QUANTIFIRE schemas

ALTER TABLE "COMMAND_F_TRIGGERED_LEADS"
ADD COLUMN IF NOT EXISTS signal_date DATE,
ADD COLUMN IF NOT EXISTS recency_days INTEGER,
ADD COLUMN IF NOT EXISTS source_url TEXT,
ADD COLUMN IF NOT EXISTS pipeline_value INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS meeting_booked BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS meeting_booked_at TIMESTAMPTZ;

-- Add indexes for new columns if they are likely to be queried
CREATE INDEX IF NOT EXISTS idx_command_f_leads_signal_date 
ON "COMMAND_F_TRIGGERED_LEADS"(signal_date DESC);
