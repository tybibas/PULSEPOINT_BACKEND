# Bolt Prompt: PulsePoint Strategic - Phase 2 (Email Dispatch System)

We are upgrading the "Dispatch" functionality to be robust, scalable, and timeout-proof using a **Queue-based Architecture**.

Instead of the frontend trying to send 30 emails at once (which times out), it will now simply **queue** them in Supabase and then **trigger** a background worker to send them.

---

## 1. Database Schema (Already Created)
The backend table `pulsepoint_email_queue` is ready.

```sql
TABLE public.pulsepoint_email_queue (
    id UUID PRIMARY KEY,
    lead_id UUID, 
    email_to TEXT,
    email_subject TEXT,
    email_body TEXT,
    status TEXT DEFAULT 'pending', -- pending, processing, sent, failed
    attempts INT DEFAULT 0,
    last_error TEXT,
    user_id UUID, -- REQUIRED for authentication
    scheduled_for TIMESTAMPTZ DEFAULT NOW(), -- Used for scheduling
    created_at TIMESTAMPTZ
);
```

## 2. "Dispatch All" Button Logic
When the user clicks "Dispatch All" (or "Send" on a single lead), do not call the Gmail API directly.

**Step A: Queue the Emails**
*   Insert a row into `pulsepoint_email_queue` for each email.
*   Set `status` = `'pending'`.
*   Set `user_id` = `currentUser.id` (Critical for auth).
*   Set `email_to`, `email_subject`, `email_body` from the current draft.
*   **Scheduling:**
    *   If "Send Now": Set `scheduled_for` = `new Date().toISOString()`.
    *   If "Schedule": Set `scheduled_for` = `selectedDate.toISOString()`.

**Step B: Trigger the Worker**
*   After the insert is confirmed, make a single fire-and-forget `POST` request to the Modal Webhook:
*   **URL:** `https://ty-1239--pulsepoint-email-dispatcher-trigger-dispatch.modal.run`
*   **Method:** `POST`
*   **Body:** `{"limit": 30}` (or however many you queued)

## 3. UI Feedback (Real-time Progress)
*   **Initial State:** Change button to "Dispatching..."
*   **After Queueing:** Change to "Queued (0/30 Sent)".
*   **Polling:** Poll the `pulsepoint_email_queue` table every 5 seconds (or use Supabase Realtime) to check the `status` of the rows you just inserted.
*   **Progress Bar:** Update the "X/30 Sent" count as rows change from `pending` -> `sent`.
*   **Completion:** When all are `sent` (or `failed`), show a success message "All Emails Dispatched".

## 5. UI for "Schedule Send"
*   Add a "Calendar/Clock" icon next to the "Dispatch" button.
*   When clicked, show a date/time picker (e.g., `input type="datetime-local"`).
*   Button Text: If a date is selected, change "Dispatch All" to "Schedule All".
*   **Triggering:**
    *   You DO NOT need a separate webhook for scheduling.
    *   Simply insert with the future `scheduled_for` date.
    *   You MAY still call the `trigger_dispatch` webhook immediately after inserting. It will safely ignore them (because they are in the future), but it ensures the worker is awake to check one last time.
    *   **Reliability:** A background job runs every 15 minutes to pick up any scheduled emails automatically. Users can safely close the tab.

## 4. Key Constraints
*   **Do not** send emails from the frontend. Only insert to the queue.
*   **Do not** wait for the Modal Webhook to return "Success" before showing "Queued". The webhook creates a background job.
*   **Handle Errors:** If any emails end up as `failed` in the queue, show a "Retrying" or "Failed" indicator next to that lead.
