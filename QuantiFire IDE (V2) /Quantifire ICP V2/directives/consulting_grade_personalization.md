# Analyst Grade Personalization Engine (SOP)

**Goal**: Generate hyper-personalized cold outreach opening lines using Ex-Buy Side analyst language and three strategic archetypes.

## Operational Rules

> [!IMPORTANT]
> - Maximum **25 words** per hook
> - Use **Ex-Buy Side Analyst persona**: cynical, observant, C-Suite language
> - **No salesperson language**

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Personalization │───▶│  Archetype      │───▶│  OpenAI         │
│  Research        │    │  Selection      │    │  (25-word hook) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐                             ┌─────────────────┐
│  Peer Gap Data  │                             │  Anti-Spam      │
│  Transcript Ctx │                             │  Filter         │
└─────────────────┘                             └─────────────────┘
```

## Archetype Selection Logic

| Archetype | Trigger Condition | Use When |
|-----------|-------------------|----------|
| **Peer Gap** | Gap > 20% vs peer | Company underperforming relative to sector peers |
| **Transcript** | Stock ±20% | Significant performance warrants Q&A friction reference |
| **Event** | Default | Strong or stable performance, use narrative urgency |

## Drafting Rules by Archetype

### A. Transcript Hook (Highest Trust)
- **Structure**: Reference specific Q&A theme
- **Prove you read it**: Mention analyst skepticism, buy-side focus
- **Example**: "Reading through your Q3 transcript, the analyst focus on your 'margin recovery timeline' seemed disconnected from the operational confidence you showed."

### B. Volatility / Peer Gap Hook (Highest Anxiety)
- **Structure**: Reference price action vs peer as "misunderstanding"
- **Terms**: narrative disconnect, sentiment drift, market mispricing
- **Example**: "I noticed your share price has drifted 15% below [Peer] this quarter, suggesting the market is pricing in a risk your guidance didn't justify."

### C. Event Hook (Highest Urgency)
- **Structure**: Frame catalyst as high-stakes test
- **Be helpful, not salesy**
- **Example**: "With your Capital Markets Day coming up, ensuring your new strategic pillars land with the skeptics on your register is likely the priority."

## Banned Phrases (Immediate Delete)

```
- "I hope you are well"
- "I'd love to learn more"
- "synergy" / "solution" / "unlock"
- "innovative" / "leverage" / "best-in-class"
- "value proposition" / "game-changing"
```

## Tools

| Script | Purpose |
|--------|---------|
| `execution/personalization_research.py` | Builds context: peer gaps, transcript friction, events |
| `templates/prompts.py` | Contains archetypes, anti-spam filter, prompt assembly |
| `execution/populate_master_universe.py` | Enriches contacts and generates hooks |

## Execution

```bash
# Test mode (3 companies)
python execution/populate_master_universe.py --test

# Full run (all 40 DAX companies)
python execution/populate_master_universe.py

# Sync to Google Sheet
python execution/sync_to_gsheet.py
```
