# Still requires human review

Engineering cannot close any of these. Each needs a named person with the
relevant authority, and several are prerequisites for handling real PHI.

## Privacy

1. **De-identification has never been reviewed by a qualified statistician.**
   The pipeline removes direct identifiers, truncates dates to the year and
   caps ages over 89. That is Safe Harbor-*oriented*, and the product now says
   only that. Whether it actually meets Safe Harbor is a determination nobody
   has made, and the module performs no named-entity recognition, so a name
   written into free-text prose can survive. **Do not describe output as
   de-identified for a regulatory purpose until someone qualified says so.**

2. **Day-level longitudinal data would need a different standard.** If
   interval analysis at day resolution is ever required, that is Expert
   Determination under 45 CFR 164.514(b)(1), not Safe Harbor, and needs the
   expert's written determination on file *before* collection.

3. **Re-identification risk on exports is unquantified.** Small-cell
   suppression uses a threshold of 11 with no formal basis, and there is no
   k-anonymity check. A statistician should set the threshold.

## Legal

4. **No executed agreements.** No BAA with any party touching PHI, including
   the hosting provider; no DUA with any institution; no IRB reliance
   agreement. A record marked "approved" in HealthDB is platform state, not
   evidence of an executed document.

5. **The rewards programme needs legal and tax review before it exists.**
   Points are currently an inert counter and redemption is disabled. Turning
   it on needs an audited ledger, a redemption API, fraud controls, published
   terms, a tax position and a fulfilment provider. Compensating research
   participants is separately regulated as potential inducement and needs IRB
   input on the amount and structure.

6. **Consent language has not been reviewed.** The templates and the
   revocation model are engineering drafts.

## Security

7. **No independent assessment.** No penetration test, no security review, no
   SOC 2. The authorization model is covered by tests written by the same
   process that wrote the code, which is not a substitute.

8. **JWT secret rotation is an operational decision.** Roles now resolve from
   the database, so a stale token cannot escalate, but rotation still needs
   scheduling and an owner.

9. **The audit log is an ordinary table.** Not tamper-evident, no retention
   enforcement, no anomaly alerting.

10. **No incident response procedure.** No documented breach notification
    workflow and no on-call rotation.

## Institutional

11. **Researcher approval has no defined criteria.** `approve-researcher`
    records a decision but nothing states what should be checked first.
    Affiliation and standing are verified out of band, by nobody in
    particular at present.

12. **Dual review before data release is not implemented.** A single
    qualifying reviewer can approve a regulatory submission. Separation of
    duties prevents self-approval, which is not the same control.

13. **Pilot participants need an actual protocol.** Recruitment, eligibility,
    withdrawal handling and data retention are undocumented.

## Product

14. **Whether the architecture pages should exist at all.** They are labelled
    as target architecture and separate built from not-built, but they still
    describe a system that does not exist. That is a judgement call about how
    a reader is likely to use them.
