# Research planning workspace

The `/projects` workspace supports private project plans, a data dictionary,
milestones, team discussion, JSON specification download, and optional listings
visible to approved researchers. Administrators can create and manage their own
plans. Listings are not claims that datasets or validated results are available.

## Working flow

1. Create a project or open an existing study from the research dashboard.
2. Define the question, population, exposure/comparator, outcome, analysis, and
   intended use. Describe variables and expected sources; never enter patient values.
3. Assign milestone responsibility by role and track progress.
4. Optionally list the title, question, and collaborator needs. Full plans remain private.
5. Approved researchers request an invitation. The owner reviews the request;
   inviting creates a pending in-app invitation, not immediate membership.
6. The researcher accepts in `/collaborations`, then reads the plan and posts suggestions.
7. The owner incorporates edits. Revision checks reject stale saves rather than
   overwriting newer work. Downloads contain the saved plan and revision only.

## Boundaries and next priorities

- No email delivery, automatic institutional verification, EHR connection,
  patient-data intake, executed license, or clinical recommendation is added here.
- Free-text planning is not a validated de-identification system. Do not put
  patient information, secrets, or confidential source material in it.
- Plans and requests use the existing active-account and researcher approval gates.
- Listing does not waive institutional governance. Use the evidence/readiness workflow.
- Milestones are self-reported progress, not evidence of regulatory approval.
- Next priorities: verified institution profiles; site-level availability and
  terminology mapping; reproducible analysis runs tied to approved dataset versions;
  independent review of results; secure email invitations; full protocol version comparison.
- Project and applicant lists are bounded to 200 records, discussion to the newest
  100 messages. Expand pagination before larger institutional deployments.

## Verification

Automated coverage includes private-plan authorization, opt-in listing, duplicate
requests, invitation acceptance, collaborator read-only access and discussion,
schema validation, stale-save conflicts, and UI preservation of unsaved edits.
