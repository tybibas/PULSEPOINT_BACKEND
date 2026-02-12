# PulsePoint UI/UX Overhaul Prompt

## CRITICAL: Backend Preservation Rules

> [!CAUTION]
> **DO NOT modify any of the following:**
> - Supabase queries, table names, or column references
> - Modal webhook endpoints or API calls
> - Email sending logic in `deliveryService.ts` or edge functions
> - Authentication/OAuth flows
> - Any TypeScript interfaces/types related to database schema

This is a **frontend-only refactor**. All changes are to component structure, routing, and styling.

---

## NEW: Template + AI Hook System

The Modal backend now supports a **hybrid email generation system**. When users create an `initial_outreach` template with the `{{ai_hook}}` placeholder, the system will:

1. Generate ONLY a 1-2 sentence AI hook referencing the trigger event (using GPT-4o-mini for cost savings)
2. Insert the hook into the user's template
3. Apply other placeholders: `{{first_name}}`, `{{company_name}}`, `{{sender_name}}`

**If no template exists**, the backend falls back to generating a full AI email (legacy behavior).

### Template Placeholder Reference:
| Placeholder | Description |
|------------|-------------|
| `{{ai_hook}}` | AI-generated 1-2 sentence opener referencing the trigger event |
| `{{first_name}}` | Contact's first name |
| `{{company_name}}` | Company name |
| `{{sender_name}}` | Sender's name (defaults to "Ty") |

### Example Initial Outreach Template:
```
Hi {{first_name}},

{{ai_hook}}

We help companies like {{company_name}} [your value prop here].

Would you be open to a quick chat?

Best,
{{sender_name}}
```

**Action Items for Templates Page:**
1. Add `{{ai_hook}}` to the list of available placeholders in the template editor
2. Show a tooltip explaining: "AI-generated opener that references the trigger event (e.g., funding, new hire, rebrand)"
3. Ensure `initial_outreach` templates can be set as default

---

## Overview

Simplify the dashboard navigation from **11 sidebar items to 5** by merging overlapping features and removing underused ones. The goal is a cleaner information architecture that matches the user's mental model:

**Monitor → Detect → Draft → Review → Send**

---

## Part 1: Navigation Consolidation

### Current Sidebar (11 items)
```
Dashboard
Signals
Draft Review
Active Threads (badge)
Scheduled Queue
Sequences
Templates
Contacts
Accounts
Settings
Help
```

### Target Sidebar (5 items + footer)
```
Dashboard
Signals
Drafts
Accounts
Settings
───────────
Help (footer)
```

### Implementation Steps

#### 1.1 Update Sidebar Component

**File:** `src/components/Sidebar.tsx`

Remove these nav items entirely:
- Active Threads
- Scheduled Queue
- Sequences
- Contacts

Move "Help" from sidebar to footer position (below Settings, separated by divider).

