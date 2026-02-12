# Bolt Prompt: Passive Account Monitoring System

You are an expert Frontend AI. Your goal is to build the "Passive Account Monitoring" feature.

## 1. Database & Architecture (Context)
I (Backend) have already implemented the SQL schema and the Modal worker.
- **Table:** `triggered_companies` now has `monitoring_status` ('active','paused') and `monitoring_frequency` ('daily','weekly').
- **Table:** `pulsepoint_email_queue` now supports `status = 'draft'` and `source = 'monitor_auto'`.
- **Worker:** A Modal job runs daily to find triggers and insert drafts into the queue.

Your job is to build the **User Interface** to control this.

## 2. Requirements

### A. CSV Upload Component (New File)
Create `src/components/CsvUploadModal.tsx`.
- **Inputs:** Drag-and-drop CSV.
- **Expected Columns:** `Company`, `Website`, `Contact Name`, `Contact Email`, `Contact Title`, `Client Context` (Optional, defaults to 'pulsepoint_strategic').
- **Dropdown:** In the UI Import dialog, allow selecting a global "Client Context" for the batch (e.g. "Mike Ecker", "PulsePoint", "Sourcepass", "QuantiFire") which populates the `client_context` column.
- **Action:**
    1. Parse CSV.
    2. Insert unique companies into `triggered_companies` (`monitoring_status='paused'`).
    3. Insert contacts into `PULSEPOINT_STRATEGIC_TRIGGERED_LEADS` linked to the company.
- **Placement:** Add "Import CSV" button to `AccountsPage` header.

### B. Monitoring Controls (AccountsPage.tsx)
Update the Companies Table:
- **Toggle:** Add "Monitor" switch (updates `monitoring_status`).
- **Dropdown:** Add "Frequency" (updates `monitoring_frequency`).
- **Timestamp:** Show `last_monitored_at` relative time.
- **Note:** No manual "Scan Now" button is needed for this version. The system runs automatically in the cloud.

### C. Draft Review Page (New File)
Create `src/components/DraftReviewPage.tsx`.
- **Logic:** Query `pulsepoint_email_queue` where `status='draft'`.
- **UI:** Card layout. Show Context (Trigger Event) + Email Body.
- **Actions:**
    - "Approve" -> Updates status to 'pending'.
    - "Edit" -> Inline edit body.
    - "Discard" -> Deletes row.
- **Nav:** Add to Sidebar ("Draft Review"). Show Badge count.

### D. Dashboard Metrics
Update `DashboardPage.tsx` to include:
- "Monitored Accounts" (Count active).
- "Pending Drafts" (Count drafts).

## 3. Implementation Plan
Please implement the above features. Start with the CSV Upload Modal.
