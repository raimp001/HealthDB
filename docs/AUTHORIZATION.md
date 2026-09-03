# Route / role authorization matrix

Generated from the live FastAPI app, not maintained by hand.
`tests/test_authorization_matrix.py` enumerates the same route table, so an
endpoint added without a gate fails CI rather than shipping.

**The JWT never decides what a request may do.** The `type` claim is written
when the token is minted and read nowhere else. Every dependency resolves the
user row and reads role, `is_active` and `researcher_approved_at` from the
database, so a deactivation, a role change or a revoked approval takes effect
on the next request rather than at token expiry.

## Roles

| Role | Obtained by | Notes |
|---|---|---|
| `patient` | Self-service signup | |
| `researcher` | Self-service signup, then `manage.py approve-researcher` | Needs **active + verified + approved**; all three are separate |
| `institution` | `manage.py grant-role <email> institution --institution-id <id>` | Must be scoped to an institution |
| `admin` | `manage.py grant-role <email> admin` | Not institution-scoped |

## Matrix

| Method | Route | Required |
|---|---|---|
| `POST` | `/api/auth/login` | anonymous |
| `GET` | `/api/auth/me` | any active user |
| `POST` | `/api/auth/register` | anonymous |
| `POST` | `/api/auth/request-password-reset` | anonymous |
| `POST` | `/api/auth/request-verification` | any active user |
| `POST` | `/api/auth/reset-password` | anonymous |
| `POST` | `/api/auth/verify-email` | anonymous |
| `POST` | `/api/cohort/build` | researcher (verified + approved) |
| `POST` | `/api/cohort/save` | researcher (verified + approved) |
| `GET` | `/api/cohort/saved` | researcher (verified + approved) |
| `GET` | `/api/cohort/variables` | researcher (verified + approved) |
| `GET` | `/api/cohort/{cohort_id}/summary` | researcher (verified + approved) |
| `POST` | `/api/consent/sign` | patient |
| `GET` | `/api/consent/templates` | anonymous |
| `POST` | `/api/consent/{consent_id}/revoke` | patient |
| `POST` | `/api/contact` | anonymous |
| `GET` | `/api/diseases/variable-sets` | anonymous |
| `GET` | `/api/diseases/{disease_name}/variables` | anonymous |
| `GET` | `/api/docs` | anonymous |
| `GET` | `/api/emr/connections` | institution (scoped) or admin |
| `POST` | `/api/extraction/create` | researcher (verified + approved) |
| `GET` | `/api/extraction/jobs` | researcher (verified + approved) |
| `GET` | `/api/extraction/jobs/{job_id}/download` | researcher (verified + approved) |
| `GET` | `/api/health` | anonymous |
| `GET` | `/api/institution/agreements` | institution (scoped) or admin |
| `POST` | `/api/institution/agreements` | institution (scoped) or admin |
| `GET` | `/api/institution/collaborations` | institution (scoped) or admin |
| `GET` | `/api/institution/emr-connections` | institution (scoped) or admin |
| `GET` | `/api/institution/irb-protocols` | institution (scoped) or admin |
| `POST` | `/api/institution/irb-protocols` | institution (scoped) or admin |
| `GET` | `/api/institution/profile` | institution (scoped) or admin |
| `GET` | `/api/institutions` | anonymous |
| `POST` | `/api/marketplace/inquiry` | anonymous |
| `GET` | `/api/marketplace/products` | anonymous |
| `GET` | `/api/marketplace/products/{product_id}` | anonymous |
| `GET` | `/api/patient/connections` | patient |
| `POST` | `/api/patient/connections/fhir` | patient |
| `DELETE` | `/api/patient/connections/{connection_id}` | patient |
| `GET` | `/api/patient/consents` | patient |
| `POST` | `/api/patient/consents` | patient |
| `GET` | `/api/patient/data-access-log` | patient |
| `GET` | `/api/patient/data-summary` | patient |
| `GET` | `/api/patient/extracted-data` | patient |
| `GET` | `/api/patient/profile` | patient |
| `POST` | `/api/patient/request-deletion` | patient |
| `GET` | `/api/patient/rewards` | patient |
| `GET` | `/api/patient/studies` | patient |
| `GET` | `/api/redoc` | anonymous |
| `POST` | `/api/regulatory/submit` | researcher (verified + approved) |
| `POST` | `/api/regulatory/{submission_id}/approve` | admin or institution |
| `POST` | `/api/regulatory/{submission_id}/submit` | researcher (verified + approved) |
| `GET` | `/api/researcher/analytics` | researcher (verified + approved) |
| `GET` | `/api/researcher/collaborations` | researcher (verified + approved) |
| `GET` | `/api/researcher/studies` | researcher (verified + approved) |
| `POST` | `/api/researcher/studies` | researcher (verified + approved) |
| `GET` | `/api/researcher/studies/{study_id}` | researcher (verified + approved) |
| `GET` | `/api/researcher/studies/{study_id}/analytics` | researcher (verified + approved) |
| `GET` | `/api/researcher/studies/{study_id}/participants` | researcher (verified + approved) |
| `PUT` | `/api/researcher/studies/{study_id}/recruiting` | researcher (verified + approved) |
| `GET` | `/api/researcher/studies/{study_id}/sites` | researcher (verified + approved) |
| `POST` | `/api/researcher/studies/{study_id}/sites` | researcher (verified + approved) |
| `GET` | `/api/stats/cancer-types` | anonymous |
| `GET` | `/api/stats/platform` | anonymous |
| `GET` | `/api/studies/available` | researcher (verified + approved) |
| `POST` | `/api/studies/{study_id}/join` | researcher (verified + approved) |
| `POST` | `/api/studies/{study_id}/leave` | researcher (verified + approved) |
| `GET` | `/api/study/{study_id}/comments` | researcher (verified + approved) |
| `POST` | `/api/study/{study_id}/comments` | researcher (verified + approved) |
| `POST` | `/api/study/{study_id}/invite` | researcher (verified + approved) |
| `GET` | `/api/study/{study_id}/team` | researcher (verified + approved) |

## Anonymous routes

Each was reviewed individually. They serve reference or catalogue data with
no subject, or are the unauthenticated entry points to authentication itself.
`/api/auth/register` additionally refuses unless the pilot gate is open.

