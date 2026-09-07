# What is still missing, end to end

A map of the research lifecycle from a patient consenting to a result being
published, marking what exists in code, what is missing, and — for each gap —
whether it is engineering work or something engineering cannot produce.

The distinction matters because the second kind does not get closer by
writing more code, and treating it as if it did is how a platform ends up
with a beautiful workflow around an empty centre.

| | Legend |
| --- | --- |
| **Built** | Implemented and covered by tests |
| **Partial** | Exists but incomplete in a way that matters |
| **Missing** | Not built |
| **Not ours** | Requires a determination, signature, or authority engineering does not have |

---

## Stage 1 — A patient decides

| Piece | State | Note |
| --- | --- | --- |
| Consent records, versions, options | Built | |
| Revocation | Built | Stops future extracts immediately |
| Revocation reaching already-released data | Built | Flags the release; a person must still act on it |
| Patient-visible access log | Built | |
| Patient-visible list of releases containing them | Built | `/api/patient/data-releases` |
| Consent covering **commercial** use | **Missing** | See §Money |
| Re-consent when study scope changes | **Missing** | A study can change purpose after enrolment; consent does not re-open |
| Proxy / paediatric / decisionally-impaired consent | **Missing** | Requires a legal model, not a checkbox |
| Returning results to the patient | **Missing** | Patients contribute and hear nothing back |

## Stage 2 — Data arrives

| Piece | State | Note |
| --- | --- | --- |
| Synthetic FHIR R4 bundle parsing | Built | Flag-gated |
| Year-only date truncation on ingest | Built | |
| Direct-identifier scrubbing | Partial | Regex only, no NER; unreliable on free text |
| Live EHR connection (SMART on FHIR, Bulk FHIR) | **Missing** | Blocked on de-identification review, not on code |
| HL7v2, claims, lab feeds | **Missing** | |
| Terminology normalization (ICD-10, SNOMED, LOINC, RxNorm) | **Missing** | Cohorts match on free-text strings today, which is why they cannot be compared across sites |
| Provenance: which system, which extraction, when | **Missing** | A record's origin is not stored |
| Ingest validation and rejection reporting | **Missing** | Bad data is stored, not quarantined |

## Stage 3 — A researcher asks a question

| Piece | State | Note |
| --- | --- | --- |
| Cohort criteria and feasibility counts | Built | |
| Small-cell suppression on aggregates | Built | |
| Saved cohorts | Built | |
| Variable inventory | Built | |
| **Query budget across repeated cohorts** | **Missing** | Differencing two overlapping cohorts defeats the suppression floor; nothing tracks it |
| Cohort versioning | Partial | The manifest snapshots criteria at release; editing a cohort still silently changes what "the cohort" means |

## Stage 4 — Governance

| Piece | State | Note |
| --- | --- | --- |
| IRB and DUA records, expiry checks | Built | Gate is enforced on export |
| Approvals recorded in the release manifest | Built | |
| Researcher approval as a human decision | Built | CLI only, deliberately |
| **Executed agreements as documents** | **Not ours** | The system stores a status string. A BAA or DUA is a negotiated instrument signed by two institutions |
| Institutional onboarding and verification | **Missing** | No audited path for a real institution to join |
| Site-level (multi-institution) approvals | Partial | Modelled, not enforced end to end |
| Data-use violation reporting | **Missing** | |

## Stage 5 — Release

| Piece | State | Note |
| --- | --- | --- |
| Consent-gated, variable-projected extract | Built | |
| Residual identifier check | Built | |
| k-anonymity / l-diversity measured per subject | Built | Blocks below threshold |
| Immutable, hashed release manifest | Built | Reproducibility, accountability and metering in one record |
| Download metered and logged | Built | |
| **Validated de-identification** | **Not ours** | Requires a named qualified statistician. See `DISCLOSURE_RISK_REVIEW.md` |
| Automatic generalization instead of blocking | **Missing** | An outlier record fails the export; nothing coarsens it |
| l-diversity / t-closeness enforced by threshold | **Missing** | Measured, not enforced |
| Signed manifests | **Missing** | Digests detect change; they do not prove authorship. Needs a key |
| Export formats beyond CSV (REDCap, FHIR, OMOP) | **Missing** | |

## Stage 6 — Analysis and publication

