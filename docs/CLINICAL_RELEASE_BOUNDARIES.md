# Clinical and care-navigation release boundaries

Reviewed for implementation on 2026-09-06. This is an engineering scope record, not legal advice or a certification.

## Released public feature

`/care-guide` provides general US screening education for four topics, source dates, official external directories, clinician questions, a self-reported checklist, and a text download. It takes no medical history, makes no individual eligibility decision, orders no tests, books no appointment, and interprets no result. Checklist state is memory-only, with an explicit clear action; downloads remain under the visitor's control. Directory listings do not imply contracts, availability, insurance coverage, or endorsement. Clinical content lives in `src/data/careGuides.json`.

## Evidence and change control

- Breast screening: https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/breast-cancer-screening (2024-04-30)
- Colorectal screening: https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/colorectal-cancer-screening (2021-05-18)
- Hypertension: https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/hypertension-in-adults-screening (2021-04-27)
- Diabetes: https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/screening-for-prediabetes-and-type-2-diabetes (2021-08-24)

These sources were checked on the review date, not clinically validated by a physician. Assign a licensed clinical content owner before expanding into personalized guidance. Record guideline updates, applicability, exclusions, review dates, and clinical reviewer sign-off. Disclaimers alone do not determine regulatory classification.

## Required before personalized clinical services

1. Define intended use, patient population, jurisdictions, escalation protocols, and accountable licensed clinicians. Obtain an FDA device/CDS assessment for the actual function, especially patient-directed recommendations: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software .
2. Determine HIPAA covered-entity/business-associate roles, required BAAs, state privacy and consumer-health obligations, and FTC applicability. Validate infrastructure, access controls, retention, deletion, consent, incident response, and tracking: https://www.hhs.gov/hipaa/for-professionals/special-topics/health-apps/index.html . Do not claim HIPAA compliance from code review alone.
3. Contract with providers and laboratories, verify licensing and service capabilities, implement real order/referral and booking acknowledgments, and handle declined referrals, cancellations, and insurance barriers.
4. Assign result ownership. Radiology interprets mammograms; the patient's clinician reviews the report and arranges indicated follow-up. Provide confirmed delivery, overdue-result escalation, and closed-loop referral status before claiming care coordination.
5. Validate recommendations with clinician-reviewed cases, missing-data and high-risk cases, subgroup performance, guideline updates, and human overrides before release. Never treat a missing datum as a negative finding.
6. Review any financial incentives for inducement, anti-kickback, consent, and equity concerns before launch. Current guide only offers optional progress tracking, no monetary value or health score.

## Remaining audit scope

The existing automated suite covers specific authentication, consent, cohort, export and pilot boundaries, not all possible defects. Production authenticated workflows, penetration testing, accessibility across assistive technologies, disaster recovery, clinical validation, and contracted provider integrations require further verification. No claim of bug-free operation or regulatory approval is made.
