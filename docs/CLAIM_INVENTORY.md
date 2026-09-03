# Claim inventory

Every public claim reviewed in this pass, with what happened to it.

"Evidence" means a file, endpoint or test in this repository. Nothing here is
backed by an external document, because no external document exists: HealthDB
holds no certification, audit report, executed agreement or IRB approval.

Status keys refer to `src/data/featureStatus.js`, which the content check
(`scripts/check_content_claims.js`) and the unit tests enforce.

---

## Removed — unsupported and unfixable by rewording

| Claim | Appeared in | Why removed |
|---|---|---|
| "50+ institutions already signed" | Resources | No institutional agreement exists. |
| "Pre-negotiated reliance agreements" | Resources, Pricing, ForInstitutions | Nothing has been negotiated. |
| "Average 21 days to approval" | Resources | HealthDB runs no IRB; it cannot influence a timeline. |
| "3 weeks" / "2-3 weeks with central sIRB" | ForInstitutions, Pricing | Same. |
| "Add sites with reliance agreements in 24 hours" | Resources, ForInstitutions | No reliance agreement exists. |
| "Central sIRB" as an available service | ForInstitutions, Pricing, Resources | No sIRB arrangement. |
| "Epic, Cerner, Meditech, athenahealth" as integrations | ForInstitutions, Resources | No EHR connection of any kind. |
| "We're piloting federated approaches" | Resources | One database, no federation. |
| "HIPAA compliant" as a property of the software | index.html, DataMarketplace, ForInstitutions, Resources | Compliance is an organisational determination, not a software property. |
| "SOC 2 Type II" in the page footer | index.html | No audit has begun. |
| "100 pts = $1" and a live dollar figure | ForPatients, PatientPortal | Points have no monetary value. |
| Gift cards, direct payment, medical bill credits | ForPatients, Resources | No ledger, redemption API or fulfilment provider. |
| CAR-T case study: 547 patients, 8 sites, sIRB in 18 days | Resources | No study has run on the platform. Now marked hypothetical. |
| 12K+ patients / 8 sites / 50+ partners | Landing, About *(earlier pass)* | Live statistics report zero. |
| OHSU, Fred Hutch, Emory, ASH and eight more as partners | Landing, About, InstitutionDashboard *(earlier pass)* | Real organisations with no relationship to the project. |

## Rewritten — the underlying capability exists, the wording overstated it

| Was | Now | Evidence |
|---|---|---|
| "HIPAA Safe Harbor de-identification" | "Identifier removal, dates reduced to year, ages over 89 capped" | `api/deidentification.py`, `privacy.identifier-removal` |
| "Automated Safe Harbor compliance" | Named transformations, with Expert Determination listed as not performed | `privacy.expert-determination` (planned) |
| "HealthDB implements both [Safe Harbor and Expert Determination]" | "HealthDB has completed neither" | `privacy.expert-determination` (planned) |
| "All 18 HIPAA identifiers removed" | "Identifier fields removed... no named-entity recognition, so a name in prose can survive" | `api/deidentification.py` docstring |
| "We shift all dates by a random offset (±180 days)" | "Dates are truncated, not offset" — listed under what the pipeline does **not** do | `privacy.date-shifting` (planned) |
| "We maintain k≥5 across all datasets" | "No k is computed or enforced on any output" | `privacy.k-anonymity` (planned) |
| "For aggregate queries, we add calibrated noise" | "No noise is added to aggregate queries" | `privacy.differential-privacy` (planned) |
| "Patients get mathematical guarantees of privacy" | "No mathematical privacy guarantee is being claimed here" | — |
| "Connect your medical records (Epic, Cerner)" | "Upload a FHIR bundle exported from your patient portal" | `ingest.fhir-upload` (live) |
| "IRB Management — streamlined ethics approval" | "IRB protocol drafting and status tracking" | `governance.irb-tracking` (pilot) |
| "Earn rewards for contributions" | "Points record your participation and have no monetary value" | `patient.rewards` (planned) |
| "Pre-Negotiated DUAs" | "DUA Templates — not legally reviewed, none executed" | — |
| Throughput, latency and uptime figures on the roadmap | "Design targets (not measured)" | — |
| "Sign in as a researcher to load the variable inventory" (styled as an error) | "Sign in required" panel with sign-in and create-account actions | — |

## Kept — verified against the code

| Claim | Evidence |
|---|---|
| Manual FHIR R4 bundle upload | `api/fhir_ingest.py`, `POST /api/patient/connections/fhir` |
| Dates stored as year only | `_year_only`, `tests/test_date_truncation.py` |
| Direct identifier removal from structured fields and free text | `api/deidentification.py` |
| Ages over 89 capped | `_cap_age` |
| Residual identifier scan blocks a leaking export | `find_residual_identifiers` |
| Small-cell suppression on aggregates | `suppress_small_cell`, `tests/test_aggregate_suppression.py` |
| Roles resolved from the database, never the JWT | `current_user`, `tests/test_authorization_matrix.py` |
| Researchers require verification **and** explicit approval | `require_approved_researcher` |
| PBKDF2-SHA256, 600,000 iterations | `hash_password` |
| Consent checked at query time and revocable | `POST /api/consent/{id}/revoke` |
| Patient-visible access log | `GET /api/patient/data-access-log` |
| Data deletion request | `POST /api/patient/request-deletion` |

## Marked planned — described, but never in the present tense

Direct EHR connection · Epic · Cerner · Bulk FHIR · HL7v2 · Claims · OMOP CDM ·
NLP de-identification · k-anonymity · tokenized re-linkage · Expert
Determination · MFA · Postgres RLS · AWS KMS · WAF · API gateway · signed URLs ·
penetration test · SOC 2 · federated querying · trial matching · central sIRB ·
pre-negotiated DUAs · dual review · incident response · rewards programme

The four architecture pages carry a banner separating built from not-built,
each roadmap item is additionally labelled "Planned:" on its own line so a
reader scanning one entry does not have to rely on the page banner, and
`/status` renders the whole manifest.

## Enforcement

`scripts/check_content_claims.js` runs 15 rules over `src/` and `public/`.
`scripts/test_content_claims.js` injects 11 known-bad phrasings and asserts
each is caught, plus 4 correctly-qualified phrasings and asserts each passes.
Both run in CI. The self-test exists because a checker whose patterns quietly
stop matching reports success while claims regress — it caught exactly that:
a trailing word boundary meant "gift cards" was missed while "gift card"
was flagged.
