-- Add sourcing_criteria column to client_strategies
ALTER TABLE public.client_strategies
ADD COLUMN IF NOT EXISTS sourcing_criteria JSONB DEFAULT '{}'::jsonb;
