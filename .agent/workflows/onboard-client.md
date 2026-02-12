---
description: Onboard a new client to the QuantiFire triggered outreach system
---

# /onboard-client

This workflow onboards a new client for triggered outreach. Follow these steps in order.

## Input Format

The user will provide:
```
/onboard-client

Company: [COMPANY NAME]
Website: [COMPANY WEBSITE]
Past Clients: [LIST 2-3 PAST CLIENTS OR TESTIMONIALS]
Geographic Focus: [CITY/REGION]
Additional Instructions: [OPTIONAL - ANY SPECIAL REQUIREMENTS]
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
  - Target titles (decision-makers)
  - Company size indicators
  - Geographic scope
  - Keywords for news searches

### 3. Define Trigger Strategy
Create `{client_slug}/directives/trigger_strategy.md` containing:
- 2-5 trigger event types relevant to the client's service
- Search keywords for each trigger type
- Examples of what qualifies vs. what to ignore
- Rationale for each trigger type

### 4. Source ICP-Fit Leads (Automated)
Run the lead sourcing script:
```bash
python execution/source_icp_leads.py \
  --icp "{client_slug}/directives/icp_definition.md" \
  --output "{client_slug}/leads/leads.json" \
  --client "{CLIENT_NAME}" \
  --max 15
```

This will:
- Search for companies matching ICP with recent trigger events
- Analyze each result for relevance
- Find contacts via Apollo (if API key set)
- Output structured JSON

### 5. Enrich Emails (if needed)
If contacts need email enrichment:
```bash
python execution/find_lead_emails.py --input {client_slug}/leads/leads.json
```

### 6. Draft Emails
For each lead in the JSON, add:
- `email_subject`: Personalized, references trigger
- `email_body`: 3-4 sentences, clear CTA, matches client voice

Reference the template: `templates/leads_template.json`

### 7. Create Supabase Table
1. Copy the template: `pulsepoint_strategic/migrations/00_create_client_leads_table_TEMPLATE.sql`
2. Replace `{CLIENT_NAME}` with uppercase client name (e.g., `ACME_CORP`)
3. Run in Supabase SQL Editor

### 8. Export Leads to SQL
```bash
python execution/export_client_leads.py \
  --client "{CLIENT_NAME}" \
  --input {client_slug}/leads/leads.json \
  --output ~/Desktop/
```

### 9. Import to Supabase
Run the generated `{CLIENT_NAME}_seed.sql` in Supabase SQL Editor.

### 10. Add Client to Modal Backend
Follow: `directives/add_new_client_to_modal.md`

1. Add entry to `CLIENT_STRATEGIES` in `execution/monitor_companies_job.py`
2. Deploy to Modal: `modal deploy execution/monitor_companies_job.py`
3. Add test company to `triggered_companies` with correct `client_context`

### 11. Notify User
Provide:
- SQL seed file location
- Bolt prompt for dashboard wiring (auto-generated)
- Summary of leads created
- Verification steps completed

---

## Outputs

| File | Purpose |
|------|---------|
| `{CLIENT_NAME}_seed.sql` | SQL for Supabase import |
| `{CLIENT_NAME}_bolt_prompt.md` | Dashboard wiring instructions |
| `{client_slug}/directives/icp_definition.md` | ICP documentation |
| `{client_slug}/directives/trigger_strategy.md` | Trigger event strategy |
| `{client_slug}/leads/leads.json` | Verified contact data |

---

## Key Scripts Reference

| Script | Purpose |
|--------|---------|
| `execution/source_icp_leads.py` | Automated lead sourcing from ICP |
| `execution/find_lead_emails.py` | Email enrichment (Anymailfinder/Apollo) |
| `execution/export_client_leads.py` | Generate SQL seed + Bolt prompt |
| `execution/monitor_companies_job.py` | Modal backend (add CLIENT_STRATEGIES) |

---

## Reference Directives

- Full SOP: `directives/client_onboarding.md`
- Modal integration: `directives/add_new_client_to_modal.md`
- JSON template: `templates/leads_template.json`
- SQL template: `pulsepoint_strategic/migrations/00_create_client_leads_table_TEMPLATE.sql`
