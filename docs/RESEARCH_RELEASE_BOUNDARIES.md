# HealthDB AI research pilot

HealthDB AI supports research collaboration and synthetic cohort exploration, not clinical screening, treatment or referrals. OpenRx.health is a separate product.

This release supports explicit collaboration invitations and acceptance. Invitations are recorded in-app; email delivery is not enabled. Participation does not authorize data transfer. Real EHR connections, patient enrollment and commercial data releases remain gated.

Before production research data intake:

- Validate de-identification at the institution before transfer. Removing names alone is insufficient. Use HIPAA Safe Harbor or documented Expert Determination, including free-text and rare-event risk assessment.
- Do not treat limited datasets as de-identified: they remain PHI and require appropriate safeguards and agreements.
- Validate each EHR adapter and provenance mapping with synthetic fixtures, terminology checks and institution approval.
- Establish consent/legal authority, institutional agreements, applicable research review, retention, access controls and audit review.
- Require release review and licensing terms before any commercial transaction; neither pilot enrollment nor payment alone authorizes data access.

Every extract is now measured for residual re-identification risk (k-anonymity and l-diversity, per subject) and blocked below a configured threshold. That measurement is evidence for a review, not a substitute for one; see docs/DISCLOSURE_RISK_REVIEW.md for what it covers, what it does not, and what a qualified statistician would still need to determine.

The regex redaction utilities are not compliance certification. This release does not enable real data sales or promise clinical-trial operations.

Reference: https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html
