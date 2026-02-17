
-- Migration to create the missing QUANTIFIRE_TRIGGERED_LEADS table
-- Based on the schema of PULSEPOINT_STRATEGIC_TRIGGERED_LEADS

create table if not exists "public"."QUANTIFIRE_TRIGGERED_LEADS" (
    "id" uuid not null default gen_random_uuid(),
    "triggered_company_id" uuid,
    "name" text,
    "title" text,
    "email" text,
    "contact_status" text default 'pending'::text,
    "email_subject" text,
    "email_body" text,
    "thread_id" text,
    "last_message_id" text,
    "last_sent_at" timestamp with time zone,
    "nudge_count" integer default 0,
    "next_nudge_at" timestamp with time zone,
    "replied_at" timestamp with time zone,
    "bounced_at" timestamp with time zone,
    "is_selected" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "linkedin_url" text,
    "linkedin_profile_picture_url" text,
    "last_linkedin_interaction_at" timestamp with time zone,
    "video_pitch_sent" boolean default false,
    "linkedin_comment_draft" text,
    "video_script" text,
    "loom_link" text,
    "intent_score" text,
    "meeting_booked" boolean default false,
    "meeting_booked_at" timestamp with time zone,
    "pipeline_value" integer default 0,
    "signal_type" text,
    "confidence_score" numeric,
    "deal_score" numeric,
    "signal_date" date,
    "recency_days" integer,
    "why_now" text,
    "evidence_quote" text,
    "source_url" text,
    constraint "QUANTIFIRE_TRIGGERED_LEADS_pkey" primary key ("id")
);

-- Add Foreign Key to triggered_companies if needed (usually good practice)
-- alter table "public"."QUANTIFIRE_TRIGGERED_LEADS" add constraint "QUANTIFIRE_TRIGGERED_LEADS_triggered_company_id_fkey" foreign key ("triggered_company_id") references "public"."triggered_companies" ("id") on delete cascade;

-- Enable RLS
alter table "public"."QUANTIFIRE_TRIGGERED_LEADS" enable row level security;

-- Create Policy (Allow all for now, or match existing policies)
create policy "Enable all access for service role"
on "public"."QUANTIFIRE_TRIGGERED_LEADS"
as permissive
for all
to service_role
using (true)
with check (true);

-- Optional: Allow authenticated access if needed for dashboard
create policy "Allow authenticated access"
on "public"."QUANTIFIRE_TRIGGERED_LEADS"
as permissive
for all
to authenticated
using (true)
with check (true);
