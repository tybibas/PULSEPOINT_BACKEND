-- Create Client Leads Table
-- Client: COMMAND_F

CREATE TABLE IF NOT EXISTS "COMMAND_F_TRIGGERED_LEADS" (
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
    
    -- Analysis Fields
    deal_score NUMERIC,
    confidence_score NUMERIC,
    signal_type TEXT,
    why_now TEXT,
    evidence_quote TEXT,
    intent_score TEXT,

    -- Outreach Fields
    thread_id TEXT,
    last_message_id TEXT,
    last_sent_at TIMESTAMPTZ,
    nudge_count INTEGER DEFAULT 0,
    next_nudge_at TIMESTAMPTZ,
    replied_at TIMESTAMPTZ,
    bounced_at TIMESTAMPTZ,

    -- LinkedIn & Media
    linkedin_profile_picture_url TEXT,
    linkedin_comment_draft TEXT,
    video_script TEXT,
    loom_link TEXT,
    last_linkedin_interaction_at TIMESTAMPTZ,
    video_pitch_sent BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(triggered_company_id, email)
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_command_f_leads_company 
ON "COMMAND_F_TRIGGERED_LEADS" (triggered_company_id);
