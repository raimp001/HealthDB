# Closed-pilot configuration

HealthDB defaults to a read-only, synthetic-data pilot posture. A missing environment variable must never open sensitive functionality.

## Backend feature flags

All flags default to `false`.

| Variable | Effect when enabled | Pilot rule |
| --- | --- | --- |
| `ENABLE_SELF_SERVICE_REGISTRATION` | Allows patient and researcher account creation through `POST /api/auth/register` | Enable only for a supervised enrollment window, then turn it off again. |
| `ENABLE_SYNTHETIC_FHIR_UPLOADS` | Enables test acknowledgements and FHIR bundle import | Synthetic or generated bundles only. Never use this flag to accept PHI. |
| `ENABLE_DATA_MARKETPLACE` | Exposes data-product API responses and inquiries | Keep disabled until a governed, independently reviewed release workflow exists. |
| `ENABLE_PATIENT_STUDY_ENROLLMENT` | Opens the prototype study-discovery and join endpoints | Keep disabled while HealthDB is not enrolling real participants. |

The API is the source of truth. Frontend visibility is not an authorization control.

## Frontend build flag

`REACT_APP_ENABLE_SYNTHETIC_FHIR_UPLOADS=true` displays the synthetic FHIR import control. It must be set at frontend build time and should only be used when the matching backend flag is enabled.

`REACT_APP_ENABLE_PATIENT_STUDY_ENROLLMENT=true` displays the study-discovery simulation. Keep it unset while participant enrollment is unavailable, and only set it when the matching backend flag is enabled.

## Deployment checklist

1. Confirm all four backend flags are absent or `false` for the public deployment.
2. Confirm `REACT_APP_ENABLE_SYNTHETIC_FHIR_UPLOADS` is absent or `false`.
3. Call `/api/auth/register` with a valid test payload and confirm HTTP 403.
4. Call `/api/consent/templates` and confirm an empty array.
5. Call `/api/marketplace/products` and confirm an empty array.
6. Confirm `/patient`, `/research`, `/institution`, `/cohort-builder`, `/repo-analyzer`, and `/marketplace` redirect anonymous visitors to sign-in.
7. Confirm public pages state “synthetic data only” and do not claim compliance certification, partner data, or clinical use.

Any future real-data pilot needs a separate threat model, privacy and security review, data agreements, retention policy, incident plan, and explicit approval before these defaults change.
