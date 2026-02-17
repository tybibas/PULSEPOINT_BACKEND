## Bolt Prompt: Wire PULSEPOINT_STRATEGIC Dashboard

**Goal:** Connect the "Triggered" tab to the new `PULSEPOINT_STRATEGIC_TRIGGERED_LEADS` table.

**Critical Safety Rules:**
- DO NOT DELETE any existing tables or data.
- DO NOT MODIFY the original `triggered_company_contacts` table.
- Disconnect old references and reconnect to the new table below.

**Table Name:** `PULSEPOINT_STRATEGIC_TRIGGERED_LEADS`

**Schema:** Same as `MIKE_ECKER_TRIGGERED_LEADS`:
- triggered_company_id (uuid, FK to triggered_companies.id)
- name, title, email (text)
- contact_status (text: pending/sent/replied/bounced)
- email_subject, email_body (text)
- is_selected (boolean)
- created_at, updated_at (timestamptz)

**What to Wire:**
1. Query `PULSEPOINT_STRATEGIC_TRIGGERED_LEADS` in the "Triggered" tab.
2. Join with `triggered_companies` on `triggered_company_id` for company context.
3. Use `dispatch-batch-ecker` edge function (or duplicate for this client).

**Expected Result:** 5 leads displayed with full email editing and Gmail dispatch.
