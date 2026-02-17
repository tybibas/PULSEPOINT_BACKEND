-- Create Client Leads Table
-- Client: PULSEPOINT_STRATEGIC

CREATE TABLE IF NOT EXISTS "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    triggered_company_id UUID REFERENCES triggered_companies(id),
    name TEXT,
    title TEXT,
    email TEXT,
    linkedin_url TEXT,
    contact_status TEXT DEFAULT 'pending', -- pending, sent, replied, bounced
    email_subject TEXT,
    email_body TEXT,
    is_selected BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(triggered_company_id, email)
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_pulsepoint_strategic_leads_company 
ON "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS" (triggered_company_id);
