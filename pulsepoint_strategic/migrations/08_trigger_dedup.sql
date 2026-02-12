-- Phase 4: Trigger Deduplication
-- Prevents duplicate emails when the same article appears in consecutive scans.

CREATE TABLE IF NOT EXISTS trigger_dedup (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id UUID REFERENCES triggered_companies(id),
  source_url TEXT NOT NULL,
  trigger_type TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(company_id, source_url)
);

CREATE INDEX IF NOT EXISTS idx_dedup_company ON trigger_dedup(company_id);
