-- Create client_strategies table
CREATE TABLE IF NOT EXISTS public.client_strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add strategy_id to triggered_companies
ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS strategy_id UUID REFERENCES public.client_strategies(id);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_triggered_companies_strategy_id ON public.triggered_companies(strategy_id);
