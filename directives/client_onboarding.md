# Client Onboarding SOP

> Universal workflow for onboarding a new client to the QuantiFire triggered outreach system.

## Universal Prompt Template

When starting a new client, use this prompt:

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

## Workflow

### Phase 1: Intake (5 min)
**Input Required:**
- Company name and website
- 2-3 past clients or testimonial examples
- Target geography (e.g., "San Diego, CA")

**Actions:**
1. Scrape the client's website thoroughly (homepage, about, services, portfolio)
2. Extract all services, value propositions, and positioning

**Output:**
- Client subdirectory created: `/{client_slug}/`

---

### Phase 2: ICP Definition (10 min)
**Actions:**
1. Analyze past clients to identify patterns (industry, size, role types)
2. Research the client's website for positioning and value props
3. Create `{client_slug}/directives/icp_definition.md`

**Output:**
- ICP document with:
  - Primary segments (e.g., "Real Estate Developers", "Architects")
  - Target titles (e.g., "Managing Director", "CEO", "Project Manager")
  - Geographic scope
  - Company size indicators

---

### Phase 3: Trigger Event Strategy (15 min)
**Actions:**
1. Based on ICP and service type, identify 2-5 trigger event categories
2. Examples by industry:
   - **Real Estate:** Project completions, awards, new developments
   - **Tech:** Funding rounds, leadership changes, product launches
   - **Professional Services:** New office openings, partnership announcements

**Output:**
- List of 2-5 trigger types with rationale
- Documented in `{client_slug}/directives/trigger_strategy.md`

> After defining ICP and triggers, insert the strategy into Supabase:
> See `directives/add_new_client_to_modal.md` for the SQL template.
> Create the leads table (`{CLIENT_SLUG}_TRIGGERED_LEADS`) at this point.

---

### Phase 4: Lead Research (30 min)
**Actions:**
1. Use automated sourcing to find companies matching ICP with recent trigger events
2. Alternatively, manually search for 10+ companies with verifiable recent news
3. Identify 1-3 contacts per company (decision-maker titles)

**Automated Option:**
```bash
# Option A: DB-driven sourcing (requires strategy row in client_strategies)
python execution/source_new_accounts.py --strategy_id "UUID_OF_STRATEGY"

# Option B: ICP file-driven sourcing
python execution/source_icp_leads.py --icp {client_slug}/directives/icp_definition.md \
  --output {client_slug}/leads/enriched_contacts.json --client "Client Name" --max 20
```

> Both options now write results to Supabase `triggered_companies` automatically.

**Output:**
- Companies inserted into `triggered_companies` with `client_context = '{client_slug}'`
- `{client_slug}/leads/enriched_contacts.json` — Structured data (ICP sourcing)

---

### Phase 5: Email Enrichment (10 min)
**Actions:**
1. Run automated enrichment for the client
2. Fallback to manual enrichment if automated fails

**Automated:**
```bash
# Option A: Modal (production)
modal run execution/enrich_pulsepoint_job.py --client {client_slug}

# Option B: Local batch (with cleanup of unenrichable companies)
python execution/batch_enrich_cleanup.py --client {client_slug}
```

**Output:**
- Decision-maker contacts with verified emails in `{CLIENT_SLUG}_TRIGGERED_LEADS`

---

### Phase 6: Email Drafting (20 min)
**Actions:**
1. For each lead, write personalized email referencing:
   - Specific trigger event (from research)
   - Client's value proposition
   - Clear CTA
2. Follow client's voice/tone if provided

**Output:**
- `email_subject` and `email_body` for each contact
- Stored in export-ready format

---

### Phase 7: Export (5 min)
**Actions:**
1. Run `execution/export_client_leads.py` with client config
2. Generate SQL seed file for Supabase
3. Generate CSV backup

**Script:** `execution/export_client_leads.py`

**Output:**
- `{CLIENT_NAME}_seed.sql` on Desktop
- Ready for Supabase import

---

### Phase 8: Bolt Handoff (5 min)
**Actions:**
1. Generate natural language Bolt prompt
2. Include:
   - New table name
   - Schema reference
   - Dashboard wiring instructions

**Output:**
- Bolt prompt for dashboard integration

---

## File Structure

```
/QuantiFire IDE V3/
├── {client_slug}/
│   ├── directives/
│   │   ├── icp_definition.md
│   │   └── trigger_strategy.md
│   ├── leads/
│   │   └── enriched_contacts.json
│   └── .tmp/
├── execution/
│   ├── shared/
│   │   ├── __init__.py
│   │   └── enrichment_utils.py       # Canonical enrichment functions
│   ├── monitor_companies_job.py      # Trigger monitoring (Modal)
│   ├── enrich_pulsepoint_job.py      # Enrichment (Modal, --client flag)
│   ├── batch_enrich_cleanup.py       # Batch enrichment (local, --client flag)
│   ├── source_new_accounts.py        # Automated sourcing (--strategy_id)
│   └── source_icp_leads.py           # ICP sourcing (--icp, writes to Supabase)
└── directives/
    ├── client_onboarding.md          # This file
    └── add_new_client_to_modal.md    # DB-driven strategy setup
```

---

## Supabase Table Naming Convention

Each client gets their own leads table:
- `{CLIENT_NAME_UPPER}_TRIGGERED_LEADS`
- Example: `MIKE_ECKER_TRIGGERED_LEADS`, `ACME_CORP_TRIGGERED_LEADS`

This ensures complete isolation between client data.

---

## Checklist for Quality

- [ ] All emails verified or pattern-guessed
- [ ] Each email references a specific, real trigger event
- [ ] Trigger event has a source URL
- [ ] Email body follows client's tone/voice
- [ ] SQL seed file tested in Supabase
- [ ] Bolt prompt reviewed before handoff
