-- PULSEPOINT_STRATEGIC - SEED DATA
-- Generated: 2026-02-17T12:08:59.313720
-- Run this in the Supabase SQL Editor.

BEGIN;

-- 1. INSERT COMPANIES
--------------------------------------------------------------------------------
INSERT INTO public.triggered_companies (
    id, 
    company, 
    event_type, 
    event_title, 
    event_context, 
    event_source_url, 
    created_at
)
VALUES
    (
        'e3aacb59-e701-5a49-86cf-a9a88edf7010', 
        'COHO Creative', 
        'Branding and Design Agency Recognition', 
        'Featured in ''Top brand design agencies''', 
        'COHO Creative has been highlighted as one of the top brand design agencies, indicating recognition and potential new projects. The agency operates within the design industry and aligns with the target profile.', 
        'https://www.cohocreative.com/news/tag/Top+brand+design+agencies',
        NOW()
    ),
    (
        '8d93647a-7579-519a-a53a-4a8b68196c20', 
        'Focus Lab', 
        'Industry Insight', 
        'State of Creative Agencies in 2025', 
        'Focus Lab CEO, Bill Kenney, discussed trends and future directions for creative agencies in a recent dialogue. This reflects a proactive approach to industry changes.', 
        'https://focuslab.agency/blog/creative-agencies-in-2025-trends-advice-and-whats-next',
        NOW()
    ),
    (
        'b9dca186-9e53-541a-9113-d57d36fbf6d9', 
        'RJP.design', 
        'New Account Win', 
        'Top Web Design Agencies in NYC - February 2026 Edition', 
        'RJP.design has been ranked as the top web design agency in NYC, indicating recent recognition and potential new business opportunities.', 
        'https://www.openpr.com/news/4392881/top-web-design-agencies-in-nyc-february-2026-edition',
        NOW()
    ),
    (
        '295f6c68-fb9c-53f0-b10c-2e85e2d4a824', 
        'Bellweather Agency', 
        'Recognition', 
        'Ranked Top 20 Branding Agencies', 
        'Bellweather Agency has been recognized as a Top 20 New York Branding Agency, indicating a significant achievement within the creative industry.', 
        'https://bellweather.agency/news/bellweather-agency-ranked-top-20-branding-agencies-in-new-york/',
        NOW()
    ),
    (
        'e5b247f9-3807-5891-9212-213de8ad97fa', 
        'Walrus, Contino Studio, &Walsh', 
        'New Account Win / Award Recognition', 
        'Top Creative Agencies Recognition', 
        'Walrus, Contino Studio, and &Walsh are notable creative agencies that have been recognized for their outstanding work through numerous awards, highlighting their effectiveness and reputation in the industry.', 
        'https://www.superside.com/blog/creative-agencies-new-york',
        NOW()
    )
ON CONFLICT (id) DO UPDATE SET event_title = EXCLUDED.event_title;

-- 2. INSERT LEADS INTO PULSEPOINT_STRATEGIC_TRIGGERED_LEADS
--------------------------------------------------------------------------------
INSERT INTO public."PULSEPOINT_STRATEGIC_TRIGGERED_LEADS" (
    triggered_company_id, 
    name, 
    title, 
    email, 
    contact_status, 
    email_subject, 
    email_body, 
    is_selected,
    created_at,
    updated_at
)
VALUES
    (
        'e3aacb59-e701-5a49-86cf-a9a88edf7010', 
        '[TO BE ENRICHED]', 
        'Decision Maker', 
        '', 
        'pending',
        '', 
        '', 
        true,
        NOW(),
        NOW()
    ),
    (
        '8d93647a-7579-519a-a53a-4a8b68196c20', 
        '[TO BE ENRICHED]', 
        'Decision Maker', 
        '', 
        'pending',
        '', 
        '', 
        true,
        NOW(),
        NOW()
    ),
    (
        'b9dca186-9e53-541a-9113-d57d36fbf6d9', 
        '[TO BE ENRICHED]', 
        'Decision Maker', 
        '', 
        'pending',
        '', 
        '', 
        true,
        NOW(),
        NOW()
    ),
    (
        '295f6c68-fb9c-53f0-b10c-2e85e2d4a824', 
        '[TO BE ENRICHED]', 
        'Decision Maker', 
        '', 
        'pending',
        '', 
        '', 
        true,
        NOW(),
        NOW()
    ),
    (
        'e5b247f9-3807-5891-9212-213de8ad97fa', 
        '[TO BE ENRICHED]', 
        'Decision Maker', 
        '', 
        'pending',
        '', 
        '', 
        true,
        NOW(),
        NOW()
    )
ON CONFLICT (triggered_company_id, email) DO UPDATE
SET 
  email_subject = EXCLUDED.email_subject,
  email_body = EXCLUDED.email_body,
  updated_at = NOW();

COMMIT;