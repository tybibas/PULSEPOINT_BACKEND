-- Create Dashboard User for PulsePoint Strategic (and Command F for testing)
-- User: tbibas@usc.edu
-- Context: pulsepoint_strategic, command_f

-- Ensure the user exists in auth.users first. 
-- This script will only insert/update if the user already exists in Authentication.

INSERT INTO public.quantifire_dashboard_users (id, email, client_context, role)
SELECT 
  id, 
  email, 
  ARRAY['pulsepoint_strategic', 'command_f'], -- Updated to array type with multiple contexts for testing
  'admin'
FROM auth.users
WHERE email = 'tbibas@usc.edu'
ON CONFLICT (id) DO UPDATE SET 
  -- For testing purposes, we explicitly set both contexts to verify the switcher functionality.
  client_context = ARRAY['pulsepoint_strategic', 'command_f'],
  role = 'admin';

-- NOTE: If no rows are affected, it means the user 'tbibas@usc.edu'
-- does not exist in your Supabase Authentication (auth.users) table.
-- You must Create/Invite the user in the Supabase Dashboard first.
