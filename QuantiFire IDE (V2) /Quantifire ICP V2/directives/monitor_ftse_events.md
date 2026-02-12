# Monitor FTSE 350 Events (SOP)

**Goal**: Identify "anxiety-inducing" events (CFO appointment, Capital Markets Day) in FTSE 350 companies and queue personalized emails.

## Inputs
*   `ftse_constituents.json`: List of companies to monitor (Ticker, Name).
*   `active_triggers.json`: Output from the event monitoring step.

## Tools
*   `execution/fetch_ftse_constituents.py`: Updates the `ftse_constituents.json` master list from LSE.
*   `execution/check_company_events.py`: Scans for news/events using Apify.
*   `execution/enrich_lead.py`: Finds contacts (Anymailfinder) and drafts emails (LLM).

## Workflow
1.  **Update Universe**: Run `fetch_ftse_constituents.py` to ensure the company list is current.
2.  **Scan for Events**: Run `check_company_events.py`.
    *   **Triggers**: "Capital Markets Day", "CFO Appointment", "New CFO".
    *   **Output**: `active_triggers.json` (Company, EventType, EventDetails, Date).
3.  **Enrich & Draft**: Run `enrich_lead.py` for each item in `active_triggers.json`.
    *   **Find Contact**: Head of IR or CFO.
    *   **Draft**: Create a hook based on the event.
    *   **Output**: Append to `dashboard_queue.json`.

## Edge Cases
*   **No Events Found**: Script should exit gracefully without writing to the queue.
*   **Contact Not Found**: Log the missing contact but do not fail the batch.
*   **API Errors**: Retry with exponential backoff for Apify/Anymailfinder/OpenAI.
