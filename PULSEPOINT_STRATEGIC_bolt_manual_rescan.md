# Bolt: Fix Manual Rescan Functionality

## The Problem

When users toggle frequency to "daily" or click a "Rescan" button, nothing happens because:

1. The backend `get_due_companies()` still checks thresholds
2. There's no way to force an immediate rescan from the dashboard

## What Needs to Change

### 1. Add "Rescan Now" Button

For each company in the Accounts/Signals tab, add a "Rescan Now" button that:

```javascript
async function rescanCompanyNow(companyId) {
  // First, ensure monitoring_status is 'active' (in case it was 'triggered')
  await supabase
    .from('triggered_companies')
    .update({ 
      monitoring_status: 'active',
      last_monitored_at: null  // Force it to be due
    })
    .eq('id', companyId);
  
  // Call the Modal webhook to trigger immediate scan
  try {
    const response = await fetch('https://ty-1239--pulsepoint-monitor-worker-manual-scan-trigger.modal.run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company_id: companyId })
    });
    
    const result = await response.json();
    
    if (result.status === 'started') {
      // Show success toast: "Scanning in background..."
      toast.info('Scanning in background. Results will appear in a few minutes.');
    } else {
      toast.error('Scan failed: ' + result.message);
    }
  } catch (error) {
    toast.error('Network error: ' + error.message);
  }
}
```

### 2. Where to Place the Button

**Option A:** Add to the company row actions (alongside the frequency toggle)
**Option B:** Add to the company detail panel when a company is selected

Recommended: **Option A** - a small "refresh" icon button next to each company row.

### 3. Loading State

While scan is running:
- Show a spinning loader on that company row
- Disable the rescan button
- After ~30-60 seconds, check if `event_title` has changed

### 4. Polling for Results (Optional)

After triggering a rescan, you can poll for results:

```javascript
async function pollForScanResult(companyId, maxAttempts = 6) {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10s
    
    const { data } = await supabase
      .from('triggered_companies')
      .select('event_title, event_type, monitoring_status')
      .eq('id', companyId)
      .single();
    
    if (data.event_type === 'REAL_TIME_DETECTED') {
      toast.success('Trigger found: ' + data.event_title);
      return data;
    }
    
    if (data.monitoring_status === 'triggered') {
      toast.success('Trigger found!');
      return data;
    }
  }
  
  toast.info('Scan complete. No new triggers found.');
  return null;
}
```

---

## Summary

The key change: **Call the Modal webhook directly** instead of relying on the scheduled cron job. The webhook URL is:

```
POST https://ty-1239--pulsepoint-monitor-worker-manual-scan-trigger.modal.run
Body: {"company_id": "uuid-of-company"}
```

This bypasses all threshold logic and immediately scans that specific company.