| Piece | State | Note |
| --- | --- | --- |
| Citable dataset identity | Partial | The content digest is citable; there is no DOI or persistent landing page |
| Analysis environment | **Missing** | Data leaves the platform entirely. A trusted research environment would mean it never has to |
| Results returned to the platform | **Missing** | Nothing links a publication back to the release it used |
| Reproducibility check against a manifest | Partial | Possible by hand; no route does it |

## Stage 7 — Keeping it working

| Piece | State | Note |
| --- | --- | --- |
| Health endpoint with a real database probe | Built | |
| Behavioural production probe | Built | `scripts/monitor.py` — catches the SPA swallowing `/api`, which a liveness check cannot |
| Scheduled monitoring | Built | Hourly, plus after every deploy |
| Self-audit invariants over live data | Built | 11 checks, `python -m api.manage self-audit`, exit code as the alarm |
| Invariants in CI on a fresh database | Built | Catches drift between checker and schema |
| Structured request logs | Partial | Audit lines exist; no request id, no aggregation |
| Alerting to a human | **Missing** | A failing GitHub Action is not a page |
| Backup and restore drill | **Missing** | Never tested |
| Incident procedure | **Missing** | |

---

## The self-audit, and why it is the load-bearing piece

Tests prove the code was right when it was written. They say nothing about
the database three months later, after a migration nobody ran, a seeder
someone re-ran, or an environment variable lowered to get an export through.

`api/self_audit.py` re-derives each safety property from live data:

```
python -m api.manage self-audit          # human readable, exit 1 on a blocker
python -m api.manage self-audit --json   # for a monitor
GET /api/health/invariants               # admin only, 503 when a blocker fails
```

Three rules make it trustworthy, and they matter more than the checks:

1. **No PHI leaves it.** Counts and labels only. A privacy checker that named
   affected patients would be a new disclosure.
2. **It is read-only.** Nothing repairs anything. A checker that silently
   fixes what it finds destroys the evidence it was ever broken.
3. **A check that cannot run is a failure.** Exceptions become blockers. The
   most dangerous bug this file could have is one that makes it always green,
   so there is a test that a raising check fails.

`no_placeholder_institutions` fails against production right now:
`GET /api/institutions` still returns eight real hospital names with no
relationship to HealthDB. `no_precise_clinical_dates` will fail too for any
row that predates the year-only schema. Neither migration has been run. That
is the point — they will keep failing, visibly, until someone runs them:

```
python -m api.manage remove-placeholder-institutions
python -m api.manage migrate-dates          # irreversible
```

## Money

Asked directly: this cannot charge for data today, and the blocker is not
billing.

- **What exists.** Every release is metered: subjects, records, variables,
  who received it, when it was downloaded, under which approvals, with a
  content digest. That is the defensible unit any future licensing would
  bill on, and it is recorded whether or not anyone ever charges.
- **`license_state` is `not_licensed` on every release** and stays that way.
  It is an accounting placeholder, not an authorization.
- **The blocker is consent.** Current consent records cover *research data
  sharing*. Commercial licensing of the same data needs consent that covers
  commercial use. Patients who consented to research have not agreed to that,
  and building a licensing flow on research consent would be the exact
  substitution this project has refused to make elsewhere.
- **What unblocks it:** a commercial-use consent type, a patient-facing
  explanation of what it means, an opt-in that is genuinely separable from
  research participation, and a decision about whether patients share in the
  proceeds. The rewards balance already says `has_monetary_value: false`;
  changing that is a promise, and it should be made deliberately or not at
  all.

Revenue that does **not** depend on that decision, and could be pursued now:
platform access for institutions running their own studies on their own data,
cohort feasibility as a service, and hosting multi-site coordination. None of
those involve selling patient data, which is why they are available.

## Order of work, if it were mine to sequence

1. **Statistician review.** Everything downstream waits on it. Live EHR
   connections cannot safely proceed without it.
2. **Terminology normalization.** Without codes, cross-site cohorts are
   string matching, and multi-institution research is the actual product.
3. **Query budgeting.** The current suppression floor is defeatable by anyone
   patient enough to run two cohorts.
4. **Institutional onboarding.** A real, audited path for one institution.
5. **Returning results to patients.** The one thing that makes contributing
   worth doing, and the cheapest of these to build.
