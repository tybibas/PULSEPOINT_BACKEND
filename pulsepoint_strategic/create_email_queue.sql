-- Create the Email Queue Table
CREATE TABLE IF NOT EXISTS public.pulsepoint_email_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link back to the lead (optional, but good for tracking)
    lead_id UUID, 
    
    -- Email Content
    email_to TEXT NOT NULL,
    email_subject TEXT NOT NULL,
    email_body TEXT NOT NULL,
    
    -- Status Tracking
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'sent', 'failed')),
    attempts INT DEFAULT 0,
    last_error TEXT,
    
    -- Timestamps
    scheduled_for TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast polling of pending emails
CREATE INDEX IF NOT EXISTS idx_email_queue_status 
ON public.pulsepoint_email_queue(status) 
WHERE status = 'pending';

-- Trigger to update updated_at automatically
CREATE EXTENSION IF NOT EXISTS moddatetime SCHEMA extensions;

CREATE TRIGGER handle_updated_at 
BEFORE UPDATE ON public.pulsepoint_email_queue 
FOR EACH ROW EXECUTE PROCEDURE extensions.moddatetime (updated_at);
