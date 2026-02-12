# Adding a New Client to the Modal Backend

> Step-by-step guide for adding a new client to the monitoring system.
> **Strategies are now stored in Supabase** (`client_strategies` table), not in code.

## Prerequisites

- Client has been onboarded (ICP defined, leads researched)
- Supabase table `{CLIENT_SLUG}_TRIGGERED_LEADS` created (or `config.leads_table` set)
- Have the client's:
  - Product/service description
  - Target trigger events
  - Email tone/voice preferences

---

## Step 1: Insert Strategy into Supabase

Insert into `client_strategies` table:

```sql
INSERT INTO client_strategies (
    slug,
    name,
    keywords,
    trigger_prompt,
    trigger_types,
    leads_table,
    draft_context,
    sourcing_criteria,
    config,
    is_active
) VALUES (
    'new_client_slug',
    'New Client Display Name',
    '("keyword1" OR "keyword2" OR "keyword3") news',
    'Determine if this represents a VALID OPPORTUNITY TYPE. Ignore generic news.',
    '["Trigger Type 1", "Trigger Type 2"]'::jsonb,
    'NEW_CLIENT_TRIGGERED_LEADS',
    'My Product: [Name] - [description].
Value Prop: [Main value proposition].

TONE: [Descriptive adjectives]. Like [analogy].
- Be conversational, not corporate
- Reference the specific trigger event
- Keep it SHORT (3-4 sentences max)

EXAMPLE EMAIL:
"Hi {name},

[2-3 sentence example with ideal style]

Best,
[Sender]"',
    '{
        "icp_industries": ["Industry A", "Industry B"],
        "icp_keywords": ["keyword1", "keyword2"],
        "icp_location": "United States",
        "icp_constraints": ["Must have 50+ employees"],
        "icp_negative_keywords": ["government", "nonprofit"],
        "target_count": 50
    }'::jsonb,
    '{
        "leads_table": "NEW_CLIENT_TRIGGERED_LEADS"
    }'::jsonb,
    true
);
```

> **IMPORTANT:** The `slug` value becomes the `client_context` used throughout the system.
> No code changes are needed — the monitor reads strategies from the DB automatically.

---

## Step 2: Create Leads Table

```sql
CREATE TABLE IF NOT EXISTS "NEW_CLIENT_TRIGGERED_LEADS" (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    triggered_company_id UUID REFERENCES triggered_companies(id),
    name TEXT,
    title TEXT,
    email TEXT,
    linkedin_url TEXT,
    contact_status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## Step 3: Add Companies to Monitoring

```sql
INSERT INTO triggered_companies (
    company,
    website,
    client_context,
    monitoring_status,
    last_monitored_at
) VALUES (
    'Target Company Name',
    'targetcompany.com',
    'new_client_slug',  -- MUST match the strategy slug
    'active',
    '2000-01-01'        -- Forces immediate scan
);
```

Or use automated sourcing:
```bash
python execution/source_new_accounts.py --strategy_id "UUID_OF_STRATEGY"
```

---

## Step 4: Deploy & Verify

1. **Deploy** (only needed if code changed, NOT for adding clients):
   ```bash
   cd execution/
   modal deploy monitor_companies_job.py
   ```

2. **Check logs:**
   ```bash
   modal app logs quantifire-monitor-worker
   ```

3. **Run enrichment for the new client:**
   ```bash
   # Option A: Modal (for production)
   modal run execution/enrich_pulsepoint_job.py --client new_client_slug

   # Option B: Local batch (for cleanup)
   python execution/batch_enrich_cleanup.py --client new_client_slug
   ```

4. **Verify in Supabase:**
   - `triggered_companies` → `last_monitored_at` updated
   - `pulsepoint_email_queue` → new drafts with correct `client_context`
   - `NEW_CLIENT_TRIGGERED_LEADS` → contact records

---

## Checklist

- [ ] Strategy row inserted in `client_strategies` with correct `slug`
- [ ] `config.leads_table` matches the actual Supabase table name
- [ ] Leads table created in Supabase
- [ ] Keywords specific enough to avoid noise
- [ ] Trigger prompt clear about accept/reject criteria
- [ ] Example email in `draft_context` matches client's voice
- [ ] Test company added to `triggered_companies`
- [ ] Manual scan triggered and verified
- [ ] Email template added to `pulsepoint_email_templates` with `client_context`

---

## Common Issues

| Problem | Solution |
|---------|----------|
| "No relevant news" for every scan | Keywords too narrow, or companies too obscure |
| Wrong leads table queried | `config.leads_table` doesn't match Supabase table name |
| Drafts not appearing | Check `pulsepoint_email_queue` — might be `client_context` mismatch |
| Monitor not finding strategy | `client_context` in `triggered_companies` doesn't match `slug` in `client_strategies` |
| Enrichment skipping all companies | All companies already have leads in the leads table |
