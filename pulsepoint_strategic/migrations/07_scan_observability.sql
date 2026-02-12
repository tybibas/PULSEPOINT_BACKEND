-- Phase 1: Structured Observability for PulsePoint Monitor
-- Creates the monitor_scan_log table for per-company scan telemetry.

CREATE TABLE IF NOT EXISTS monitor_scan_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id UUID REFERENCES triggered_companies(id),
  company_name TEXT,
  client_context TEXT,
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ,
  status TEXT DEFAULT 'running',  -- running | success | error | skipped_budget | skipped_fingerprint
  error TEXT,
  apify_calls INT DEFAULT 0,
  llm_calls INT DEFAULT 0,
  pages_fetched INT DEFAULT 0,
  trigger_found BOOLEAN DEFAULT false,
  trigger_type TEXT,              -- REAL_TIME_DETECTED | CONTEXT_ANCHOR | null
  elapsed_seconds FLOAT,
  scan_batch_id UUID,             -- groups all companies in one cron run
  analysis_log JSONB DEFAULT '[]'::jsonb  -- Phase 6: LLM decision log (added early)
);

CREATE INDEX IF NOT EXISTS idx_scan_log_company ON monitor_scan_log(company_id);
CREATE INDEX IF NOT EXISTS idx_scan_log_batch ON monitor_scan_log(scan_batch_id);
CREATE INDEX IF NOT EXISTS idx_scan_log_started ON monitor_scan_log(started_at DESC);
