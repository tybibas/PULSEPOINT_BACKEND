# Backend Changes for Bolt - February 2026

## Summary
The Modal backend monitoring system has been significantly enhanced. **No frontend changes are required** for the core functionality, but there are optional improvements you could add.

---

## What Changed in the Backend

### 1. Enhanced Search (3x Coverage)
Each company is now searched with **3 queries** instead of 1:
- General news
- LinkedIn posts/articles
- Press releases (PRNewswire, BusinessWire)

### 2. Extended Date Range
- **Before:** 7 days
- **After:** 14 days

### 3. Full Article Extraction
When a potential trigger is found, the backend now:
1. Fetches the full article text
2. Extracts the exact event date
3. Uses advanced AI scoring to validate

### 4. Per-Client Scan Limits
Each client now has a daily scan limit to control costs:
- `pulsepoint_strategic`: 50 companies/day
- Other clients: 25-30 companies/day

Companies rotate fairly (oldest-scanned-first).

---

## Impact on PulsePoint Dashboard

### No Required Frontend Changes
The existing dashboard will continue to work because:
- Database schema unchanged
- API endpoints unchanged
- Same data flows to frontend

### Optional Enhancements (Nice-to-Have)

1. **Show Event Date in Signals Tab**
   - The `event_title` now includes more accurate summaries
   - Consider adding `last_monitored_at` display to show recency

2. **Monitoring Stats Widget** (Optional)
   - Could show: "50/100 accounts scanned today"
   - Data available in `triggered_companies` table

3. **Source URL Display**
   - `event_source_url` is now more reliably populated
   - Could add a "View Source" link on trigger cards

---

## Database Fields Reference

```sql
-- triggered_companies table
event_type         -- "REAL_TIME_DETECTED" when trigger found
event_title        -- AI-generated summary (now includes date context)
event_source_url   -- Link to source article
last_monitored_at  -- Timestamp of last scan
monitoring_status  -- "active" / "paused"
client_context     -- "pulsepoint_strategic"
```

---

## Questions for You

No action required. This is informational only.

If you want to add the optional monitoring stats widget, let me know and I can provide the query.