Move "Templates" into Settings page as a subsection (don't remove the route yet, just remove from nav).

Rename "Draft Review" to "Drafts" in the sidebar.

#### 1.2 Update Routing

**File:** `src/App.tsx` (or routing file)

Keep all routes functional for now (don't break deep links), but the nav items should be hidden. Users who bookmarked `/contacts` should still be able to access it.

---

## Part 2: Merge Active Threads into Signals

### Current State
- `Signals` page shows triggered leads with status filters (All, Not Contacted, Scheduled, Sent, Opened, Replied, Bounced, Failed)
- `Active Threads` page shows emails with replies and has "Follow Up" buttons

### Target State
- `Signals` page absorbs Active Threads functionality
- Add a new filter tab: **"Needs Follow-Up"** between "Replied" and "Bounced"
- This tab shows leads where `status = 'replied'` AND no follow-up has been sent

### Implementation

**File:** `src/components/TriggeredCompanies.tsx` (or Signals page component)

1. Add new filter tab "Needs Follow-Up" to the existing filter tabs
2. When this tab is active, query leads where:
   - `status = 'replied'` OR
   - Last email was sent > 3 days ago AND no reply yet (stale threads)
3. Add "Follow Up" button to each row when in this view (same UI as Active Threads had)
4. Clicking "Follow Up" opens the same modal currently used in Active Threads

**File:** `src/components/ActiveThreads.tsx`

Keep the component file but it will no longer be in nav. Its functionality is now in Signals.

---

## Part 3: Merge Scheduled Queue into Drafts

### Current State
- `Draft Review` page shows drafts with status "draft" awaiting approval
- `Scheduled Queue` page shows drafts with status "scheduled" waiting to send

### Target State
- `Drafts` page has **tabs** at the top: "Pending Review" | "Scheduled" | "Sent Today"

### Implementation

**File:** `src/components/DraftReviewPage.tsx`

1. Rename component/page title from "Draft Review" to "Drafts"
2. Add a tab bar at the top with three tabs:
   - **Pending Review** (default): `status = 'draft'`
   - **Scheduled**: `status = 'scheduled'`
   - **Sent Today**: `status = 'sent'` AND `updated_at >= today`
3. Each tab uses the same table layout, just different query filters
4. Add badge counts to each tab header showing the number of items

**File:** `src/components/ScheduledQueue.tsx`

Keep the component but remove from nav. Its query logic should be moved into DraftReviewPage's "Scheduled" tab.

---

## Part 4: Move Templates into Settings

### Current State
- Templates has its own fullpage at `/templates`
- Settings page only shows Gmail integration

### Target State
- Settings page has sections: "Integrations" and "Email Templates"
- Templates content appears inline in Settings

### Implementation

**File:** `src/components/SettingsPage.tsx`

1. Add a new section below Gmail Integration:
   ```
   ## Email Templates
   [Embed the content from TemplatesPage here]
   ```
2. Keep the same template CRUD functionality (create, edit, delete, set default)
3. Use collapsible sections if the page gets too long

**File:** `src/components/TemplatesPage.tsx`

Convert this to an exportable component that can be embedded in SettingsPage.

---

## Part 5: Dashboard Redesign

### Current State
- 4 metric cards (Monitored Accounts, Pending Drafts, Active Signals, Total Contacts)
- Recent Activity list showing vague "Matched Ideal Customer Profile" items

### Target State
- Redesigned Dashboard with actionable sections

### New Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Dashboard                                                    │
│ Overview of your monitoring and outreach pipeline           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Accounts │ │  Drafts  │ │   Sent   │ │  Opened  │        │
│  │    77    │ │    3     │ │    35    │ │  12 (34%)│        │
│  │ monitored│ │ pending  │ │ this week│ │ open rate│        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────┐ ┌────────────────────────────┐ │
│  │ QUICK ACTIONS           │ │ SIGNALS THIS WEEK          │ │
│  │                         │ │                            │ │
│  │ [Review 3 Drafts →]     │ │ ⚡ Jenn David Design       │ │
│  │ [View 5 New Signals →]  │ │    New CMO Appointed       │ │
│  │ [Check 2 Follow-Ups →]  │ │                            │ │
│  │                         │ │ ⚡ Backbone Branding       │ │
│  └─────────────────────────┘ │    Rebranding Announced    │ │
│                              │                            │ │
│                              │ ⚡ DDNYC                   │ │
│                              │    Expansion to West Coast │ │
│                              │                            │ │
│                              │ [View All Signals →]       │ │
│                              └────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

**File:** `src/components/DashboardPage.tsx`

1. **Metric Cards**: Update the 4 cards:
   - Card 1: "Accounts Monitored" → count from `triggered_companies` where `monitoring_status = 'active'`
   - Card 2: "Drafts Pending" → count from `pulsepoint_email_queue` where `status = 'draft'`
   - Card 3: "Sent This Week" → count from `pulsepoint_email_queue` where `status = 'sent'` AND `updated_at >= 7 days ago`
   - Card 4: "Open Rate" → calculate from `open_count > 0` / total sent (use tracking columns)

2. **Quick Actions Section** (NEW):
   - Three action cards with counts and arrows
   - "Review X Drafts" → links to `/drafts`
   - "View X New Signals" → links to `/signals?filter=not_contacted`
   - "Check X Follow-Ups" → links to `/signals?filter=needs_followup`
   - Only show cards where count > 0

3. **Signals This Week** (replaces "Recent Activity"):
   - Query: `triggered_companies` where `event_type IS NOT NULL` AND `updated_at >= 7 days ago`
   - Show: Company name, event_title
   - Limit to 5 items
   - "View All Signals" link at bottom

---

## Part 6: Visual Polish

### 6.1 Metric Card Enhancements

Add subtle fade-in animation when numbers update:
```css
@keyframes countUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

Add comparison text below metrics where applicable:
```
35
Sent This Week
+12 from last week
```

### 6.2 Table Improvements

Add stronger row hover highlight:
```css
tr:hover {
  background: rgba(255, 193, 7, 0.08); /* subtle gold tint */
}
```

Add sticky header on scroll for all tables.

### 6.3 Status Pills

Keep current styling but ensure consistency:
- `Not Contacted` → gray
- `Scheduled` → blue
- `Sent` → amber/gold
- `Opened` → green
- `Replied` → bright green
- `Bounced` → red
- `Failed` → dark red

### 6.4 "Cool" Engagement Label

The "Cool" label in the Accounts table is unclear. Replace with one of:
- "No Recent Activity" (if no engagement)
- "Active" (if recently engaged)
- Or remove entirely and use last_monitored_at timestamp instead

---

## Part 7: Help in Footer

### Implementation

**File:** `src/components/Sidebar.tsx`

Move Help to a footer section at bottom of sidebar:

```tsx
{/* Footer Section */}
<div className="mt-auto border-t border-gray-700 pt-4">
  <NavItem icon={HelpCircle} href="/help">Help</NavItem>
</div>
```

---

## Part 8: Remove Contacts Page from Navigation

The Contacts page is redundant because:
- Contacts are visible in Signals (grouped under each company)
- Contacts are visible in Accounts (expanded row shows contacts)

### Implementation

**File:** `src/components/Sidebar.tsx`

Remove the Contacts nav item. Keep the route and component functional for users with direct links.

---

## Part 9: Remove Sequences Page from Navigation

The Sequences/Email Pipeline page is not actively used and creates confusion.

### Implementation

**File:** `src/components/Sidebar.tsx`

Remove the Sequences nav item. Keep the route functional.

---

## Summary Checklist

- [ ] Sidebar: Remove Active Threads, Scheduled Queue, Sequences, Contacts, Templates from nav
- [ ] Sidebar: Move Help to footer position
- [ ] Sidebar: Rename "Draft Review" to "Drafts"
- [ ] Signals: Add "Needs Follow-Up" filter tab with Follow Up button per row
- [ ] Drafts: Add tabs "Pending Review" | "Scheduled" | "Sent Today"
- [ ] Settings: Embed Templates section
- [ ] Dashboard: Redesign with actionable Quick Actions + Signals This Week
- [ ] Dashboard: Update metric cards (Monitored, Drafts, Sent This Week, Open Rate)
- [ ] Visual: Add row hover effects, sticky headers, countUp animation
- [ ] Visual: Replace "Cool" with clearer engagement labels

---

## Testing After Implementation

1. **Navigation Test**: Verify only 5 items + Help footer are visible
2. **Signals Test**: Verify "Needs Follow-Up" tab filters correctly
3. **Drafts Test**: Verify all 3 tabs show correct data
4. **Dashboard Test**: Verify metrics load correctly, Quick Actions link to correct pages
5. **Settings Test**: Verify Templates section works (create, edit, delete, set default)
6. **Deep Link Test**: Verify `/contacts`, `/sequences`, `/active-threads` still work if accessed directly
7. **Mobile Test**: Verify sidebar collapses properly on mobile

---

## Do NOT Change

- Any Supabase query logic (table names, column names, filters stay the same)
- Any API endpoints or webhook calls
- Email sending/receiving logic
- Authentication flows
- TypeScript interfaces/types for database entities
