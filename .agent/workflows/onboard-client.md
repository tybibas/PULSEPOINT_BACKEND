---
description: Onboard a new client to the QuantiFire triggered outreach system
---

# /onboard-client

This workflow onboards a new client for triggered outreach, including setting up their Client Intelligence Profile (CIP).

## Input Format

The user will provide:
```
/onboard-client

Company: [COMPANY NAME]
Website: [COMPANY WEBSITE]
Past Clients: [LIST 2-3 PAST CLIENTS OR TESTIMONIALS]
Geographic Focus: [CITY/REGION]

--- New CIP Config ---
Tone: [e.g. Consultative, Direct, Professional]
Value Proposition: [1-2 sentences on the core problem solved]
Forbidden Phrases: [Comma-separated list]
Avg Deal Size: [Amount in USD]
Sales Cycle: [Days]
Target Titles: [List of decision maker titles]
```

> The agent will scrape the website to understand all services/offerings.

---

## Steps

### 1. Create Client Directory
```bash
# turbo
mkdir -p {client_slug}/directives {client_slug}/leads {client_slug}/.tmp
```
Where `{client_slug}` = lowercase company name with underscores (e.g., `acme_corp`)

### 2. Scrape Website & Create ICP Definition
- Scrape the client's website (homepage, about, services, portfolio)
- Analyze past clients provided to identify patterns
- Create `{client_slug}/directives/icp_definition.md` containing:
  - Primary segments (industry types)
  - Target titles (decision-makers) - *Sync with CIP config*
  - Company size indicators
  - Geographic scope
  - Keywords for news searches

### 3. Create Client Intelligence Profile (Database)
Create a SQL file `{client_slug}/migrations/01_create_client_profile.sql` with the following:

```sql
-- 1. Create Strategy
INSERT INTO client_strategies (slug, name, sourcing_criteria)
VALUES ('{client_slug}', '{Client Name}', '{{}}'::jsonb)
ON CONFLICT (slug) DO NOTHING;

-- 2. Create/Update Profile
INSERT INTO client_profiles (strategy_id, commercial_config, scoring_config, voice_config)
SELECT 
  id,
  '{{ "average_deal_size": {DEAL_SIZE}, "sales_cycle_days": {CYCLE_DAYS}, "currency": "USD" }}'::jsonb,
  '{{ "decision_maker_titles": {TITLES_JSON_ARRAY}, "minimum_score_threshold": 60, "signal_weights": {{ "funding": 15, "hiring": 10, "expansion": 10 }} }}'::jsonb,
  '{{ "tone": "{TONE}", "value_proposition": "{VALUE_PROP}", "forbidden_phrases": {FORBIDDEN_ARRAY}, "cta_style": "soft" }}'::jsonb
FROM client_strategies WHERE slug = '{client_slug}'
ON CONFLICT (strategy_id) DO UPDATE SET
  commercial_config = EXCLUDED.commercial_config,
  scoring_config = EXCLUDED.scoring_config,
  voice_config = EXCLUDED.voice_config;
```

**Run this SQL in Supabase SQL Editor.**

### 4. Define Trigger Strategy
Create `{client_slug}/directives/trigger_strategy.md` containing:
- 2-5 trigger event types relevant to the client's service
- Search keywords for each trigger type
- Examples of what qualifies vs. what to ignore

### 5. Source ICP-Fit Leads (Automated)
Run the lead sourcing script:
```bash
python execution/source_icp_leads.py \
  --icp "{client_slug}/directives/icp_definition.md" \
  --output "{client_slug}/leads/leads.json" \
  --client "{CLIENT_NAME}" \
  --max 15
```

### 6. Enrich Emails (if needed)
If contacts need email enrichment:
```bash
python execution/find_lead_emails.py --input {client_slug}/leads/leads.json
```

### 7. Draft Emails
For each lead in the JSON, add:
- `email_subject`: Personalized, references trigger
- `email_body`: 3-4 sentences, clear CTA, matches client voice
- **Note:** The `generate-research-brief` Edge Function now handles dynamic AI voice, so this step mainly validating the approach.

### 8. Create Client Leads Table
1. Copy the template: `pulsepoint_strategic/migrations/00_create_client_leads_table_TEMPLATE.sql`
2. Replace `{CLIENT_NAME}` with uppercase client name (e.g., `ACME_CORP`)
3. Run in Supabase SQL Editor

### 9. Export Leads to SQL
```bash
python execution/export_client_leads.py \
  --client "{CLIENT_NAME}" \
  --input {client_slug}/leads/leads.json \
  --output ~/Desktop/
```

### 10. Import to Supabase
Run the generated `{CLIENT_NAME}_seed.sql` in Supabase SQL Editor.

### 11. Add Client to Modal Backend
Follow: `directives/add_new_client_to_modal.md`

1. Add entry to `CLIENT_STRATEGIES` in `execution/monitor_companies_job.py`
2. Deploy to Modal: `modal deploy execution/monitor_companies_job.py`
3. Add dashboard user in `quantifire_dashboard_users` with `client_context` = `{client_slug}`

### 12. Notify User
Provide:
- SQL seed file location
- Bolt prompt for dashboard wiring (auto-generated)
- Summary of leads created
- Verification steps completed

---

## Outputs

| File | Purpose |
|------|---------|
| `{client_slug}/migrations/01_create_client_profile.sql` | CIP Database Config |
| `{CLIENT_NAME}_seed.sql` | SQL for Leads Import |
| `{CLIENT_NAME}_bolt_prompt.md` | Dashboard wiring instructions |
| `{client_slug}/directives/icp_definition.md` | ICP documentation |

---

## Reference Directives

- Full SOP: `directives/client_onboarding.md`
- Modal integration: `directives/add_new_client_to_modal.md`

