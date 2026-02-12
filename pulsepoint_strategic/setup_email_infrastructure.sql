-- 1. EMAIL QUEUE TABLE
CREATE TABLE IF NOT EXISTS public.pulsepoint_email_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID, 
    email_to TEXT NOT NULL,
    email_subject TEXT NOT NULL,
    email_body TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'sent', 'failed')),
    attempts INT DEFAULT 0,
    last_error TEXT,
    scheduled_for TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    user_id UUID, -- For multi-user support
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_queue_status ON public.pulsepoint_email_queue(status) WHERE status = 'pending';

-- 2. GMAIL OAUTH TOKENS TABLE
-- Stores the refresh token for the sending account (e.g., ty@quantifire.com)
CREATE TABLE IF NOT EXISTS public.gmail_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email TEXT NOT NULL UNIQUE, -- The email address of the sender
    access_token TEXT,
    refresh_token TEXT NOT NULL, -- Critical for offline access
    token_expiry TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to update updated_at automatically
CREATE EXTENSION IF NOT EXISTS moddatetime SCHEMA extensions;

DROP TRIGGER IF EXISTS handle_updated_at_queue ON public.pulsepoint_email_queue;
CREATE TRIGGER handle_updated_at_queue
BEFORE UPDATE ON public.pulsepoint_email_queue 
FOR EACH ROW EXECUTE PROCEDURE extensions.moddatetime (updated_at);

DROP TRIGGER IF EXISTS handle_updated_at_tokens ON public.gmail_oauth_tokens;
CREATE TRIGGER handle_updated_at_tokens
BEFORE UPDATE ON public.gmail_oauth_tokens
FOR EACH ROW EXECUTE PROCEDURE extensions.moddatetime (updated_at);
