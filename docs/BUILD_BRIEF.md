# HealthDB: compact handoff for coding assistants

## Mission
Connect institutions, researchers and consenting patients to conduct useful,
governed multi-site real-world research. First pilot: myeloma bispecific-associated
suspected tumor flare/pseudoprogression. This is not OpenRx or a screening app.

## Product constraints
- Pilot uses synthetic data. No real records, production EHR or payments until
  validated, authorized infrastructure and institutional agreements exist.
- Consent is a product requirement; a prototype acknowledgement is not research
  consent or HIPAA authorization. Never convert it when enabling a feature.
- Keep source identifiers and linkage keys out of the research workspace.
- No fabricated partnerships, datasets, approvals, certifications, results or payouts.
- Research access requires active accounts plus operator confirmation/approval.
- Sponsors must not control conclusions. Reward completed work, not desired findings.
- User authorizes GitHub merges and Vercel deployment after checks; verify live revision.
- Multiple assistants work here. Fetch main first and preserve their changes.

## Current surfaces
- `/admin`: requests, identity/affiliation confirmation, approval and checks.
- `/projects`: private plans, dictionary, milestones, discussion, opt-in discovery;
  new empty plans can load a proposed myeloma scaffold. Site declarations map
  saved variables to expected sources and flag stale plans. Work ledger records
  submissions, owner review, disputes and resubmission without self-approval.
- `/collaborations`: explicit invitation acceptance.
- `/research-readiness`: references to externally reviewed governance evidence.
  Includes study-level consent/authorization process and withdrawal procedure;
  open evidence withdrawals block that scope even with replacement evidence.
  Independent admin disposition records external actions; no patient-level intake.
- Patient portal: consent simulation and contribution visibility; read current code.

## Minimal working loop
1. Read this brief, git status and recent main commits. Inspect the specific files
   needed for the requested acceptance criterion; avoid re-reading the repository.
2. Pick one deliverable. State acceptance checks before editing.
3. Implement it, including authorization, empty/error states and honest limitations.
4. Run targeted tests; run required CI gates once before merging. Repeat only failed
   checks or checks affected by later changes. Never weaken a safety test to get green.
5. Publish, verify Vercel production and live route/API revision. Report what was
   tested versus what still needs a real user, institution or credential.
6. Update this brief only when decisions change. Keep the final handoff under 200 words.

## Pasteable prompt
Read docs/BUILD_BRIEF.md and git status/recent main commits. Implement ONE scoped
deliverable: [task]. Acceptance criteria: [up to three observable checks]. Inspect
only relevant files; use existing modules; preserve other assistants' changes.
Use concise tool outputs and updates. No agents, broad refactors, repeated audits,
or dependency upgrades unless needed. Preserve access, consent and privacy gates.
Run targeted tests and required CI; fix failures. Merge to GitHub and verify the
Vercel production revision and affected routes. Report changes, evidence, and any
remaining blocker in under 200 words. Do not claim functionality you cannot verify.

## Next bounded tickets
1. Reproducible analysis manifests and independent result review, then a governed
   safety-report preparation workflow. No automatic sponsor/FDA submission.
2. Institutional validation of consent/authorization workflow and actual enforcement
   integration. Administrative evidence tracking is not patient e-consent.
