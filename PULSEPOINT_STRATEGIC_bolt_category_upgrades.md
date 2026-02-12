# Bolt: Category-Defining Dashboard Upgrades

## Overview

Transform the PulsePoint dashboard from a trigger detection tool into a **closed-loop sales intelligence platform**. The goal: `Signal → Action → Outcome → Attribution` in one seamless flow.

---

## Phase 1: Trigger Quality Scoring (High Priority)

### 1.1 Add Trigger Quality Badges

The backend now returns a `confidence` score (1-10) with each trigger. Display quality badges:

```javascript
// Mapping logic
function getTriggerTier(confidence, triggerType) {
  // Tier 1: Hot (score 8-10 OR high-value trigger types)
  if (confidence >= 8 || ['New Executive', 'M&A', 'Funding Round', 'Major Rebrand'].includes(triggerType)) {
    return { tier: 'hot', icon: '🔥', color: 'text-red-500', bgColor: 'bg-red-500/20' };
  }
  // Tier 2: Warm (score 6-7)
  if (confidence >= 6) {
    return { tier: 'warm', icon: '⚡', color: 'text-amber-500', bgColor: 'bg-amber-500/20' };
  }
  // Tier 3: Signal (score 4-5)
  return { tier: 'signal', icon: '📊', color: 'text-blue-400', bgColor: 'bg-blue-400/20' };
}
```

**UI Implementation:**
- Add a small pill badge next to the trigger title: `🔥 Hot` / `⚡ Warm` / `📊 Signal`
- Use the appropriate color scheme for the badge background
- Show the tier in the trigger card header, not buried in details

### 1.2 Tier-Based Filtering

Add filter buttons in the Signals tab header:

```
[All (12)] [🔥 Hot (3)] [⚡ Warm (5)] [📊 Signal (4)]
```

Clicking a filter shows only triggers of that tier.

---

## Phase 2: Pipeline & ROI Tracking (High Priority)

### 2.1 Add Pipeline Stage Tracking

For each triggered lead, track their journey. Add a `pipeline_stage` column to track:

```javascript
const PIPELINE_STAGES = [
  { id: 'triggered', label: 'Triggered', color: 'gray' },
  { id: 'contacted', label: 'Contacted', color: 'blue' },
  { id: 'replied', label: 'Replied', color: 'green' },
  { id: 'meeting', label: 'Meeting Booked', color: 'purple' },
  { id: 'opportunity', label: 'Opportunity', color: 'amber' },
  { id: 'closed', label: 'Closed Won', color: 'emerald' },
  { id: 'lost', label: 'Lost', color: 'red' }
];
```

**UI: Pipeline Stage Dropdown**
- Add a small dropdown in each trigger card to update the stage
- When user sends an email, auto-set to "Contacted"
- Visual indicator showing current stage (colored dot or pill)

### 2.2 ROI Dashboard Widget

Add a collapsible stats panel at the top of the Signals tab:

```
┌─────────────────────────────────────────────────────────────┐
│  📊 This Month's Pipeline                                    │
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │   12    │  │    8    │  │    3    │  │    1    │         │
│  │Triggers │  │Contacted│  │ Replied │  │Meetings │         │
│  │ Found   │  │         │  │  (38%)  │  │         │         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
│                                                              │
│  Conversion: Trigger → Reply: 25% | Reply → Meeting: 33%    │
└─────────────────────────────────────────────────────────────┘
```

Query from Supabase: `SELECT pipeline_stage, COUNT(*) FROM contacts GROUP BY pipeline_stage`

---

## Phase 3: AI Coach Insights (Medium Priority)

### 3.1 Smart Insights Banner

Below the ROI dashboard, show AI-generated insights when relevant:

```
┌─────────────────────────────────────────────────────────────┐
│ 💡 Insight: Your reply rate on "New CMO" triggers is 45%,   │
│    2x higher than "Award" triggers. Prioritize executive    │
│    changes for higher conversion.               [Dismiss]   │
└─────────────────────────────────────────────────────────────┘
```

