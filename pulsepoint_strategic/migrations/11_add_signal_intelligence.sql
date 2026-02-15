
-- 11_add_signal_intelligence.sql
-- Adds Signal Intelligence columns to the leads table for ranking and context.
-- Target Table: public."PULSEPOINT_STRATEGIC_TRIGGERED_LEADS"

-- 1. Add Columns
ALTER TABLE public."PULSEPOINT_STRATEGIC_TRIGGERED_LEADS"
ADD COLUMN IF NOT EXISTS signal_type TEXT,
ADD COLUMN IF NOT EXISTS confidence_score NUMERIC,  -- 0-10
ADD COLUMN IF NOT EXISTS deal_score INTEGER,        -- 0-100
ADD COLUMN IF NOT EXISTS signal_date DATE,
ADD COLUMN IF NOT EXISTS recency_days INTEGER,
ADD COLUMN IF NOT EXISTS why_now TEXT,              -- Short 1-2 sentence explanation
ADD COLUMN IF NOT EXISTS evidence_quote TEXT,
ADD COLUMN IF NOT EXISTS source_url TEXT;

-- 2. Add Indexes for Sorting/Filtering
CREATE INDEX IF NOT EXISTS idx_pulsepoint_leads_deal_score 
ON public."PULSEPOINT_STRATEGIC_TRIGGERED_LEADS"(deal_score DESC);

CREATE INDEX IF NOT EXISTS idx_pulsepoint_leads_signal_date 
ON public."PULSEPOINT_STRATEGIC_TRIGGERED_LEADS"(signal_date DESC);

CREATE INDEX IF NOT EXISTS idx_pulsepoint_leads_signal_type 
ON public."PULSEPOINT_STRATEGIC_TRIGGERED_LEADS"(signal_type);

-- 3. Update Template (for future clients)
-- (Optional: Copy same ALTERS to 00_create_client_leads_table_TEMPLATE.sql if needed, 
--  but for now we focus on the active client)
