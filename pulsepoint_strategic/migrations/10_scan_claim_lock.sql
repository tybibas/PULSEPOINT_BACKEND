-- Scan claim locking to prevent duplicate scans when cron and manual trigger overlap.
-- Orchestrator claims before spawn; worker clears on completion.

ALTER TABLE triggered_companies ADD COLUMN IF NOT EXISTS scan_claimed_at TIMESTAMPTZ;

CREATE OR REPLACE FUNCTION claim_company_for_scan(p_company_id UUID, p_cutoff TIMESTAMPTZ)
RETURNS TABLE(claimed BOOLEAN) AS $$
BEGIN
  UPDATE triggered_companies SET scan_claimed_at = now()
  WHERE id = p_company_id AND (scan_claimed_at IS NULL OR scan_claimed_at < p_cutoff);
  RETURN QUERY SELECT FOUND AS claimed;
END;
$$ LANGUAGE plpgsql;
