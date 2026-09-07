-- Apply the two pending production migrations.
--
-- These do exactly what `python -m api.manage remove-placeholder-institutions`
-- and `python -m api.manage migrate-dates` do, written as SQL so they can be
-- run from any database console without a Python environment.
--
-- PostgreSQL. Run the whole file in one session, in this order.
--
-- BOTH STEPS DESTROY DATA AND NEITHER CAN BE UNDONE. Step 1 deletes rows.
-- Step 2 destroys the month and day of every stored clinical date, which is
-- the point of it — restoring them would need a backup taken beforehand, and
-- would reintroduce the Safe Harbor contradiction the migration removes.
--
-- Take a backup first if you want one. Then run the SELECTs, read what they
-- return, and only then run the statements that change anything.

BEGIN;

-- ===========================================================================
-- Step 1 — remove seeded rows naming real hospitals
--
-- These name real institutions that have no relationship to HealthDB, and
-- GET /api/institutions is public, so they are currently served as though
-- they were partner sites.
--
-- A row referenced by a user or a regulatory submission is KEPT: deleting it
-- would destroy a real association, which is worse than the name lingering.
-- ===========================================================================

-- 1a. Look first. This changes nothing.
SELECT i.name,
       (SELECT count(*) FROM users u
          WHERE u.institution_id = i.id) AS user_refs,
       (SELECT count(*) FROM regulatory_submissions r
          WHERE r.institution_id = i.id) AS submission_refs
FROM institutions i
WHERE i.name IN (
    'Stanford Cancer Center',
    'Mayo Clinic',
    'MD Anderson Cancer Center',
    'Memorial Sloan Kettering',
    'Dana-Farber Cancer Institute',
    'Fred Hutchinson Cancer Center',
    'Cleveland Clinic',
    'Johns Hopkins Hospital',
    'OHSU Knight Cancer Institute',
    'Emory Winship Cancer Institute',
    'UCSF Helen Diller Cancer Center'
)
ORDER BY i.name;

-- 1b. Delete only the unreferenced ones.
DELETE FROM institutions
WHERE name IN (
    'Stanford Cancer Center',
    'Mayo Clinic',
    'MD Anderson Cancer Center',
    'Memorial Sloan Kettering',
    'Dana-Farber Cancer Institute',
    'Fred Hutchinson Cancer Center',
    'Cleveland Clinic',
    'Johns Hopkins Hospital',
    'OHSU Knight Cancer Institute',
    'Emory Winship Cancer Institute',
    'UCSF Helen Diller Cancer Center'
)
AND NOT EXISTS (
    SELECT 1 FROM users u WHERE u.institution_id = institutions.id)
AND NOT EXISTS (
    SELECT 1 FROM regulatory_submissions r
     WHERE r.institution_id = institutions.id);


-- ===========================================================================
-- Step 2 — truncate stored clinical dates to the year
--
-- extracted_medical_data.original_date held a full date parsed from uploaded
-- FHIR resources, which contradicts the Safe Harbor language used elsewhere
-- in the product. Safe Harbor permits no date element more precise than a
-- year.
--
-- Skip this whole step if 2a reports the column does not exist: it has
-- already been applied.
-- ===========================================================================

-- 2a. Does the column still exist, and how many rows still carry a month
--     and a day? This changes nothing.
SELECT count(*) AS rows_with_month_and_day
FROM extracted_medical_data
WHERE original_date IS NOT NULL;

-- 2b. Preserve the year before destroying the rest.
UPDATE extracted_medical_data
SET original_year = EXTRACT(YEAR FROM original_date)::int
WHERE original_year IS NULL
  AND original_date IS NOT NULL;

-- 2c. Confirm nothing was left behind. This must return 0 before you go on;
--     if it does not, stop and ROLLBACK rather than dropping the column.
SELECT count(*) AS unbackfilled
FROM extracted_medical_data
WHERE original_year IS NULL
  AND original_date IS NOT NULL;

-- 2d. Destroy the month and day.
UPDATE extracted_medical_data
SET original_date = NULL
WHERE original_date IS NOT NULL;

-- 2e. Drop the column so nothing can write a full date again.
ALTER TABLE extracted_medical_data DROP COLUMN original_date;


COMMIT;

-- ===========================================================================
-- Afterwards
--
-- GET https://healthdb.ai/api/institutions should no longer return any of the
-- names listed above. The self-audit invariants `no_placeholder_institutions`
-- and `no_precise_clinical_dates` should both pass:
--
--     python -m api.manage self-audit
-- ===========================================================================
