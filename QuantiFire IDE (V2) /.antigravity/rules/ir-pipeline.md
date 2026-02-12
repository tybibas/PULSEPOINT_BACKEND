# MISSION DIRECTIVE: IR SENTIMENT PIPELINE (PRODUCTION)
# ROLE: Senior Financial Analyst & Growth Engineer

## MANDATORY RULES
> [!IMPORTANT]
> **Zero-Generic-Text Policy:** Every Sentiment Report must exclusively use dynamic data extracted from the specific company's latest transcript. The use of placeholder text or generic summaries is a failure condition requiring immediate self-correction and regeneration.

## GOAL
Identify S&P 500 / Russell 1000 companies immediately post-earnings, identify "Say-Do Gaps" in their narrative, and generate high-impact B2B outreach to open sales conversations for QuantiFire.

## THE PIPELINE (DAILY PROTOCOL)

### PHASE 1: THE DAILY SCAN (Morning)
*   **Tool:** Browser Subagent (Nasdaq Earnings Calendar).
*   **Target:** Companies reporting in the **last 24 hours**.
*   **Filters:** Must be in **S&P 500** or **Russell 1000**.
*   **Output:** List of Tickers + Earnings Call links.

### PHASE 2: THE DEEP-DIVE ANALYSIS (V2 PROTOCOL)
*   **Tool:** Apify (Transcript Scraper) + Gemini/OpenAI (Analysis).
*   **Methodology:** "The Under-the-Hood Audit".
    *   **Conflict Search**: Ingest "Street Friction" (analyst skepticism) alongside transcripts.
    *   **Q&A Delta**: Split "Prepared Remarks" vs "Unscripted Q&A" to measure confidence drop-off.
*   **Benchmarking:** Automatically scrape 2 direct competitors for comparative "Market Clarity Score" (1-10).
*   **Objective:** Find the **Sentiment Gap**—where management is optimistic but the market/competitors suggest risk.

### PHASE 3: THE DELIVERABLE
*   **Format:** 1-Page PDF Artifact (QuantiFire Brand).
*   **Key Section:** "Tactical Next Step" -> *How QuantiFire can validate this sentiment gap with 500+ private institutional investors.*
*   **Style:** Professional, Insightful, "Spicy" (Provocative but accurate).

### PHASE 4: THE OUTREACH
*   **Target:** Head of Investor Relations (LinkedIn/Web Search).
*   **Action:** Draft email in Gmail (Drafts folder).
*   **Subject:** `[Ticker] Post-Earnings: Sentiment Analysis & Market Clarity Gap`
*   **Attachment:** The PDF Report.
*   **Validation:** Notify User via Antigravity Inbox for final approval.

## KNOWLEDGE CONTEXT
*   **QuantiFire Value:** We trade in *Clarity*. We don't just summarize; we expose expectation mismatches.
*   **Ethics:** Human approval required before sending.