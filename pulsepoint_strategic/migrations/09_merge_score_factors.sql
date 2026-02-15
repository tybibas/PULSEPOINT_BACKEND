
-- 09_merge_score_factors.sql
-- Defines a function to atomically merge JSONB updates into score_factors
-- Prevents race conditions where parallel scouts might overwrite each other's updates

CREATE OR REPLACE FUNCTION merge_score_factors(p_company_id UUID, p_delta JSONB)
RETURNS VOID AS $$
BEGIN
  UPDATE triggered_companies
  SET score_factors = COALESCE(score_factors, '{}'::jsonb) || p_delta
  WHERE id = p_company_id;
END;
$$ LANGUAGE plpgsql;
