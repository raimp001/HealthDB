# HealthDB website review and improvement plan

This review covers the React application in `src`, the FastAPI service in `api`, and the Vercel configuration. The production domain could not be inspected from the review environment, so these are source findings, not claims about observed production behavior.

## Priority 1: reliable pilot access

Implemented in this change:

- Validate dashboard sessions against `/api/auth/me` before mounting the workspace, with role-appropriate routing, expired-session recovery, and retry on service outages. Backend authorization remains the security boundary.
- Return researchers to the cohort builder after sign-in rather than losing their destination.
- Distinguish invalid credentials, server outages, validation failures, malformed responses, and connection failures. Bound authentication requests with a timeout.
- Reject inactive accounts during login and session restoration.
- Share API-origin configuration across the frontend, honoring the configured backend in production as well as development.
- Report database failure as HTTP 503 without exposing connection details. Include the Vercel commit revision and prevent health-response caching.

## Priority 2: coherent onboarding and accessible navigation

Implemented in this change:

- Keep the pilot notice below the fixed navigation so it is visible.
- Shorten the full-screen homepage hero and clarify synthetic-data pilot access.
- Replace the homepage's direct-MyChart and guaranteed-dataset implications with current workflow descriptions.
- Add a skip link, visible keyboard focus, mobile-menu expanded state, hidden-menu keyboard exclusion, active-page semantics, and reduced CSS motion.
- Associate registration and login labels with inputs, support password managers, announce errors, and confirm successful registration.
- Reset scrolling between routes and contain authentication-page decorative overlays.

## Remaining product work

1. Verify production against the released commit: homepage, nested route refreshes, API health, synthetic account registration/sign-in, patient consent/import, researcher cohort/study creation, and institution access. A successful build alone does not verify these workflows.
2. Replace silent empty-state fallbacks throughout the dashboards with per-panel loading, error, and retry states. Several fetch sequences currently turn non-200 responses into empty arrays, which can look like missing data.
3. Provide secure account recovery and email verification with an agreed email provider. The existing recovery link only opens the contact form; no automated reset delivery is implemented.
4. Complete institutional onboarding and connect verified data sources. Existing source explicitly identifies direct EMR connectivity, institutional agreements, and substantial parts of the infrastructure roadmap as planned. Those capabilities cannot be completed by changing homepage copy.
5. Validate de-identification, consent withdrawal, study permissions, extraction/export, and operational controls before accepting real patient records. This release retains the synthetic-data pilot restriction.
6. Add browser-level workflow checks to CI and run desktop/mobile accessibility and layout checks against a deployment preview.

## Release validation

The change adds frontend regression tests for authentication responses and safe return destinations, plus backend tests for disabled accounts and health failures. GitHub CI runs these tests and the production frontend build. Production verification must inspect the deployed revision and exercise representative workflows after deployment.

## Rollback

Revert this change through GitHub and redeploy the prior production revision if regression checks fail. This change introduces no database migration or deletion.
