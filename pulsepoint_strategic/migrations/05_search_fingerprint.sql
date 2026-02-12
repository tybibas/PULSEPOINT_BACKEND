-- Add last_search_hash to triggered_companies for efficiency tracking
ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS last_search_hash TEXT;

COMMENT ON COLUMN public.triggered_companies.last_search_hash IS 'Hash of the previous search result URLs to detect identical news cycles and skip re-analysis.';
