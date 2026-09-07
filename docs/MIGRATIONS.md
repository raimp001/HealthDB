# Database migrations

Migrations run from `initialize_database()` at application start. They are
idempotent, so a restart, a redeploy, or a partially-completed run is safe to
repeat.

---

## 2026-09 — Truncate clinical dates to year (`original_date` → `original_year`)

### Why

`extracted_medical_data.original_date` stored a full `DATE` parsed from the
uploaded FHIR resource. `_parse_fhir_original_date()` padded partial dates
(`2021-08` became `2021-08-01`) and kept month and day for complete ones.

HIPAA Safe Harbor requires removing every date element more precise than the
year for dates tied to an individual. The product described its pipeline as
Safe Harbor de-identification while persisting month and day, so the storage
contradicted the claim. The research export already emitted year only, which
masked the problem — the precision was in the database, not the output.

### What changed

| Layer | Before | After |
|---|---|---|
| `fhir_ingest._record()` | Passed the raw date string through | `_year_only()` returns a 4-digit `int` |
| `main._parse_fhir_original_date()` | Padded to a full `date` | `_parse_fhir_year()` returns `int` |
| `models.ExtractedMedicalData` | `original_date = Column(Date)` | `original_year = Column(Integer)` |
| `ExtractedDataResponse` | `original_date: Optional[date]` | `original_year: Optional[int]` |

Month and day are dropped at the parse boundary, so no downstream caller can
persist or log them by accident. Both layers truncate independently.

### Migration

`migrate_truncate_original_dates(engine)` runs on boot:

1. Adds `original_year INTEGER` (via `SCHEMA_SYNC_STATEMENTS`).
2. Backfills it from `original_date` — SQLite `strftime`, PostgreSQL
   `EXTRACT` fallback.
3. **Sets `original_date` to NULL for every row.** This is the step that
   satisfies the privacy requirement.
4. Attempts `DROP COLUMN original_date`. Needs SQLite ≥ 3.35; PostgreSQL
   always supports it.

Ordering matters: the year is copied before anything is destroyed, and the
column is dropped only after its values are NULL. An interrupted run cannot
lose the year while leaving month/day behind. If step 4 fails the column
remains but is entirely NULL, so no month/day survives either way.

### Rollback

**The month and day are not recoverable.** Step 3 destroys them by design;
that is the point of the migration. Reverting the code restores the old
column shape but not the discarded precision.

To roll back the code:

1. Revert the commit.
2. `ALTER TABLE extracted_medical_data ADD COLUMN original_date DATE;` if it
   was dropped.
3. Optionally seed `original_date` from `original_year` as `YYYY-01-01`.
   These are synthetic January 1st values, **not** clinical dates, and must
   not be presented as such.

Restoring true dates requires a pre-migration backup, which reintroduces the
Safe Harbor contradiction — a privacy decision, not an engineering one.

### Verification

```
pytest tests/test_date_truncation.py -v
```

Covers the parser, the persisted row, the patient-facing API, the log stream,
and the migration including idempotency. The assertions were verified by
reintroducing the leak at both layers and confirming the matching tests fail.

### If day-level data is later required

Longitudinal analysis needing day-level resolution **cannot** use Safe Harbor.
It requires Expert Determination under 45 CFR 164.514(b)(1): a qualified
statistician documents that re-identification risk is very small, typically
using date-shifting with a consistent per-patient offset so intervals survive
while absolute dates do not.

That is a different standard with different evidence requirements. It must not
be described as Safe Harbor, and the expert's written determination must be on
file before any such data is collected.

---

## Checking whether a migration has actually been run

Nothing in the application enforces that these migrations happened. That is
deliberate — they take locks, and running them at import time caused an
outage — but it means "we ran it" is a claim rather than a fact until it is
re-derived from the database:

```
python -m api.manage self-audit          # exit 1 if any invariant is failing
python -m api.manage self-audit --json   # for a monitor
```

`no_precise_clinical_dates` fails until `migrate-dates` has been run and no
`original_date` value survives. `no_placeholder_institutions` fails until
`remove-placeholder-institutions` has been run. Both check live rows, not a
migration ledger, so a partially applied migration is reported as failing
rather than done.

The same checks are available at `GET /api/health/invariants` (admin only,
503 when a blocker is failing) and run in CI against a fresh database, which
catches the checker and the schema drifting apart.
