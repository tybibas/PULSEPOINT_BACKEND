# Bolt Prompt: PulsePoint Growth Dashboard Redesign

> **Purpose:** Paste this prompt into Bolt to regenerate the PulsePoint Growth (Esker) frontend with the new enterprise-grade design system.

---

## Context

I have an existing triggered leads dashboard that needs a complete visual overhaul. The current design is functional but basic. I need it transformed into a premium, enterprise-grade interface that could compete with Salesforce, Outreach, or Apollo.io while maintaining a bespoke agency feel.

**Current Stack:**
- React/Vite frontend
- Supabase backend (PostgreSQL)
- Row-Level Security per client

**Brand:**
- Name: Esker (or PulsePoint Growth)
- Primary color: Gold/Amber (#d4a853)
- Theme: Dark mode primary

---

## Design System

Please implement the following design tokens throughout the application:

### Colors
```css
/* Background */
--color-bg-primary: #0a0a0a;      /* Main background */
--color-bg-secondary: #111111;     /* Card backgrounds */
--color-bg-tertiary: #1a1a1a;      /* Elevated surfaces */
--color-bg-elevated: #222222;      /* Hover states */

/* Accent (Gold) */
--color-accent-primary: #d4a853;
--color-accent-hover: #e6bc6a;
--color-accent-muted: rgba(212, 168, 83, 0.15);

/* Text */
--color-text-primary: #ffffff;
--color-text-secondary: #a8a8a8;
--color-text-muted: #666666;

/* Semantic */
--color-success: #22c55e;
--color-warning: #f59e0b;
--color-error: #ef4444;
--color-info: #3b82f6;

/* Intent Badges */
--color-intent-high: #ef4444;
--color-intent-medium: #f59e0b;
--color-intent-low: #22c55e;
```

### Typography
- **Display font:** Outfit (Google Fonts) - for headings and logo
- **Body font:** Inter (Google Fonts) - for all other text
- **Base size:** 16px
- **Line height:** 1.5

### Spacing
Use a 4px base scale: 4, 8, 12, 16, 20, 24, 32, 48px

### Border Radius
- Small: 4px
- Medium: 8px
- Large: 12px
- Full: 9999px (pills/badges)

### Shadows
- Use subtle shadows with rgba(0,0,0,0.4) for dark mode
- Add a gold glow effect on accent elements: `0 0 20px rgba(212, 168, 83, 0.3)`

---

## Page Structure

### Layout
Create a fixed sidebar navigation on the left (240px width) with the main content area to the right. The layout should be:

```
┌──────────┬─────────────────────────────────────────┐
│ SIDEBAR  │  HEADER                                 │
│          ├─────────────────────────────────────────┤
│ ⚡ Esker │  MAIN CONTENT AREA                      │
│          │                                         │
│ 📊 Dash  │  Lead cards, filters, etc.             │
│ ⚡ Sig.. │                                         │
│ 📧 Seq.. │                                         │
│ 👥 Cont. │                                         │
│ 🏢 Acct. │                                         │
│ 🎯 Tgt.  │                                         │
│          │                                         │
│ ⚙️ Set.  │                                         │
│ ❓ Help  │  FOOTER / BULK ACTIONS BAR              │
└──────────┴─────────────────────────────────────────┘
```

---

## Sidebar Component

Create a vertical navigation sidebar with:

1. **Logo section** at top
   - Lightning bolt icon (⚡) with gold glow effect
   - "ESKER" text in Outfit font, bold, white

2. **Primary navigation** (icons + text)
   - Dashboard (📊 grid icon)
   - Signals (⚡ lightning icon) - ACTIVE state uses gold accent background
   - Sequences (📧 envelope icon)
   - Contacts (👥 users icon)
   - Accounts (🏢 building icon)
   - Targets (🎯 target icon)

3. **Badge count** on Signals showing number of pending leads

4. **Secondary navigation** at bottom
   - Settings (⚙️ gear icon)
   - Help (❓ question icon)

5. **User profile** section at very bottom
   - Avatar with initials
   - User name
   - Role (e.g., "Admin")

**Active state:** Gold background tint with gold text
**Hover state:** Subtle dark background lift

---

## Signals Page (Main View)

### Page Header
- Title: "Triggered Leads"
- Subtitle: "X high-value prospects detected"
- Filter tabs: All (count) | Not Contacted | Sent | Opened | Replied | Bounced

### Lead Card Component

Each lead card should display:

#### Card Header (dark tertiary background)
- **Intent Badge** (pill shape, left side): 
  - "HIGH INTENT" = red background (#ef4444 at 15% opacity, red text)
  - "MEDIUM INTENT" = amber
  - "LOW INTENT" = green
- **Timestamp** (right side): "2 hours ago" in muted text
- **More options** button (three dots) - appears on hover

#### Company Section
- **Avatar** with company initials (gold/amber background tint, gold text)
- **Company name** in large semibold text
- **Trigger event** with ✨ sparkle icon in gold/amber color
  - Example: "✨ Centerpark Labs Named Life Science Campus of the Year"
- **Meta info** row: location, lead count, estimated value

#### Context Banner
- Left-bordered box with gold accent
- Gold muted background
- "CONTEXT" label
- Description of why this trigger matters

#### Contact Row(s)
- Checkbox for bulk selection
- Contact avatar (gray with person icon)
- Name + status badge (Not Contacted, Sent, Opened, etc.)
- Title and email
- AI-suggested best contact time

#### Email Preview Section
- "EMAIL DRAFT" label
- Subject line in bold
- Preview text (truncated to 3 lines)
- Edit button (gold text)

### Card Interactions
- Clicking "Edit" opens the email modal
- Hover lifts the card slightly (subtle shadow increase)
- Checkbox enables bulk selection mode

---

## Email Modal Component

When user clicks "Edit" on an email draft, show a centered modal:

### Modal Structure
1. **Header**
   - Title: "Edit Email for [Contact Name]"
   - Subtitle: "[Company Name]"
   - Close button (X)

2. **Recipient Info Bar** (tertiary background)
   - Contact avatar
   - Contact name, title, email
   - Edit button

3. **Split Panel Layout** (compose | preview)
   - **Left: Compose Panel**
     - "COMPOSE" label header
     - Subject input field
     - Body textarea (large, resizable)
   
   - **Right: Preview Panel**
     - "PREVIEW" label header
     - To: recipient display
     - Subject display
     - Formatted email body preview

4. **AI Suggestions Section** (below split panels)
   - 🤖 "AI SUGGESTIONS" header
   - List of 2-3 suggestions with icons:
     - "💡 Try a more casual opener..."
     - "🎯 Add specificity..."
     - "📊 Include a stat..."
   - Each has an "Apply" button in gold

5. **Footer** (tertiary background)
   - Cancel button (secondary style)
   - Save Draft button (secondary style)
   - Send Email button (primary gold with paper plane icon)

---

## Bulk Actions Bar

Fixed at bottom of screen when leads are selected:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ✓  10 Leads Selected                               [Clear] [Dispatch] │
│     Ready to dispatch personalized emails                              │
└─────────────────────────────────────────────────────────────────────────┘
```

- Shows count of selected leads
- Clear Selection button (secondary)
- Dispatch All button (primary gold)

---

## Micro-interactions & Polish

1. **Card animations:** Fade in with slight upward slide on load
2. **Hover effects:** Lift cards slightly, show hidden actions
3. **Button feedback:** Scale down slightly on click
4. **Loading states:** Skeleton loaders with shimmer animation
5. **Empty states:** Friendly illustration, helpful message
6. **Toast notifications:** For success/error messages (top-right)

---

## Supabase Data Binding

The data should come from Supabase tables:
- `${CLIENT}_TRIGGERED_LEADS` - main leads table
- Columns: id, company_name, trigger_headline, trigger_context, trigger_source_url, contact_name, contact_title, contact_email, email_subject, email_body, status, created_at

Status enum: 'not_contacted', 'sent', 'opened', 'replied', 'bounced'

Use Supabase Row-Level Security to ensure clients only see their own data.

---

## Mobile Responsive

- Sidebar collapses to hamburger menu below 768px
- Lead cards stack vertically
- Email modal goes full-screen on mobile
- Hide preview panel on mobile (compose only)

---

## Priority Order

Please implement in this order:
1. Design system (CSS variables, fonts)
2. Sidebar navigation
3. Lead card component
4. Signals page layout with filters
5. Email modal
6. Bulk actions bar
7. Animations and polish

Thank you! This should result in a premium, enterprise-grade dashboard that feels like Salesforce quality while maintaining a bespoke agency feel.