Insights to generate (local logic, no AI call needed):
- "You have 3 hot triggers waiting for outreach"
- "Your fastest meeting came from a trigger contacted within 24 hours"
- "Industry X has 2x more triggers than industry Y this month"

### 3.2 Trigger Age Indicator

Show how fresh each trigger is:

```javascript
function getTriggerAge(detectedAt) {
  const hours = differenceInHours(new Date(), new Date(detectedAt));
  if (hours < 24) return { label: 'Today', color: 'green', urgent: true };
  if (hours < 72) return { label: `${Math.floor(hours/24)}d ago`, color: 'amber' };
  return { label: `${Math.floor(hours/24)}d ago`, color: 'gray' };
}
```

Display as a small badge: `🟢 Today` or `🟡 2d ago`

---

## Phase 4: Enhanced Outreach Experience (Medium Priority)

### 4.1 Quick Action Buttons

For each triggered lead, show inline action buttons:

```
[✉️ Draft Email] [📋 Copy Trigger] [📅 Schedule Follow-up] [⋮ More]
```

- **Draft Email**: Opens the email composer with trigger context pre-loaded
- **Copy Trigger**: Copies trigger summary to clipboard for use elsewhere
- **Schedule Follow-up**: Sets a reminder for 3/7 days later

### 4.2 Follow-Up Reminders

Track follow-up dates. Show visual indicator:

```
┌──────────────────────────────────────────────────────────────┐
│  Acme Corp - 🔥 Hot                           🟡 Follow-up  │
│  ⚡ New CMO Appointed                         due tomorrow  │
│  Jane Doe → CMO, Jan 28, 2026                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Phase 5: Reply Detection (Lower Priority - Future)

### 5.1 Reply Status Indicators

If email integration supports it, show reply status on contacted leads:

```
[✅ Replied] [⏳ No Reply (3d)] [📭 Bounced] [🏖️ OOO Detected]
```

### 5.2 Reply Categorization

When a reply comes in, categorize it:
- 🟢 Interested
- 🟡 Not Now
- 🔴 Not Interested
- ⚪ Auto-Reply / OOO

---

## Database Changes Required

Add these columns to `triggered_leads` (or equivalent contacts table):

```sql
ALTER TABLE triggered_leads ADD COLUMN IF NOT EXISTS pipeline_stage TEXT DEFAULT 'triggered';
ALTER TABLE triggered_leads ADD COLUMN IF NOT EXISTS contacted_at TIMESTAMPTZ;
ALTER TABLE triggered_leads ADD COLUMN IF NOT EXISTS follow_up_date DATE;
ALTER TABLE triggered_leads ADD COLUMN IF NOT EXISTS reply_status TEXT;
```

---

## UI Design Guidelines

1. **Don't Clutter**: Use collapsible panels, progressive disclosure
2. **Visual Hierarchy**: Hot triggers should visually pop; signals should be subtle
3. **Action-Oriented**: Every view should answer "what should I do next?"
4. **Mobile-Friendly**: These features should work on tablet/mobile too

---

## Implementation Order

1. ✅ **Phase 1.1**: Trigger quality badges (uses existing `confidence` field)
2. ✅ **Phase 1.2**: Tier filtering buttons
3. ✅ **Phase 2.1**: Pipeline stage dropdown
4. ✅ **Phase 2.2**: ROI stats widget (collapsible)
5. ✅ **Phase 3.1**: Smart insights banner
6. ✅ **Phase 3.2**: Trigger age indicator
7. ✅ **Phase 4.1**: Quick action buttons
8. ⏳ **Phase 4.2**: Follow-up reminders (if time permits)
9. ⏳ **Phase 5**: Reply detection (future phase)

---

## Questions for Clarification

1. Should the ROI dashboard be on the Signals tab or the main Dashboard page?
2. For pipeline stages, should moving to "Contacted" happen automatically when an email is sent, or require manual update?
3. Should insights be dismissible, or always visible?
