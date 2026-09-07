# Disclosure-risk review packet

This document exists so a qualified statistician can review HealthDB's export
pipeline without reading the whole codebase, and so nobody inside the project
can mistake a passing test for a de-identification determination.

**Current status: no qualified statistician has reviewed this pipeline.**
Until one has, HealthDB cannot describe any output as de-identified under
45 CFR 164.514(b)(1) (Expert Determination), and must not accept real patient
data.

---

## 1. What leaves the system

The only route that emits record-level data is the extraction job
(`process_extraction_job` in `api/main.py`). It writes a CSV with these
columns, one row per source record:

| Column | Contents |
| --- | --- |
| `patient_pseudonym` | `P-` + first 12 hex of `sha256("<study_id>:<patient_id>")` |
| `data_category` | Category label, e.g. `diagnosis` |
| `data_type` | Free-text type label, passed through the identifier scrubber |
| `year` | Year only. Month and day are never stored (see §4) |
| `quality_score` | Numeric completeness score |
| `data_json` | The selected variables, scrubbed |

Nothing else is released. Aggregate cohort counts follow a separate
small-cell floor (`MIN_AGGREGATE_CELL_SIZE`, default 11).

Known property of the pseudonym: it is a keyed-per-study but *unsalted* SHA-256
of an internal UUID. It is stable across exports of the same study, which makes
longitudinal linkage within a study possible by design. It is not reversible
without the internal UUID, but it is not a rotating token either. A reviewer
should decide whether that is acceptable for the intended release.

## 2. What is measured before release

`api/disclosure_risk.py` computes, per export:

- **k-anonymity** — the size of the smallest equivalence class over the
  quasi-identifier set.
- **l-diversity** — the number of distinct sensitive values in the least
  diverse class.
- Class-size histogram, count of unique classes, count of subjects below
  threshold.

The measurement unit is the **subject**, not the row. A subject contributing
several rows is collapsed into one signature carrying the set of values it
shows for each quasi-identifier, because a recipient reading the file sees
every row sharing a pseudonym. Measuring per row on such a file reports a
larger k than the release actually offers; there is a regression test for
exactly that mistake
(`test_per_row_measurement_overstates_k_when_subjects_repeat`).

An export whose smallest class falls below `MIN_EXPORT_K` (default: the same
value as `MIN_AGGREGATE_CELL_SIZE`, 11) is **failed, not warned**. No CSV is
produced. The measured report is stored on the job either way, so a reviewer
sees the numbers behind a pass as well as a block.

## 3. Quasi-identifier set

Defined as `DEFAULT_QUASI_IDENTIFIERS` in `api/disclosure_risk.py`:

`original_year`, `year`, `age`, `age_band`, `sex`, `gender`, `race`,
`ethnicity`, `zip`, `zip3`, `postal_code`, `state`, `cancer_type`,
`primary_site`, `stage`, `histology`, `vital_status`.

Matching is on the leaf field name, so a quasi-identifier nested inside
`data_json` is still counted.

**This set is the main judgement call in the whole module, and it is ours,
not a statistician's.** An attribute is a quasi-identifier if an adversary
could plausibly hold it from another source. We cannot know what external
data exists for a given release population. A reviewer should expect to
change this list.

## 4. Date handling

Clinical dates are stored as `original_year` (an integer). Month and day are
not stored. `api/fhir_ingest.py` truncates on ingest; `python -m api.manage
migrate-dates` destructively backfills existing rows.

Safe Harbor prohibits dates more precise than year and requires ages over 89
be aggregated into a single 90+ category. **That aggregation is not enforced.**
Records may carry an `age_band` / `age_range` value inside `deidentified_data`,
which can be selected as an export variable; nothing checks that the band does
not resolve an individual over 89. Age is treated as a quasi-identifier for
measurement, but banding is whatever the source produced.

## 5. Limits a reviewer should not have to discover

1. **k-anonymity does not prevent attribute disclosure.** A class of 30 that
   all share one diagnosis discloses that diagnosis. l-diversity is reported
   for this reason but is not currently enforced by a threshold.
2. **No cross-release tracking.** Repeated exports over overlapping cohorts
   can defeat a per-export threshold. Nothing here accumulates disclosure
   across releases, and nothing prevents a researcher from differencing two
   exports.
3. **t-closeness is not computed.**
4. **No date shifting or generalization is applied** beyond year truncation.
   There is no automatic suppression or coarsening of an outlier record — an
   export containing one is blocked, not repaired. A researcher's remedy is
   to broaden the cohort or drop a variable.
5. **The identifier scrubber is regex-based** (`api/deidentification.py`).
   It has no named-entity recognition. It will not reliably catch an
   identifier embedded in free text.
6. **The pseudonym is stable per study** (see §1).
7. **`MIN_EXPORT_K` is deployer-configurable via environment variable.** A
   deployment can lower it. There is a test asserting the code default is at
   least 11, but nothing prevents a production environment from overriding it,
   and nothing records that it was overridden.

## 6. What a review would need to produce

For an Expert Determination under 45 CFR 164.514(b)(1), a reviewer would need
to state, in writing and by name:

- the release population and the assumed adversary,
- the external datasets assumed available for linkage,
- the correct quasi-identifier set for that population,
- the threshold(s) and why they are appropriate,
- whether l-diversity or t-closeness must be enforced, and at what level,
- what must change before real data is accepted.

Items 1-7 in §5 are the open questions. None of them are blocked on
engineering; they are blocked on that determination.

## 7. Reproducing the measurement

```
python -m pytest tests/test_disclosure_risk.py tests/test_export_disclosure_gate.py -v
```

`tests/test_disclosure_risk.py` covers the metric itself. `tests/test_export_disclosure_gate.py`
drives the full HTTP path and asserts that a blocked export leaves no
downloadable file behind.
