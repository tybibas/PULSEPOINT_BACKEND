# PulsePoint Monitor: 8-Phase Overhaul

## Phase 1: Structured Observability
- [x] Create `monitor_scan_log` migration SQL
- [x] Add scan logging to `run_monitoring_scan` (batch_id)
- [x] Add per-company logging to `process_company_scan`
- [x] Verify via webhook test

## Phase 2: Per-Company Isolation
- [x] Extract `scan_single_company` as Modal function
- [x] Refactor `run_monitoring_scan` to use `.spawn()`
- [x] Verify parallel execution + scan_log entries

## Phase 3: Scout Retries
- [x] Add retry + timeout to `portfolio_scout.py`
- [x] Add retry + timeout to `testimonial_scout.py`
- [x] Add retry + timeout to `social_scout.py`
- [x] Add retry + timeout to `blog_scout.py`

## Phase 4: Trigger Deduplication
- [x] Create `trigger_dedup` migration SQL
- [x] Add dedup check before trigger write (main loop)
- [x] Add dedup check before trigger write (context anchor)

## Phase 5: Extraction Fallback
- [x] Refactor `extract_article_content` with newspaper4k fallback
- [x] Verify paywall rejection still works

## Phase 6: Confidence Calibration Logging
- [x] Add `analysis_log` column to `monitor_scan_log`
- [x] Log each LLM analysis decision

## Phase 7: Async Scouts
- [x] Parallelize blog + social scouts with ThreadPoolExecutor
- [x] Parallelize portfolio + testimonial fallback scouts

## Phase 8: Cost Dashboard
- [x] Create `cost_dashboard.py`
- [x] Integrate summary into end of `run_monitoring_scan`

## Phase 9: State Persistence
- [x] Refactor `ClientStrategyContext` to include `companies` state
- [x] Update `AccountsPage` to use Context state
- [x] Implement persistence for background scans

## Phase 10: Backend Robustness
- [x] Fix worker crash on missing strategy context

## Phase 11: Verification
- [ ] Verify End-to-End Flow
  - [x] Identify test companies (Richter Studios: 11e3afbb-ee4f-406b-94cc-5199fc79cb74)
  - [x] Identify test companies (Lasso: bcccbee1-3858-4d37-9dbb-7be6ba1ef787)
  - [x] Trigger manual scan via Webhook (Simulate Frontend)
  - [ ] Verify Backend execution logs (Failed: No logs found)
  - [ ] Investigate Worker Failure
    - [ ] Check Webhook entry point
    - [ ] Verify Supabase connection in Worker
  - [ ] Confirm Database updates
