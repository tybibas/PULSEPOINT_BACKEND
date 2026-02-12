
-- purge_misclassified_pulsepoint_leads.sql

BEGIN;

-- 1. Count before
SELECT COUNT(*) as "Count BEFORE Purge" FROM "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS";

-- 2. Delete ALL records (since we confirmed 100% contamination)
-- Safe because these were generated during testing and are mostly QuantiFire leads
DELETE FROM "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS";

-- 3. Verify empty
SELECT COUNT(*) as "Count AFTER Purge" FROM "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS";

COMMIT;
