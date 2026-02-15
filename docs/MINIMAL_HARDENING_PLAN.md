# Signal Monitoring System — Minimal Hardening Plan

## Scope (Pragmatic, Not Hyperscale)

- **Target**: 5-15 enterprise clients, 1,000-3,000 monitored companies, moderate daily scanning
- **Out of scope**: Async migration, Kafka/Celery/queues, microservices, Kubernetes
- **Constraints**: Preserve `monitor_companies_job.py` as orchestrator, keep ThreadPoolExecutor, avoid new infra unless necessary

## Executive Summary

Five focused changes that prevent duplicate scans, data corruption, API overuse, and crashes — with minimal code and no new dependencies.

---

## 1. Scan Claim Locking — Prevent Duplicate Scans

**Why it matters at current scale**: Overlapping runs (cron + manual trigger) can assign the same company to multiple workers → 2x Apify/OpenAI cost, duplicate triggers.

**Approach**: One nullable column `scan_claimed_at` on `triggered_companies`. Orchestrator claims before spawn; worker clears on completion. Uses existing Supabase — no new infra.

**Migration** (Supabase SQL Editor):

```sql
ALTER TABLE triggered_companies ADD COLUMN IF NOT EXISTS scan_claimed_at TIMESTAMPTZ;
```

**Optional RPC** (cleaner than `.or_()`):

```sql
CREATE OR REPLACE FUNCTION claim_company_for_scan(p_company_id UUID, p_cutoff TIMESTAMPTZ)
RETURNS TABLE(claimed BOOLEAN) AS $$
BEGIN
  UPDATE triggered_companies SET scan_claimed_at = now()
  WHERE id = p_company_id AND (scan_claimed_at IS NULL OR scan_claimed_at < p_cutoff);
  RETURN QUERY SELECT FOUND;
END;
$$ LANGUAGE plpgsql;
```

**Orchestrator** (in `run_monitoring_scan`, before spawn): Call RPC; if `claimed=true`, spawn. Else skip.

**Worker** (in `process_company_scan`, always at exit — success/skip/crash):

```python
supabase.table("triggered_companies").update({"scan_claimed_at": None}).eq("id", comp["id"]).execute()
```

---

## 2. Atomic score_factors Updates — Prevent Race/Corruption

**Why it matters at current scale**: Blog, social, and LinkedIn scouts write `score_factors` from different threads. Full-object replace overwrites concurrent changes (e.g. blog_url clobbers last_social_scout_at), breaking throttles.

**Approach**: Postgres JSONB merge (`||`). One RPC, no new infra.

**Migration**:

```sql
CREATE OR REPLACE FUNCTION merge_score_factors(p_company_id UUID, p_delta JSONB)
RETURNS void AS $$
BEGIN
  UPDATE triggered_companies
  SET score_factors = COALESCE(score_factors, '{}'::jsonb) || p_delta
  WHERE id = p_company_id;
END;
$$ LANGUAGE plpgsql;
```

**Code change**: Replace every `supabase.table(...).update({"score_factors": ...})` with:

```python
def merge_score_factors(supabase, company_id: str, delta: dict):
    if not delta: return
    supabase.rpc("merge_score_factors", {"p_company_id": company_id, "p_delta": delta}).execute()
```

Example: `merge_score_factors(supabase, comp['id'], {"last_social_scout_at": ...})` — send only the delta, not the full object.

---

## 3. Apify Concurrency Cap — Stay Under Plan Limits

**Why it matters at current scale**: Apify Free ≈ 25, Scale ≈ 128 concurrent runs. BATCH_SIZE=10 × 6 threads/worker ≈ 60 peak. One burst can hit 429.

**Approach**: **Config-based** (no new infra). Reduce `BATCH_SIZE` and increase wave delay so concurrent Apify stays under your plan.

**Change** in `execution/monitor_companies_job.py`:

```python
APIFY_MAX_CONCURRENT = int(os.environ.get("APIFY_MAX_CONCURRENT", "20"))
BATCH_SIZE = max(1, min(10, APIFY_MAX_CONCURRENT // 6))
WAVE_DELAY_SECS = int(os.environ.get("SCAN_WAVE_DELAY_SECS", "60"))
# In loop: time.sleep(WAVE_DELAY_SECS)  # instead of 5
```

Default BATCH_SIZE=3, WAVE_DELAY=60 keeps ~18 concurrent. Adjust via env for your Apify plan.

---

## 4. 429-Aware Retry — Intelligent Backoff

**Why it matters at current scale**: 429 means "slow down." Short backoff causes retry storms; longer backoff (15-60s) lets the API recover.

**Approach**: Detect rate-limit errors in `resilience.py` and apply extended backoff.

**Change** in `execution/resilience.py`: Add `_is_rate_limit_error(exc)` checking for "429", "rate limit", "too many requests", or `exc.code == "rate_limit_exceeded"`. In `retry_with_backoff`, when the caught exception matches, use `rate_limit_initial=15` and `rate_limit_factor=3` instead of normal delay. Scouts already use the decorator and get 429-specific backoff automatically.

---

## 5. Fix score_factors Undefined Crash

**Why it matters at current scale**: If `comp.get('website')` is falsy, `score_factors` is never set. Line 1229 `score_factors.get('last_social_scout_at')` raises `NameError` and crashes the scan.

**Approach**: One-line change. Define `score_factors` before the scout block.

**Change** in `execution/monitor_companies_job.py` ~1208:

```python
# ==================== DEEP SCOUTS (Async Phase 7) ====================
score_factors = comp.get('score_factors', {}) or {}  # Always define (fixes crash when no website)

with ThreadPoolExecutor(max_workers=6) as executor:
```

---

## Summary: Files and Touches

| File | Changes |
|------|---------|
| `execution/monitor_companies_job.py` | score_factors init, merge_score_factors usage, claim-before-spawn, BATCH_SIZE/WAVE_DELAY config, clear claim on completion |
| `execution/resilience.py` | _is_rate_limit_error, extended backoff for 429 in retry_with_backoff |
| Supabase | scan_claimed_at column, claim_company_for_scan RPC (optional), merge_score_factors RPC |

**No new files. No Redis, Celery, or Kafka.** All changes are localized and additive.
