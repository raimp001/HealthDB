# Institutional onboarding and evidence review

This release provides evidence tracking, not live EHR access, legal execution or compliance certification. It does not change intake or export gates.

## Workflow

1. An approved researcher opens a study's **Review launch readiness** link.
2. Keep evidence documents in an institution-approved repository. Enter its reference ID, SHA-256, exact scope and review expiration. Never paste credentials, patient information, document contents or signed download URLs.
3. A platform admin opens the same study ID, obtains the document through an approved external channel, compares its hash and verifies the scope and signatories. Verification records that administrative review; it does not supply legal authority.
4. Record each of the six requirement categories for the same scope. A newer version supersedes older references; rejected, revoked and expired evidence does not count. Revocation preserves the review history.
5. Even complete evidence does not turn on live data. An institution-specific implementation and release review is still required.

## Evidence to prepare with the first participating institution

| Category | Evidence owner and contents |
|---|---|
| EHR validation | Institution IT: registered FHIR client, approved scopes, endpoint, network/secrets handling, synthetic mapping tests, provenance and reconciliation results. Keep private keys outside this app. |
| De-identification | Qualified privacy reviewer: dataset/version, method, identifier and free-text handling, linkage/rare-event assessment, recipient context, limitations and re-review triggers. |
| Institution agreement | Authorized legal signatories: parties, permitted data, transfer authority, security responsibilities, retention, termination, incident response and applicable agreements. |
| Research authority | Research office: applicable IRB determination/approval or exemption, consent/waiver or other authority, institution participation and permitted purpose. |
| Data license | Legal/data steward: licensor rights, exact dataset and recipient, permitted research, term, fees, redistribution/AI-training restrictions, no re-identification, audit and deletion terms. |
| Security review | Security officer: deployment assessment, access provisioning/revocation, secrets, encryption, backups, logging, incident response and recovery test. |

These are preparation requirements, not a ready-to-sign contract. Institutional counsel and privacy/security reviewers must determine the applicable terms.

## API

GET/POST `/api/researcher/studies/{study_id}/readiness` requires an approved researcher or admin; only the study owner submits. POST `/api/research-evidence/{id}/review` requires an independent admin and JSON `{"decision":"verified"}` (or `rejected`, `revoked`). References are not automatically fetched. `evidence_complete` refers only to a shared scope of current reviewed references; `live_data_enabled` remains false.

## Standards references

- HHS de-identification: https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html
- SMART backend registration and authorization: https://hl7.org/fhir/smart-app-launch/backend-services.html

Actual production activation is blocked pending a named partner, approved access configuration, externally reviewed evidence and institution-specific integration testing.
