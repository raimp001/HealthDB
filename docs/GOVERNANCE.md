# HealthDB Governance

Status: **closed pilot**. HealthDB holds no compliance certifications, has no
executed institutional agreements, and must not process real PHI until the
items in "Before real PHI" below are independently verified.

This document records the state machines the platform enforces in code and the
decisions that are deliberately left to people. Where a step is not implemented,
it says so rather than implying it exists.

---

## 1. Account roles

| Role | How it is obtained | What it can reach |
|---|---|---|
| `patient` | Self-service signup (when the pilot gate is open) | Own profile, consents, access log, rewards |
| `researcher` | Self-service signup (when the pilot gate is open) | Cohorts, studies, extractions they own or collaborate on |
| `institution` | `python -m api.manage grant-role <email> institution --institution-id <id>` | Their own institution's agreements, IRB protocols, EMR connections |
| `admin` | `python -m api.manage grant-role <email> admin` | Regulatory approval across institutions; audit records |

**Rules that are enforced in code**

- Registration accepts only `patient` and `researcher`. Anything else is
  rejected by schema validation. Privileged roles have no HTTP path at all.
- The authoritative role is the `users.user_type` column. It is resolved from
  the database on every privileged request; the JWT's `type` claim is never
  trusted. A token proves identity, never privilege.
- Self-service signup is refused unless `ALLOW_SELF_SERVICE_REGISTRATION=true`.

**Not implemented**

- Multi-factor authentication.
- Time-bounded or approval-gated role grants. A grant is immediate and
  permanent until revoked with `revoke-role`.

## 2. Researcher verification

`users.is_verified` is set only by the email-verification workflow, which
proves control of an address and nothing more.

**Not implemented.** Verification of institutional affiliation, credentials, or
standing. Do not treat `is_verified` as evidence that a researcher is who they
claim to be professionally. Any pilot participant must be vetted out of band.

## 3. Consent

States: `pending` → `signed`/`active` → `revoked` | `expired`.

- Consent is checked at query time, not only at collection time, so a
  revocation takes effect on the next query rather than on the next sync.
- A patient can revoke at any time through the portal or by requesting
  deletion, which revokes every active consent as a side effect.
- Revocation is not retroactive. Extracts already released to an approved
  study under a valid consent cannot be recalled from the researcher's copy.
  This limitation is stated to the patient in the deletion response.

**Not implemented.** Consent versioning — re-consent when terms change is a
manual process, and there is no machinery that invalidates a prior consent
when a new template version is published.

## 4. Study and regulatory approval

States: `draft` → `pending_approval` → `approved` → `active` → `completed` |
`archived`.

Regulatory submissions (`irb_protocol`, `dua`, `reliance_agreement`,
`amendment`) move `draft` → `submitted` → `under_review` → `approved` |
`revision_required` | `signed` | `expired`.

**Rules that are enforced in code**

- Approval requires the `institution` or `admin` role.
- An institution reviewer may only act on their own institution's submissions.
- Nobody may approve a submission for a study they own — separation of duties.
- Re-approving an already approved submission is refused.
- IRB approvals expire after 365 days, DUAs after 730.

**Not implemented**

- Dual review. A single qualifying reviewer can approve. Requiring two
  independent approvals before data release is an open item.
- Any check that a platform "approved" record corresponds to a legally
  executed document. These records track platform state only. **An approval
  in HealthDB is not evidence of an executed IRB approval, DUA, reliance
  agreement, or BAA.**

## 5. Data release

- Exports run against de-identified data only.
- Aggregate results apply small-cell suppression.
- Access is scoped to the requesting researcher's studies, checked per object
  rather than per role.

**Not implemented.** k-anonymity verification on export, re-identification
risk scoring, expiring signed download URLs, and dual sign-off before release.

## 6. Audit

Every data access is written to an append-only log that the patient can read.
Role grants, password resets, email verifications, and deletion requests are
written to the audit logger.

**Not implemented.** Tamper-evident storage (the log is an ordinary table),
real-time anomaly alerting, and log retention enforcement.

## 7. Incident response

**Not implemented.** There is no documented incident response procedure, no
breach notification workflow, and no on-call rotation. This must exist before
real PHI is processed.

Interim expectation: any suspected exposure is escalated to the project owner
immediately, the pilot gate is closed
(`ALLOW_SELF_SERVICE_REGISTRATION=false`), and `JWT_SECRET` is rotated, which
invalidates every outstanding session.

## 8. Rewards

`points_balance` and `total_points_earned` are internal counters with no
monetary value. They must not be described as cash, gift cards, medical
credits, or compensation anywhere in the product or in recruitment material
until a funded programme exists and has had legal review — patient inducement
in research is regulated.

---

## Before real PHI

Every item below is outstanding. None is satisfied by application code alone.

- [ ] Independent security assessment and penetration test
- [ ] SOC 2 Type II audit
- [ ] Executed BAAs with every party touching PHI, including hosting
- [ ] IRB approval, and reliance agreements for multi-site work
- [ ] Executed DUAs with each contributing institution
- [ ] Documented incident response and breach notification procedure
- [ ] Legal review of the consent model and the rewards programme
- [ ] Hosting review: data residency, backup encryption, key management
- [ ] Workforce security and privacy training
