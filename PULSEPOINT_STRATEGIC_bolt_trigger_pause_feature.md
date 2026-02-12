# Bolt: Trigger Pause & Resume Feature

## What the Backend Now Does

When the monitoring system finds a trigger event for a company:

```python
# Backend sets monitoring_status to "triggered"
supabase.table("triggered_companies").update({
    "event_type": "REAL_TIME_DETECTED",
    "event_title": "Jane Doe appointed CMO at Acme Corp",
    "event_source_url": "https://reuters.com/...",
    "monitoring_status": "triggered"  # ← NEW: Pauses automatic rescanning
}).eq("id", company_id).execute()
```

**Result:** Companies with `monitoring_status = "triggered"` are **excluded from automatic daily scans**.

---

## What the Frontend Needs to Do

### 1. Show Status Badge on Company Cards

For companies in the Signals tab, display their monitoring status:

```javascript
// Possible values for monitoring_status:
// - "active"    → Green badge: "Monitoring"
// - "triggered" → Orange badge: "Trigger Found" 
// - "paused"    → Gray badge: "Paused"
```

### 2. Add "Resume Monitoring" Button

For companies with `monitoring_status = "triggered"`, show a button that resets them to active:

```javascript
async function resumeMonitoring(companyId) {
  await supabase
    .from('triggered_companies')
    .update({ 
      monitoring_status: 'active',
      // Optionally clear the old trigger, or keep it:
      // event_type: null,
      // event_title: null,
      // event_source_url: null
    })
    .eq('id', companyId);
  
  // Refresh the UI
}
```

**UX Guidance:**
- Place button near the trigger event display
- Label: "Search for New Trigger" or "Resume Monitoring"
- Tooltip: "This will include this company in the next monitoring scan"

### 3. Optional: Add "Rescan Now" Button

To immediately trigger a rescan (instead of waiting for next daily run):

```javascript
async function rescanNow(companyId) {
  // First, reset to active so it can be rescanned
  await supabase
    .from('triggered_companies')
    .update({ monitoring_status: 'active' })
    .eq('id', companyId);
  
  // Then trigger the webhook
  await fetch('https://ty-1239--pulsepoint-monitor-worker-manual-scan-trigger.modal.run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ company_id: companyId })
  });
  
  // Show "Scanning..." toast
}
```

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPANY MONITORING FLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   [Company Added]                                               │
│         │                                                        │
│         ▼                                                        │
│   monitoring_status = "active"                                   │
│         │                                                        │
│         ▼                                                        │
│   ┌─────────────────┐                                           │
│   │  Daily Cron Job  │  ← Only scans "active" companies          │
│   │  (9am daily)    │                                           │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│      Trigger Found?                                              │
│        /       \                                                 │
│      YES        NO                                               │
│       │          │                                               │
│       ▼          ▼                                               │
│   Set status   Keep status                                       │
│   "triggered"  "active"                                          │
│       │          │                                               │
│       │          └────────────────────┐                          │
│       ▼                               │                          │
│   [PAUSED FROM AUTO-SCAN]             │                          │
│       │                               │                          │
│       ▼                               │                          │
│   User sees trigger in dashboard      │                          │
│       │                               │                          │
│       ├──── Likes it? ────────────────┼──→ Take action           │
│       │                               │                          │
│       └──── Doesn't like it? ─────────┘                          │
│                   │                                              │
│                   ▼                                              │
│       Click "Resume Monitoring"                                  │
│                   │                                              │
│                   ▼                                              │
│       Set status back to "active"                                │
│                   │                                              │
│                   ▼                                              │
│       [INCLUDED IN NEXT DAILY SCAN] ─────────────────────────────┘
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Reference

**Table:** `triggered_companies`

| Column | Type | Values |
|--------|------|--------|
| `monitoring_status` | text | `"active"`, `"triggered"`, `"paused"` |
| `event_type` | text | `"REAL_TIME_DETECTED"` or null |
| `event_title` | text | AI summary of the trigger event |
| `event_source_url` | text | Link to source article |
| `last_monitored_at` | timestamp | When last scanned |

---

## Summary

1. **No breaking changes** - existing UI continues to work
2. **New feature:** Companies with found triggers are paused from automatic rescans
3. **Required:** Add "Resume Monitoring" button for `monitoring_status = "triggered"`
4. **Optional:** Add "Rescan Now" button to trigger immediate rescan via webhook
