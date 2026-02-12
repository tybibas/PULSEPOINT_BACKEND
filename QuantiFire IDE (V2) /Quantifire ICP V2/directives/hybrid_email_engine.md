# Hybrid Email Engine (SOP)

**Goal**: Generate high-precision outreach emails by combining a dynamic AI-generated hook with a static value proposition body.

## Operational Rule

> [!IMPORTANT]
> Do NOT ask the LLM to write the full email. Generate ONLY the opening hook sentence.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Trigger        │────▶│  OpenAI         │────▶│  Static Body    │
│  Detection      │     │  (Hook Only)    │     │  Template       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  email_draft    │
                                                │  in queue.json  │
                                                └─────────────────┘
```

## Inputs
* Trigger data from `active_triggers.json`
* Contact name, company name from enrichment

## Tools
* `templates/prompts.py`: Contains static body, meta-prompts, and assembly logic
* `execution/enrich_lead.py`: Calls the hook engine during lead enrichment

## Workflow

### Step 1: Detect Trigger Type
Classify the event into one of three scenarios:

| Trigger Type | Event Keywords |
|-------------|----------------|
| **EVENT** | Capital Markets Day, CMD, Investor Day, Investor Conference |
| **LEADERSHIP** | CFO Appointment, New CFO, Head of IR, Appointed |
| **VOLATILITY** | Stock Drop, Underperform, negative % performance |

### Step 2: Generate Hook (OpenAI)
Use the appropriate meta-prompt:

**Scenario A: Event Trigger (CMD / Investor Day)**
```
Context: They just announced a Capital Markets Day on [Date].
Goal: Connect the high stakes of a CMD to the risk of being misunderstood.
Tone: Professional, direct, slightly provocative.
Output: Just the sentence. No quotes.
```

**Scenario B: Leadership Trigger (New CFO / Head of IR)**
```
Context: They were just appointed as the new [Role].
Goal: Frame their arrival as the perfect time to "audit" legacy perception.
Tone: Helpful, authoritative.
Output: Just the sentence. No quotes.
```

**Scenario C: Volatility Trigger (Stock Drop)**
```
Context: Their stock is down [X]% or underperforming the sector.
Goal: Frame the price drop as a 'Narrative Gap' (market missing the value).
Tone: Fiduciary, objective, not alarmist.
Output: Just the sentence. No quotes.
```

### Step 3: Assemble Final Email
Concatenate:
1. `Hi {{FirstName}},`
2. `[AI_Generated_Hook]`
3. Static Body Template (verbatim)

### Step 4: Save to Queue
Store in `dashboard_queue.json`:
* `email_draft`: The complete assembled email
* `draft_hook`: Same value (backwards compatibility)
* `status`: "needs_approval"

## Static Body Template

```
We specialize in "Fiduciary Risk Audits"—measuring exactly where your 
management narrative diverges from market reality (the "Narrative Gap").

Most Boards rely on feedback filtered through brokers, creating a blindspot 
on true investor sentiment. We fix that by analyzing the raw, unvarnished 
perception of your register.

I have a Strategic Diagnostic prepared for [Company_Name] that identifies 
specific friction points your current reporting may be missing.

Do you want to see the audit before your next Board pack goes out?

Best,
[Sender_Name]
QuantiFire
```

## Edge Cases

* **Unknown Trigger Type**: Default to EVENT trigger
* **Missing Contact Name**: Use "there" as fallback in greeting
* **OpenAI Error**: Return error message, do not save incomplete email
* **Negative Performance but EVENT type**: If performance is negative and event is CMD, still use EVENT (the event is the primary trigger)

## Example Output

**Input:**
- Company: Allianz SE
- Event Type: Capital Markets Day
- Contact: Claire-Marie Coste-Lepoutre
- Performance: +28.1%

**Generated Hook:**
"With your Capital Markets Day approaching, ensuring your new strategic pillars land correctly with skeptics on the register is likely top of mind."

**Final Email:**
```
Hi Claire-Marie,

With your Capital Markets Day approaching, ensuring your new strategic 
pillars land correctly with skeptics on the register is likely top of mind.

We specialize in "Fiduciary Risk Audits"—measuring exactly where your 
management narrative diverges from market reality (the "Narrative Gap").

Most Boards rely on feedback filtered through brokers, creating a blindspot 
on true investor sentiment. We fix that by analyzing the raw, unvarnished 
perception of your register.

I have a Strategic Diagnostic prepared for Allianz SE that identifies 
specific friction points your current reporting may be missing.

Do you want to see the audit before your next Board pack goes out?

Best,
Your Name
QuantiFire
```
