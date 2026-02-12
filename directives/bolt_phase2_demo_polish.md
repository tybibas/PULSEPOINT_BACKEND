# Bolt Prompt: Demo Polish (Pre-Close)

> **Goal:** Make the demo visually indistinguishable from Salesforce/Apollo without adding complex backend logic. Focus on visual polish and placeholder AI features.

---

## 1. Intent Badges on Contact Rows

Add intent scoring badges to make leads look prioritized. Use static/mock data for now.

**Current:**
```
☐ Brandon Maddox  ⊙ Not Contacted
```

**Target:**
```
☐ Brandon Maddox  🔥 HIGH  ⊙ Not Contacted
```

**Implementation:**
- Add a `intent_score` field display (use random assignment for demo: 40% HIGH, 40% MEDIUM, 20% LOW)
- Badge styles:
  - HIGH: red background (#ef4444 at 15% opacity), red text, 🔥 icon
  - MEDIUM: amber background (#f59e0b at 15% opacity), amber text, 🟡 icon  
  - LOW: green background (#22c55e at 15% opacity), green text, 🟢 icon

---

## 2. Company Grouping Headers

Group contacts by their company to show the signal → company → contacts relationship.

**Current:**
```
☐ Brandon Maddox   Not Contacted   Longfellow RE
☐ Eric Hotovy      Not Contacted   Longfellow RE
☐ Jackie Angel     Not Contacted   Carrier Johnson
```

**Target:**
```
▼ Longfellow Real Estate Partners (3)
  ⚡ Centerpark Labs Named Life Science Campus of the Year
  ├── ☐ Brandon Maddox    🔥 HIGH    Not Contacted
  ├── ☐ Eric Hotovy       🟡 MED     Not Contacted
  └── ☐ Daniel Mejia      🟡 MED     Not Contacted

▼ Carrier Johnson + Culture (3)
  ⚡ New Office Expansion in Del Mar
  ├── ☐ Jackie Angel      🔥 HIGH    Not Contacted
  ├── ☐ David Huchteman   🟢 LOW     Not Contacted
  └── ☐ Claudia Escala    🟡 MED     Not Contacted
```

**Implementation:**
- Group contacts by `triggered_company` or company name
- Show collapsible headers with company name, contact count, and trigger event
- Indent contact rows under each company
- Keep the right-panel email editor behavior the same

---

## 3. Dashboard KPI Sparklines

Add tiny trend charts inside each KPI card to make metrics feel dynamic.

**Current:**
```
┌─────────────────┐
│ 📊 Active Signals │
│ 47        +12% │
└─────────────────┘
```

**Target:**
```
┌─────────────────────────────────┐
│ 📊 Active Signals         +12% │
│                    ╱╲           │
│ 47            ╱╲╱╱  ╲╱         │
└─────────────────────────────────┘
```

**Implementation:**
- Add a small SVG sparkline (inline, ~60px wide, ~20px tall)
- Use hardcoded data points for demo: `[12, 18, 15, 25, 32, 28, 47]`
- Line color: gold accent (#d4a853)
- Make the KPI card clickable (cursor: pointer, hover effect) – no action needed yet

---

## 4. AI Suggestions Placeholder in Email Editor

Add an AI suggestions panel below the email body to show the "AI-powered" vision.

**Add this section below the Email Body textarea:**
```
┌─ AI SUGGESTIONS ─────────────────────────────────────────────┐
│ 🤖                                                           │
│                                                              │
│ 💡 Make opener more casual                           [Apply] │
│    "Congrats on the big Campus of the Year win!"            │
│                                                              │
│ 🎯 Add project specificity                           [Apply] │
│    Mention SOVA or Bioterra by name for personalization     │
│                                                              │
│ 📊 Include social proof stat                         [Apply] │
│    "Helped 12+ life science campuses boost tenant retention" │
└──────────────────────────────────────────────────────────────┘
```

**Implementation:**
- Add a collapsible section titled "AI SUGGESTIONS" with robot emoji
- Show 3 static placeholder suggestions with Apply buttons
- Apply button click: show toast "AI suggestion applied" (no actual edit needed for demo)
- Style: gold left border accent, dark tertiary background

---

## 5. Empty State Improvements

When Sequences page shows "No recent activity", make it feel productive instead of broken.

**Current:**
```
┌─ Recent Activity ─────────────┐
│                               │
│    ⏱ No recent activity       │
│                               │
└───────────────────────────────┘
```

**Target:**
```
┌─ Recent Activity ─────────────────────────────────────────────┐
│                                                               │
│    📬 Your outreach activity will appear here                │
│                                                               │
│    Once you start sending emails, you'll see opens,         │
│    replies, and engagement metrics in real-time.             │
│                                                               │
│              [→ Go to Signals to get started]                │
└───────────────────────────────────────────────────────────────┘
```

**Implementation:**
- Replace "No recent activity" with helpful onboarding message
- Add a CTA button linking to /signals
- Same treatment for "All caught up!" in Follow-Up Queue

---

## 6. Trigger Event Highlight in Contact Row

Make the trigger event more visible when a contact row is selected/hovered.

**Current:** Trigger only visible in right panel

**Target:** Show trigger preview inline on hover or in a subtle way

**Implementation:**
When hovering a contact row, show a tooltip or subtitle with the trigger:
```
☐ Brandon Maddox  🔥 HIGH  Not Contacted
   ⚡ Centerpark Labs Named Life Science Campus...
```

Or add as a second line in muted smaller text.

---

## Summary of Changes

| Feature | Effort | Impact |
|---------|--------|--------|
| Intent badges | Low | High – looks intelligent |
| Company grouping | Medium | High – shows differentiation |
| Dashboard sparklines | Low | Medium – feels dynamic |
| AI suggestions placeholder | Low | High – shows AI vision |
| Empty state copy | Low | Medium – feels polished |
| Trigger preview on hover | Low | Medium – context at a glance |

---

## What NOT to Build Yet

- Actual AI API integration (wait for close)
- Table view toggle (nice-to-have)
- Real-time signal detection (Phase 3)
- Chrome extension (Phase 3)
- Multi-touch sequence builder (Phase 3)

---

Please implement these demo polish features in priority order: Intent badges → Company grouping → AI suggestions → Dashboard sparklines → Empty states.
