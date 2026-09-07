# HealthDB pilot decision — 2026-09-07

This is a product proposal, not an approved protocol, privacy determination,
contract, regulatory opinion or promise of revenue. Obtain institutional, IRB,
privacy/legal and statistical review before using real patient records.

## Decision: start with a narrow, distributed study

Use the myeloma bispecific tumor-flare question to test the collaboration workflow
with two willing sites. Begin with synthetic cases and a common dictionary.
Institutions retain source records and linkage keys; HealthDB initially coordinates
plans, mappings, permissions, contributions and reviewed outputs. Patient-directed
record retrieval is a later, separate authorized pathway, not a workaround for a
site declining a research request.

This architecture is not new: PCORnet describes a distributed network with data
held by partners and limited query responses. Our hypothesis is that better
onboarding, shared definitions, patient participation and fair contribution terms
can make a narrow collaboration easier to start and repeat.
Source: https://pcornet.org/data/

## Challenge the assumptions

| Proposal | Devil's advocate | Practical response |
| --- | --- | --- |
| Patient consent unlocks any needed record | Participation consent and HIPAA authorization are distinct; transfer still needs a valid operational/legal pathway | Document purpose, source, recipient, permission and institutional requirements separately |
| Remove names and centralize everything | Rare clinical histories and timing can identify people; linkage supports follow-up but adds risk | Separate identity custody, minimize fields, and obtain a formal de-identification assessment |
| Collect interesting events first | A selected case series cannot estimate incidence; missing follow-up may bias classification | Define the exposed denominator and ascertainment strategy before making frequency claims |
| Pay for every record | Encourages quantity and duplicates rather than usable science | Pay for approved participation burden and independently accepted work |
| Pharma funds the loop | Funding may influence event selection or publication | Prespecify analysis, disclose conflicts and preserve independent review and publication rights |
| Build the whole data marketplace first | Infrastructure cost arrives before evidence of demand | Validate one study workflow and a funded use case before scaling |

HHS describes research authorization, limited-data-set agreements and permitted
waivers as different pathways. Our consent-led product preference is not a claim
that individual authorization is legally required for every research use.
Source: https://www.hhs.gov/hipaa/for-professionals/special-topics/research/index.html

HIPAA de-identification requires Safe Harbor or Expert Determination; merely
removing names is insufficient. A coded identifier is not automatically anonymous.
For rare events, exact timing and uncommon combinations need particular scrutiny.
Source: https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html

## Pilot deliverables and decision gates

1. **Planning:** agree on suspected-event definitions, adjudication, follow-up,
   denominator, missing data and output purpose. The in-app scaffold is a draft.
2. **Synthetic rehearsal:** two site representatives independently apply the same
   dictionary to synthetic scenarios. Record disagreements and abstraction effort.
3. **Go/no-go:** proceed only with named site leads, written governance pathway,
   reviewed privacy architecture, a funded budget and agreed contribution terms.
4. **Small real-data pilot:** only after approvals. Review source provenance,
   adjudication agreement, data completeness, duplicate risk and privacy controls.
5. **Publish and learn:** produce a limitations-aware output and a patient-facing
   summary. Expand only if sites and participants want to repeat the experience.

Proposed success measures: time to site onboarding, time per usable abstraction,
definition disagreements, completeness of required variables, withdrawal handling,
accepted contributions, payment timeliness when enabled, and repeat participation.
Set thresholds with the first sites; do not invent adoption or outcome numbers.

## Fair incentives without distorting the science

- **Patients:** compensate approved time/burden and reimburse expenses; offer
  accessible results and governance input. No extra reward for reporting an adverse
  event, no payment conditioned on perpetual consent, no forfeiture of earned pay
  solely for withdrawal. IRB reviews the schedule and participant information.
- **Researchers/coordinators:** pay contracted work such as abstraction and review
  after acceptance; transparently record contributions. Authorship follows scholarly
  criteria, not a purchased reward or automatic consequence of record volume.
- **Institutions:** contracted cost recovery for extraction, curation and oversight,
  approved through institutional channels; define permitted downstream uses.
- **Sponsor/platform:** fund a study budget covering approved work, review, operations
  and a disclosed platform fee. Retain a dispute process. No payouts beyond funded
  contractual obligations; payment execution needs its own controlled integration.

FDA guidance calls for fair payment and IRB consideration of undue influence;
payment should accrue during participation rather than depend on completing a study.
Source: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/payment-and-reimbursement-research-subjects

The first software step is a contribution ledger, not a token or speculative
royalty: task, role, approved terms, evidence reference, reviewer, accepted/disputed
state and payment reconciliation reference. Do not store banking details in study data.

## Safety outputs

Separate a research signal from a confirmed adverse reaction. A future reviewed
handoff can record provenance, seriousness, follow-up needs, duplicate checks and
recipient authority. Use established reporting channels and applicable sponsor
obligations; never silently send study data to a company. MedWatch is FDA's safety
information and adverse-event reporting program, not a substitute for study review.
Source: https://www.fda.gov/safety/medwatch-fda-safety-information-and-adverse-event-reporting-program

## More ambitious hypothesis — test later

A patient-governed research cooperative could let members help prioritize questions
and approve transparent funding rules, while sites run reviewed analyses locally.
Sponsors would fund approved questions and independently reviewed outputs rather
than buy unrestricted raw records. This is an experimental business/governance
proposal; no claim of novelty, legal feasibility, guaranteed privacy or profitability.

Before investing in it, test willingness to participate, site operating cost, sponsor
demand, representativeness, dispute handling and how minority patient preferences
are protected. Federated execution reduces transfers; it does not eliminate leakage,
site agreements, operational burden or biased data.

## Efficient implementation

Use docs/BUILD_BRIEF.md as the shared handoff for Claude and Codex. One owner per
branch, one acceptance-tested feature per PR, targeted reads and tests, brief outputs.
Keep legal/research decisions in this document rather than restating the entire
conversation. This should reduce avoidable context, but no fixed token saving is promised.
