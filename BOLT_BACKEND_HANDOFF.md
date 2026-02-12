# Backend Refactoring Handoff — Frontend Assessment

## What Changed

The backend was refactored for multi-client support and bug fixes. **Strategies are now stored in Supabase** (`client_strategies` table) instead of being hardcoded in Python. All enrichment is now client-aware via a `client_context` parameter.

---

## Webhook Endpoints (all unchanged URLs, updated behavior)

### 1. `manual_scan_trigger` (POST)
**URL:** `https://ty-1239--pulsepoint-monitor-worker-manual-scan-trigger.modal.run`
```
Request:  { "company_id": "uuid", "force_rescan": true|false }
Response: { "status": "started"|"error", "message": "..." }
```
**Change:** Now reads strategy from `client_strategies` DB table based on the company's `client_context` field in `triggered_companies`. No payload change needed.

### 2. `manual_enrich_trigger` (POST)
**URL:** `https://ty-1239--pulsepoint-monitor-worker-manual-enrich-trigger.modal.run`
```
Request:  { "company_id": "uuid", "client_context": "pulsepoint_strategic" }
Response: {
  "status": "success"|"already_enriched"|"no_contacts_found"|"error",
  "message": "...",
  "contacts_found": int,
  "contacts": [{ "name": "...", "email": "...", "title": "..." }]
}
```
**Change:** `client_context` field now actually works — it resolves the correct leads table dynamically from `client_strategies.config.leads_table`. Previously hardcoded to `PULSEPOINT_STRATEGIC_TRIGGERED_LEADS`.

**Frontend action needed:** If the dashboard calls this endpoint, ensure it passes `client_context` from the company record. If omitted, it defaults to `"pulsepoint_strategic"`.

### 3. `source_accounts_trigger` (POST)
**URL:** `https://ty-1239--pulsepoint-monitor-worker-source-accounts-trigger.modal.run`
```
Request:  { "strategy_id": "uuid" }
Response: { "status": "success"|"error", "message": "..." }
```
**Change:** No change to this endpoint's interface.

---

## Supabase Table Changes

### `client_strategies` (existing table, now the canonical source)
All strategy data (keywords, trigger prompts, leads table name, draft context, sourcing criteria) is read from here. Key columns the frontend may need:
- `slug` (TEXT) — the `client_context` identifier (e.g. `"pulsepoint_strategic"`)
- `config` (JSONB) — contains `leads_table` key mapping to the client's leads table name
- `is_active` (BOOL) — whether the strategy is active

### `pulsepoint_email_templates`
- **New column needed:** `client_context` (TEXT) — filters email templates per client. A fallback to `client_context IS NULL` (global default) exists.

### `triggered_companies`
- No schema change. `client_context` column is already used. The monitor now filters by it correctly.

### `pulsepoint_email_queue`
- No schema change. Drafts are still inserted with `triggered_company_id`, `lead_id`, `email_to`, `email_subject`, `email_body`, `status`, `source`, `user_id`.
- `status` is now `"pending"` only if the company has a verified contact email; otherwise `"needs_review"`.

### Leads Tables (per-client)
- Pattern: `{CLIENT_SLUG_UPPER}_TRIGGERED_LEADS` (e.g. `PULSEPOINT_STRATEGIC_TRIGGERED_LEADS`, `MIKE_ECKER_TRIGGERED_LEADS`)
- The exact table name is resolved from `client_strategies.config.leads_table`, with a fallback to the uppercase slug convention.
- Schema is identical across all client leads tables: `id`, `triggered_company_id`, `name`, `title`, `email`, `linkedin_url`, `contact_status`, `created_at`.

---

## What the Frontend Should Check

1. **Enrichment calls:** If calling `manual_enrich_trigger`, pass `client_context` from the company's record. If you're already doing this, no change needed. If hardcoded to `"pulsepoint_strategic"`, parameterize it.

2. **Leads table queries:** If the frontend directly queries a leads table (e.g. `PULSEPOINT_STRATEGIC_TRIGGERED_LEADS`), it now needs to resolve the table name per client. Either:
   - Read `client_strategies.config.leads_table` for the active client, OR
   - Use the convention `{SLUG.upper()}_TRIGGERED_LEADS`

3. **Strategy management:** If the dashboard has any UI for managing strategies/keywords, it should read/write to `client_strategies` table (not a hardcoded config).

4. **Email templates:** If the dashboard manages email templates, add a `client_context` filter to template queries against `pulsepoint_email_templates`.

5. **No breaking changes:** All webhook URLs are the same. Default behavior (when `client_context` is omitted) falls back to `"pulsepoint_strategic"`, so existing PulsePoint-specific frontend code will continue to work unchanged.
