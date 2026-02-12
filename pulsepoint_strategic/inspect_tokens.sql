-- 1. Check Columns in gmail_oauth_tokens
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'gmail_oauth_tokens';

-- 2. Check Columns in pulsepoint_email_queue
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pulsepoint_email_queue';

-- 3. View the actual Data in tokens table (to see if 'email' or 'user_email' is populated)
SELECT * FROM public.gmail_oauth_tokens LIMIT 5;

-- ---------------------------------------------------------
-- POTENTIAL FIXES (Run these ONLY if you see the issues below)
-- ---------------------------------------------------------

-- FIX A: If the column is named 'email' but we need 'user_email':
-- ALTER TABLE public.gmail_oauth_tokens RENAME COLUMN email TO user_email;

-- FIX B: If the 'user_email' column is missing entirely:
-- ALTER TABLE public.gmail_oauth_tokens ADD COLUMN user_email TEXT UNIQUE;

-- FIX C: If pulsepoint_email_queue is missing 'user_id':
-- ALTER TABLE public.pulsepoint_email_queue ADD COLUMN user_id UUID;
