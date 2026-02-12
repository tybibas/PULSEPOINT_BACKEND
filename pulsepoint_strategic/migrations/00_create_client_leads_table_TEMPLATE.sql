-- ============================================================================
-- CLIENT LEADS TABLE TEMPLATE
-- ============================================================================
-- Usage: Replace {CLIENT_NAME} with the uppercase client name (e.g., ACME_CORP)
-- Run this in Supabase SQL Editor BEFORE importing leads.
-- ============================================================================

-- Create the client-specific leads table
CREATE TABLE IF NOT EXISTS public."{CLIENT_NAME}_TRIGGERED_LEADS" (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    triggered_company_id UUID REFERENCES public.triggered_companies(id) ON DELETE CASCADE,
    
    -- Contact Info
    name TEXT NOT NULL,
    title TEXT,
    email TEXT NOT NULL,
    linkedin_url TEXT,
    
    -- Outreach Status
    contact_status TEXT DEFAULT 'pending' CHECK (contact_status IN ('pending', 'scheduled', 'sent', 'opened', 'replied', 'bounced', 'failed')),
    
    -- Email Content (drafted by agent or user)
    email_subject TEXT,
    email_body TEXT,
    
    -- Selection for batch operations
    is_selected BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    replied_at TIMESTAMPTZ,
    
    -- Prevent duplicate contacts per company
    UNIQUE(triggered_company_id, email)
);

-- Create index for fast lookups by company
CREATE INDEX IF NOT EXISTS idx_{client_name_lower}_leads_company 
ON public."{CLIENT_NAME}_TRIGGERED_LEADS"(triggered_company_id);

-- Create index for status filtering
CREATE INDEX IF NOT EXISTS idx_{client_name_lower}_leads_status 
ON public."{CLIENT_NAME}_TRIGGERED_LEADS"(contact_status);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE public."{CLIENT_NAME}_TRIGGERED_LEADS" ENABLE ROW LEVEL SECURITY;

-- Create policy for authenticated users (adjust as needed)
CREATE POLICY "Enable all for authenticated users" 
ON public."{CLIENT_NAME}_TRIGGERED_LEADS"
FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

-- ============================================================================
-- VERIFICATION
-- ============================================================================
-- Run this to verify the table was created:
-- SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%TRIGGERED_LEADS';
