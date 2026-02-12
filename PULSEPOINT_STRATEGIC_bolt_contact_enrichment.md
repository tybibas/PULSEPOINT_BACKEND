# Bolt: Manual Contact Enrichment Integration

## Pre-requisite: Backend Deployment
Ensure the `monitor_companies_job.py` is deployed to Modal. 
Run: `modal deploy execution/monitor_companies_job.py`
Copy the base URL of your deployed app (e.g., `https://ty-1239--pulsepoint-monitor-worker...`).

## Overview

We've added **Just-In-Time Contact Enrichment** to the backend. This means:

1. **Automatic enrichment on trigger**: When a trigger is found, if no contacts exist, the system automatically finds decision-makers and their emails BEFORE the trigger appears in Signals.
2. **Phase 8 Data**: Triggers now include `buying_window` and `outcome_delta` in `score_factors`.
3. **Manual enrichment webhook**: Users can now manually trigger enrichment from the Accounts tab.

---

## Backend Changes Already Deployed

### New Webhook: `manual_enrich_trigger`

**Endpoint:**
```
POST https://YOUR_MODAL_APP_URL/manual_enrich_trigger
```
(Replace `YOUR_MODAL_APP_URL` with your actual Modal app URL, e.g. `https://ty-1239--pulsepoint-monitor-worker-manual-enrich-trigger.modal.run`)

**Request Payload:**
```json
{
  "company_id": "uuid-of-company",
  "client_context": "pulsepoint_strategic"  // optional, defaults to pulsepoint_strategic
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Found 2 contacts",
  "contacts_found": 2,
  "contacts": [
    {"name": "John Smith", "email": "john@company.com", "title": "CEO"},
    {"name": "Jane Doe", "email": "jane@company.com", "title": "CMO"}
  ]
}
```

**Response (Already Enriched):**
```json
{
  "status": "already_enriched", 
  "message": "Company already has 3 contacts",
  "contacts_found": 3,
  "contacts": [...]
}
```

**Response (No Contacts Found):**
```json
{
  "status": "no_contacts_found",
  "message": "No contacts could be found",
  "contacts_found": 0,
  "contacts": []
}
```

---

## Frontend Implementation Required

### 1. Add "Enrich Contacts" Button to Accounts Tab

**Location:** In each account card/row in the Accounts tab

**Design Specifications:**
- Button label: "Find Contacts" or "🔍 Enrich"
- Button style: Secondary/outline style (not primary)
- Position: Right side of each account row, next to existing action buttons

**Show this button when:**
- Account has no contacts (show count indicator: "0 contacts")
- Or always show it but change label based on state

**States:**
| State | Button Label | Style |
|-------|-------------|-------|
| No contacts found | "🔍 Find Contacts" | Secondary, enabled |
| Has contacts | "✅ {count} contacts" | Text only, disabled |
| Loading | "⏳ Searching..." | Secondary, disabled, spinner |
| Error | "⚠️ Retry" | Warning, enabled |

---

### 2. Implement the Enrichment Flow

**When user clicks "Find Contacts":**

```javascript
async function enrichContacts(companyId) {
  // 1. Set loading state
  setEnrichmentStatus(companyId, 'loading');
  
  try {
    // 2. Call the webhook
    const response = await fetch(
      'https://ty-1239--pulsepoint-monitor-worker-manual-enrich-trigger.modal.run',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          company_id: companyId,
          client_context: 'pulsepoint_strategic'
        })
      }
    );
    
    const data = await response.json();
    
    // 3. Handle response
    if (data.status === 'success') {
      // Show success toast
      showToast(`Found ${data.contacts_found} contacts!`, 'success');
      // Refresh the account data to show new contacts
      refreshAccountData(companyId);
    } else if (data.status === 'already_enriched') {
      showToast(`Already has ${data.contacts_found} contacts`, 'info');
    } else if (data.status === 'no_contacts_found') {
      showToast('No contacts found for this company', 'warning');
    } else {
      showToast(data.message || 'Enrichment failed', 'error');
    }
    
    // 4. Reset button state
    setEnrichmentStatus(companyId, 'idle');
    
  } catch (error) {
    setEnrichmentStatus(companyId, 'error');
    showToast('Enrichment failed - please try again', 'error');
  }
}
```

---

### 3. Add Contact Count Indicator to Account Cards

**Show contact count on each account:**

```html
<!-- In account card/row -->
<div class="contact-indicator">
  <span class="contact-count">{contactCount} contacts</span>
  {contactCount === 0 && (
    <button onclick="enrichContacts('{companyId}')" class="btn-enrich">
      🔍 Find Contacts
    </button>
  )}
</div>
```

**Styling:**
- 0 contacts: Red/orange indicator
- 1-2 contacts: Yellow indicator  
- 3+ contacts: Green indicator

---

### 4. Expected Timing

**Important:** Enrichment takes 15-45 seconds because it:
1. Searches Google for the company website
2. Searches LinkedIn for decision-makers
3. Verifies each email via Anymailfinder

**UX Recommendation:**
- Show a loading spinner during enrichment
- Consider showing "This may take up to a minute..."
- Allow user to navigate away (enrichment runs server-side)

---

### 5. Data Refresh After Enrichment

After successful enrichment, the new contacts are in the `PULSEPOINT_STRATEGIC_TRIGGERED_LEADS` table.

**To display contacts for a company:**

```sql
SELECT * FROM "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS"
WHERE triggered_company_id = '{companyId}'
```

Or via Supabase JS client:
```javascript
const { data: contacts } = await supabase
  .from('PULSEPOINT_STRATEGIC_TRIGGERED_LEADS')
  .select('*')
  .eq('triggered_company_id', companyId);
```

---

## Summary of Changes

| Feature | Status | Location |
|---------|--------|----------|
| JIT enrichment on trigger | ✅ Backend deployed | Automatic |
| Manual enrichment webhook | ✅ Backend deployed | Accounts tab |
| "Find Contacts" button | ❌ Needs frontend | Accounts tab |
| Contact count indicator | ❌ Needs frontend | Accounts tab |
| Loading/success states | ❌ Needs frontend | Accounts tab |

---

## Testing

After implementing, test with:
1. Find an account with 0 contacts
2. Click "Find Contacts"
3. Wait 15-45 seconds
4. Verify contacts appear in the UI
5. Try clicking again - should show "already_enriched"
