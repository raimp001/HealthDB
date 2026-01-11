# HealthDB.ai - Comprehensive Architecture Documentation

## Executive Summary

HealthDB.ai is a comprehensive longitudinal health data platform designed to:
1. **Enable voluntary patient data contribution** through secure, consented data sharing
2. **Facilitate researcher collaboration** with robust IRB compliance and data access controls
3. **Connect to EMR systems** for automated data extraction based on cohort criteria
4. **Manage multi-institutional coordination** including IRB approvals and data sharing agreements
5. **Provide ethical data monetization** with patient revenue sharing

## Core Value Propositions

### For Patients
- **Data Sovereignty**: Control over who accesses health data
- **Transparency**: See all data access events
- **Compensation**: Earn rewards for data sharing
- **Contribution to Science**: Enable medical breakthroughs
- **Privacy Protection**: Industry-leading de-identification

### For Researchers
- **Large-Scale Longitudinal Data**: Access to thousands of patients with years of follow-up
- **Rapid Cohort Building**: Query and identify eligible patients in minutes
- **IRB Compliance Built-In**: Streamlined multi-institutional IRB coordination
- **EMR Integration**: Direct connection to source EMR systems
- **Collaboration Tools**: Secure messaging and project management

### For Institutions
- **Revenue Sharing**: Earn income from contributed data
- **Research Facilitation**: Enable investigators to access multi-site data
- **Compliance Infrastructure**: Turnkey IRB and data governance
- **EMR Interoperability**: Standards-based FHIR integration

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                                  │
├─────────────┬──────────────┬──────────────┬──────────────┬──────────────┤
│  Patient    │  Researcher  │     IRB      │    Admin     │  Marketplace │
│   Portal    │  Dashboard   │    Portal    │   Console    │    Browse    │
└─────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
                                    │
┌───────────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                                 │
│  Authentication │ Rate Limiting │ Request Routing │ API Documentation      │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
┌────────────────────┬──────────────┬─────────────────┬─────────────────────┐
│   EMR CONNECTOR    │     IRB      │   CONSENT       │    DATA             │
│     LAYER          │   SERVICE    │   SERVICE       │  MARKETPLACE        │
├────────────────────┼──────────────┼─────────────────┼─────────────────────┤
│ • Epic FHIR API    │ • Protocol   │ • Consent       │ • Product           │
│ • Cerner API       │   Management │   Signing       │   Catalog           │
│ • AllScripts       │ • Multi-site │ • Version       │ • Licensing         │
│ • Direct DB        │   Tracking   │   Control       │ • Usage Tracking    │
│ • FHIR Mapper      │ • Reliance   │ • Blockchain    │ • Revenue Share     │
│ • MRN Validator    │   Agreements │   Anchoring     │ • DUA Management    │
└────────────────────┴──────────────┴─────────────────┴─────────────────────┘
                                    │
┌───────────────────────────────────────────────────────────────────────────┐
│                      CORE BUSINESS LOGIC                                   │
│  Cohort Builder │ De-identification │ Query Engine │ Access Control       │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
┌────────────────────────┬──────────────────────┬─────────────────────────┐
│   PRIMARY DATABASE     │   DATA WAREHOUSE     │   BLOCKCHAIN LEDGER     │
│   (PostgreSQL)         │   (Analytics)        │   (Immutable Audit)     │
├────────────────────────┼──────────────────────┼─────────────────────────┤
│ • Patient Records      │ • Aggregated Stats   │ • Consent Hashes        │
│ • Consents             │ • Cohort Analytics   │ • Access Logs           │
│ • IRB Protocols        │ • Usage Metrics      │ • Audit Trail           │
│ • Access Logs          │ • Revenue Reports    │ • Data Integrity        │
│ • User Accounts        │ • Quality Metrics    │                         │
└────────────────────────┴──────────────────────┴─────────────────────────┘
                                    │
┌───────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL INTEGRATIONS                                 │
│  EMR Systems │ Payment Gateways │ Email/SMS │ Biometric Auth │ Blockchain │
└───────────────────────────────────────────────────────────────────────────┘
```

## Critical Feature: EMR Data Extraction System

### Overview
The EMR Extraction System enables automated retrieval of patient data from Electronic Medical Record systems based on cohort criteria (e.g., "all patients with MRNs matching these criteria: diagnosis=breast cancer, age 40-65, stage II-III").

### Architecture Components

#### 1. EMR Connector Framework
**Base Connector Interface** (`/emr_connectors/base.py`):
```python
class EMRConnector:
    def connect(credentials) → Connection
    def validate_mrn(mrn_list) → ValidationResult
    def query_cohort(criteria) → List[MRN]
    def extract_data(mrn_list, variables, date_range) → DataFrame
    def get_available_variables() → List[Variable]
```

**Supported EMR Systems**:

##### Epic Systems
- **Connection Method**: FHIR R4 API (recommended) or Direct DB
- **Authentication**: OAuth2 with EHR Launch flow
- **FHIR Resources**: Patient, Condition, Observation, Procedure, MedicationRequest, DiagnosticReport
- **Custom Queries**: Epic-specific SQL for direct DB access
- **Rate Limits**: 600 requests/minute (API), no limit (DB)
- **MRN Format**: Alphanumeric, 6-10 digits

##### Cerner (Oracle Health)
- **Connection Method**: FHIR API or Proprietary API
- **Authentication**: OAuth2 Bearer Token
- **FHIR Resources**: DSTU2 and R4 support
- **Rate Limits**: 1000 requests/minute
- **MRN Format**: Numeric, 7-9 digits

##### AllScripts
- **Connection Method**: Direct DB (Unity) or API (TouchWorks)
- **Authentication**: Database credentials or API token
- **Data Model**: Proprietary (requires mapping)
- **Rate Limits**: No API limit (DB connection)
- **MRN Format**: Alphanumeric, variable length

##### MEDITECH
- **Connection Method**: Direct DB or File Export
- **Authentication**: Database credentials or FTP
- **Data Model**: Legacy system, limited standardization
- **Export Format**: CSV, HL7, custom
- **MRN Format**: Numeric or alphanumeric, institution-specific

#### 2. MRN-Based Extraction Workflow

**Step 1: MRN Input**
- **Manual Upload**: CSV file with MRN column
- **Cohort Query**: Define criteria to auto-generate MRN list
  - Diagnosis codes (ICD-10)
  - Procedure codes (CPT)
  - Medication names
  - Lab values (LOINC)
  - Age range
  - Date range (diagnosis date, encounter date)

**Example Cohort Query**:
```json
{
  "diagnosis": "C50.9",  // ICD-10 for breast cancer
  "age_at_diagnosis": {"min": 40, "max": 65},
  "disease_stage": ["II", "IIA", "IIB", "III", "IIIA", "IIIB"],
  "treatment_type": ["chemotherapy", "radiation"],
  "minimum_followup_months": 12,
  "exclude_metastatic": true,
  "date_range": {"start": "2018-01-01", "end": "2023-12-31"}
}
```

**Step 2: MRN Validation**
- Format validation (correct MRN format for EMR system)
- Existence check (MRN exists in EMR)
- De-duplication
- **Output**: Valid MRN list + invalid MRN report

**Step 3: Consent Verification**
- Cross-reference MRN list with HealthDB consent database
- Identify patients with active consent
- Exclude patients without consent or withdrawn consent
- **Output**: Consented MRN list + non-consented MRN list

**Step 4: Variable Selection**
- Researcher selects which data elements to extract
- **Categories**:
  - Demographics: Age, sex, race, ethnicity, zip code
  - Diagnoses: All diagnosis codes with dates
  - Procedures: All procedure codes with dates
  - Medications: All medications with start/stop dates, dosages
  - Lab Results: Specific labs (e.g., CBC, CMP, tumor markers)
  - Vital Signs: Blood pressure, heart rate, weight, BMI
  - Clinical Notes: Progress notes, discharge summaries
  - Imaging: Radiology reports, imaging dates

**Step 5: Date Range Specification**
- Relative to diagnosis: "All data from 6 months before diagnosis to 5 years after"
- Absolute: "January 1, 2018 to December 31, 2023"
- Encounter-based: "All data from encounters in 2020-2023"

**Step 6: Data Extraction**
- **Parallel Extraction**: Extract data for multiple MRNs concurrently
- **Batch Size**: 100 patients per batch (configurable)
- **Error Handling**: Retry failed MRNs with exponential backoff
- **Progress Tracking**: Real-time progress bar (% complete)

**Step 7: Data Transformation**
- **FHIR Mapping**: Map EMR-specific data to FHIR resources
- **Standardization**: Convert to common formats (dates to ISO-8601, units to UCUM)
- **Validation**: Check data quality (completeness, plausibility)

**Step 8: De-identification**
- **Direct Identifiers Removal**: Name, address, SSN, phone, email
- **MRN Tokenization**: Replace MRN with random token (consistent across queries)
- **Date Shifting**: Shift all dates by random offset (consistent per patient)
- **Quasi-identifier Generalization**: Age → age ranges, zip code → 3 digits
- **Free Text Scrubbing**: NER to detect and redact PHI in clinical notes
- **HIPAA Safe Harbor Compliance**: 18 identifier removal

**Step 9: Storage**
- **Encryption**: AES-256 encryption at rest
- **Access Control**: Row-level security based on IRB protocol
- **Audit Logging**: Log all data access events

### EMR Integration Use Cases

#### Use Case 1: Retrospective Cohort Study
**Scenario**: Researcher studying outcomes of CAR-T therapy in lymphoma patients

**Process**:
1. Researcher defines cohort:
   - Diagnosis: Diffuse Large B-Cell Lymphoma (C83.3)
   - Treatment: CAR-T therapy (CPT code or medication name)
   - Date range: 2016-2023
2. HealthDB queries EMR to identify MRNs meeting criteria
3. System finds 347 patients across 5 institutions
4. Consent verification: 289 patients have consented
5. Researcher selects variables: Demographics, diagnoses, treatments, lab results, outcomes
6. System extracts data from EMRs for 289 patients
7. De-identification applied
8. Researcher downloads de-identified dataset

**Timeline**: 2-3 hours for extraction and processing

#### Use Case 2: Prospective Study Enrollment
**Scenario**: Researcher recruiting patients for new clinical trial

**Process**:
1. Researcher uploads trial eligibility criteria
2. HealthDB queries EMR weekly for new patients meeting criteria
3. Newly eligible patients notified via patient portal
4. Patients review study information and consent
5. Upon consent, patient MRN shared with study coordinator
6. Coordinator contacts patient for enrollment
7. Ongoing: Study data flows back into HealthDB

**Timeline**: Continuous enrollment over trial duration

#### Use Case 3: Multi-Institutional Study
**Scenario**: Consortium studying rare disease across 10 academic medical centers

**Process**:
1. Lead institution submits IRB protocol to HealthDB
2. HealthDB coordinates IRB submissions to all 10 sites
3. Data sharing agreements executed
4. Each institution connects EMR to HealthDB
5. Cohort query run across all 10 EMRs simultaneously
6. 127 patients identified across institutions
7. Data aggregated and de-identified
8. Single dataset provided to researchers with institutional variables for adjustment

**Timeline**: 3-6 months for IRB/DSA, 1 week for data extraction

## Critical Feature: IRB Management System

### Multi-Institutional IRB Coordination

#### Single IRB (sIRB) Model
**Regulatory Requirement**: NIH-funded multi-site trials must use single IRB as of 2018

**HealthDB Implementation**:
1. **Lead IRB Selection**: PI selects institution to serve as IRB of record
2. **IRB Reliance Agreement Template**: HealthDB provides standardized template
3. **Reliance Agreement Workflow**:
   - Lead IRB reviews and approves protocol
   - HealthDB routes reliance agreement to participating sites
   - Sites sign electronically via DocuSign integration
   - Track signatures and completion
4. **Local Context Review**: Sites retain ability to review recruitment materials, local resources
5. **Centralized Amendments**: Protocol changes reviewed only by lead IRB
6. **Continuing Review**: Annual reviews coordinated by HealthDB

**Benefits**:
- **90% faster approval**: 30 days vs 6-12 months for independent IRBs
- **Harmonized consent forms**: One consent form, no conflicting revisions
- **Streamlined reporting**: Adverse events reported to single IRB

#### Independent IRB Model
**When Used**:
- State law requires local IRB review
- Institution policy prohibits reliance
- Community-engaged research requiring local input

**HealthDB Implementation**:
1. **Protocol Distribution**: HealthDB submits to all institutional IRBs simultaneously
2. **Harmonization Support**:
   - Pre-submission call with all IRBs to discuss protocol
   - Shared response document for common revisions
   - Liaison to communicate between IRBs
3. **Revision Tracking**: Dashboard shows status at each site
4. **Approval Milestones**: Celebrate each site approval
5. **Partial Activation**: Allow study start at approved sites while awaiting others

**Challenges Addressed**:
- **Conflicting revisions**: Mediate between IRBs to find acceptable compromise
- **Slow sites**: Escalate delays, offer support
- **Inconsistent timelines**: Set expectations for 3-6 month approval process

### IRB Portal Features

#### Protocol Submission Wizard
**Step-by-Step Guidance**:
1. Study Information (title, PI, funding source)
2. Study Design (methodology, randomization, blinding)
3. Participant Population (inclusion/exclusion criteria, vulnerable populations)
4. Procedures (study visits, data collection, interventions)
5. Risks and Benefits (foreseeable risks, potential benefits, risk mitigation)
6. Informed Consent (consent process, capacity assessment, surrogate consent)
7. Privacy Protection (data security, de-identification, access controls)
8. Data Safety Monitoring (monitoring plan, DSMB if required)
9. Document Upload (consent forms, recruitment materials, grants, CVs)
10. Submission Review (review all sections before submitting)

**Submission Checklist**:
- [ ] Protocol document uploaded
- [ ] Informed consent form(s) uploaded
- [ ] Recruitment materials uploaded
- [ ] PI CITI training certificate uploaded
- [ ] All personnel CITI certificates uploaded
- [ ] Funding documentation uploaded (if funded)
- [ ] Investigator brochure uploaded (if drug/device study)
- [ ] Data safety monitoring plan included
- [ ] Conflict of interest disclosures complete
- [ ] All fields completed
- [ ] Signatures obtained

#### Review Status Dashboard
**Real-Time Tracking**:
- **Timeline View**: Visual timeline showing submission date, review date, approval date
- **Status by Site**: Table showing status at each participating institution
  - Not yet submitted
  - Submitted, awaiting triage
  - Under expedited review
  - Scheduled for full board review (date)
  - Revisions requested
  - Approved
  - Disapproved
- **Reviewer Comments**: View IRB comments and revision requests
- **Action Items**: What PI needs to do next
- **Email Notifications**: Alerts for status changes

#### Reliance Agreement Management
**Features**:
- Template library (NIH, NCI, institution-specific)
- Electronic signature collection
- Version control
- Expiration tracking
- Renewal reminders

### IRB Compliance Features

#### Continuing Review
- **Automated Reminders**: 90 days, 60 days, 30 days before annual renewal
- **Report Template**: Pre-populated with enrollment data, adverse events, deviations
- **Supporting Documents**: Upload updated consent forms, amendments
- **Renewal Tracking**: Dashboard shows renewal status

#### Adverse Event Reporting
- **Event Classification**: SAE, AE, UPIRTSO (Unanticipated Problem)
- **Severity Grading**: Common Terminology Criteria for Adverse Events (CTCAE)
- **Relatedness Assessment**: Related, possibly related, unrelated
- **Expectedness**: Expected (in consent form) or unexpected
- **Automatic Routing**: Serious unexpected events → 24 hour report to IRB + sponsor
- **Aggregate Reporting**: Annual summary of all events

#### Protocol Deviations
- **Deviation Types**: Major (affects subject safety/rights) or minor (administrative)
- **Reporting**: Major deviations reported within 5 days, minor in annual report
- **Root Cause Analysis**: For major deviations, require corrective action plan
- **Trend Analysis**: Identify patterns (e.g., repeated consent errors at one site)

## Critical Feature: Data Sharing Agreements

### Data Use Agreement (DUA) Management

#### DUA Generation
**Automated Template**:
```
DATA USE AGREEMENT

This Data Use Agreement ("DUA") is entered into as of [DATE] by and between:

HealthDB, Inc. ("Data Provider")
[Institution Name] ("Data Recipient")

1. PURPOSE
Data Recipient requests access to de-identified health data for the following research purpose:
[AUTO-POPULATED FROM IRB PROTOCOL]

2. DATA DESCRIPTION
Data Provider will provide the following data:
- Dataset: [PRODUCT NAME]
- Patients: [N PATIENTS]
- Variables: [VARIABLE LIST]
- Date Range: [DATE RANGE]
- Data Product ID: [UNIQUE ID]

3. PERMITTED USES
Data Recipient may use the data solely for the research purpose described above.
Data Recipient may not attempt to re-identify individuals.
Data Recipient may not share data with third parties without written permission.

4. DATA SECURITY [DETAILED TERMS]
5. PUBLICATION REQUIREMENTS [DETAILED TERMS]
6. INTELLECTUAL PROPERTY [DETAILED TERMS]
7. DATA RETENTION AND DESTRUCTION [DETAILED TERMS]
8. COMPLIANCE [DETAILED TERMS]
9. LIABILITY AND INDEMNIFICATION [DETAILED TERMS]
10. TERM AND TERMINATION [DETAILED TERMS]

[SIGNATURES]
```

#### DUA Negotiation Workflow
**Process**:
1. **Initial Draft**: HealthDB generates DUA from template
2. **Recipient Legal Review**: Recipient's legal counsel reviews (15-30 days)
3. **Redlines**: Recipient sends marked-up version with requested changes
4. **Provider Legal Review**: HealthDB legal reviews changes (10-15 days)
5. **Negotiation**: Iterate on terms until agreement reached (1-3 rounds)
6. **Final Review**: Both parties approve final version
7. **Execution**: Electronic signatures collected (DocuSign)
8. **Activation**: Data access granted upon full execution

**Common Negotiated Terms**:
- Publication embargo periods (pharma often requests 60-90 days to review)
- Intellectual property ownership (especially for drug discoveries)
- Indemnification and liability limits
- Data destruction timelines
- Revenue sharing for commercialized products

#### Multi-Party DUAs
**Scenario**: Data from 5 institutions being shared with 1 research consortium

**Parties**:
- HealthDB (Data Controller)
- Institution A, B, C, D, E (Data Contributors)
- Research Consortium (Data Recipient)

**Agreement Structure**:
- **Master DUA**: HealthDB ↔ Research Consortium
- **Data Contributor Agreements**: HealthDB ↔ Each Institution
- **Terms**:
  - Each institution receives revenue share proportional to patients contributed
  - Institutions have right to review publications before submission
  - Research Consortium must acknowledge all contributing institutions

#### DUA Compliance Monitoring
**Automated Checks**:
- **Access Logging**: All data queries logged with user ID, timestamp, query hash
- **Rate Limit Enforcement**: Block queries exceeding licensed limits
- **Anomaly Detection**:
  - Queries attempting to isolate single patients (potential re-identification)
  - Excessive downloads (potential unauthorized sharing)
  - Access from unexpected IP addresses (potential credential sharing)
- **Alerts**: Notify compliance team of suspicious activity

**Violation Response**:
1. **Investigation**: Compliance team reviews logs
2. **Outreach**: Contact data recipient to clarify activity
3. **Warning**: First offense typically warning + corrective action
4. **Suspension**: Second offense or serious violation → suspend access
5. **Termination**: Third offense or egregious violation → terminate license
6. **Legal Action**: For re-identification attempts or unauthorized commercialization

## Data Quality and Validation

### Data Quality Framework

#### Completeness
**Metric**: % of required fields populated

**Thresholds**:
- **Critical Fields** (Demographics, Primary Diagnosis): 100% required
- **Important Fields** (Lab results, Medications): ≥80% required
- **Optional Fields** (Clinical notes, Imaging): No minimum

**Actions**:
- If <80% completeness: Flag for manual review
- If <50% completeness: Reject extraction, improve EMR query

#### Accuracy
**Validation Rules**:
- **Format Validation**: ICD-10 codes match regex, dates in ISO-8601
- **Value Range**: Lab values within biological range (e.g., hemoglobin 0-25 g/dL)
- **Consistency**: Diagnosis date ≤ treatment date ≤ outcome date
- **Cross-Field**: Age at diagnosis calculated from DOB and diagnosis date

**Actions**:
- If validation fails: Flag record for review
- If >10% of records fail: Halt extraction, investigate data quality issue

#### Timeliness
**Metric**: Data recency (how recently was EMR data updated)

**Thresholds**:
- **Prospective Studies**: Data updated within 7 days
- **Retrospective Studies**: Data updated within 30 days

**Actions**:
- Display data freshness on researcher dashboard
- Offer "refresh" option to re-query EMR for latest data

### Data Standardization

#### Terminology Mapping
**Source** → **Target Standard**:
- **Diagnoses**: ICD-9/10, SNOMED → ICD-10-CM
- **Procedures**: CPT, ICD-10-PCS, HCPCS → CPT + ICD-10-PCS
- **Medications**: Local formulary → RxNorm
- **Lab Tests**: Local lab codes → LOINC
- **Units**: Local units → UCUM (Unified Code for Units of Measure)

**Example**:
```
Source (Epic):
  Lab: "HGB" = 10.2, Unit: "g/dL"

Mapped (HealthDB):
  Lab: "Hemoglobin [Mass/volume] in Blood" (LOINC: 718-7)
  Value: 10.2
  Unit: "g/dL" (UCUM: g/dL)
```

#### FHIR Resource Mapping
**EMR Data** → **FHIR Resource**:
- Patient demographics → Patient resource
- Diagnoses → Condition resource
- Medications → MedicationRequest resource
- Lab results → Observation resource
- Procedures → Procedure resource
- Clinical notes → DocumentReference resource
- Vital signs → Observation resource (vital signs profile)

**Benefits**:
- Interoperability across institutions
- Compatibility with FHIR-based research tools
- Future-proof as healthcare moves to FHIR standard

## Revenue and Compensation Model

### Patient Revenue Sharing

**Revenue Distribution**:
- **Patients**: 30% of net revenue
- **Institutions**: 10% of net revenue
- **HealthDB Platform**: 60% of net revenue

**Patient Payout Calculation**:
```
Example: $100,000 license for dataset of 500 patients

Total Patient Share: $100,000 × 30% = $30,000

Per-Patient Base: $30,000 ÷ 500 = $60 per patient

Data Completeness Adjustment:
- Patient A (95% complete data): $60 × 1.20 = $72
- Patient B (80% complete data): $60 × 1.00 = $60
- Patient C (60% complete data): $60 × 0.80 = $48

Payment Method Options:
1. Cash (direct deposit or check)
2. HealthDB Points (redeemable for gift cards)
3. Charity donation (patient selects charity)
```

**Payment Frequency**:
- Quarterly distributions
- Minimum payout threshold: $10 per patient (accumulate until threshold met)
- Tax reporting: Issue 1099-MISC if annual total >$600 (US patients)

### Institutional Revenue Sharing

**Calculation**:
```
Example: Same $100,000 license, patients from 3 institutions

Total Institutional Share: $100,000 × 10% = $10,000

Distribution by Patient Count:
- Institution A contributed 250 patients: $10,000 × (250/500) = $5,000
- Institution B contributed 150 patients: $10,000 × (150/500) = $3,000
- Institution C contributed 100 patients: $10,000 × (100/500) = $2,000
```

**Payment Terms**:
- Quarterly payments
- No minimum threshold
- Direct wire transfer or ACH

### Pricing Transparency

**Researcher Pricing Calculator**:
- Input: Number of patients, data categories, license duration
- Output: Estimated cost by pricing tier (academic, startup, enterprise, pharma)
- Display: Cost breakdown (per-patient, base fee, access fee)

**Patient Revenue Estimator**:
- Show patients estimated earnings based on:
  - Data completeness score
  - Historical licensing activity (how often data in patient's category is licensed)
  - Projected earnings over time

## Technical Implementation Details

### Security Architecture

#### Authentication
**Multi-Factor Authentication (MFA)**:
- **Factor 1**: Password (bcrypt hashed with salt)
- **Factor 2**:
  - SMS code (Twilio integration)
  - Authenticator app (TOTP)
  - Biometric (WebAuthn passkey with fingerprint/FaceID)
  - Hardware token (YubiKey via WebAuthn)

**Session Management**:
- JWT tokens (15-minute expiration for access token)
- Refresh tokens (7-day expiration, stored in httpOnly cookie)
- Session invalidation on logout
- Automatic logout after 30 minutes inactivity

#### Data Encryption
**At Rest**:
- Database: PostgreSQL with Transparent Data Encryption (TDE)
- Files: AES-256-GCM encryption
- Backups: Encrypted with AWS KMS

**In Transit**:
- TLS 1.3 for all HTTPS traffic
- Certificate pinning for mobile apps
- VPN required for EMR connections

**Application-Level**:
- PHI fields encrypted at application level with separate key
- Key rotation every 90 days
- Hardware Security Module (HSM) for key storage

#### Access Control
**Role-Based Access Control (RBAC)**:
- **Roles**: Patient, Researcher, IRB Reviewer, Admin, Data Steward
- **Permissions**: Read, Write, Delete, Export, Admin
- **Scopes**: Own data, Study data, All data

**Row-Level Security**:
- Researchers can only query patients in their IRB-approved cohort
- Patients can only view their own records
- Admins can view all, audit logged

#### Audit Logging
**Logged Events**:
- All data access (who, what, when, why)
- All data modifications (before/after values)
- All authentication events (login, logout, failed attempts)
- All consent changes (signed, withdrawn, modified)
- All administrative actions (user creation, role changes)

**Log Storage**:
- Immutable audit log (append-only)
- Blockchain anchoring for critical events (consent signing, data access)
- Retained for 7 years (HIPAA requirement)

### Performance Optimization

#### Database Optimization
**Indexing Strategy**:
- B-tree indexes on frequently queried fields (patient_id, mrn_token, diagnosis_code)
- GiST indexes for date ranges
- Full-text search indexes for clinical notes
- Partial indexes for common cohort queries

**Query Optimization**:
- Materialized views for common aggregations
- Query result caching (Redis) for 5 minutes
- Partitioning large tables by date (monthly partitions)

**Connection Pooling**:
- PgBouncer connection pooler
- Connection pool size: 100 connections
- Transaction mode for short queries, session mode for long transactions

#### Caching Strategy
**Multi-Layer Cache**:
1. **CDN** (CloudFront): Static assets, public pages
2. **Application Cache** (Redis): API responses, session data
3. **Database Query Cache**: Query results
4. **Browser Cache**: JavaScript, CSS, images

**Cache Invalidation**:
- Time-based expiration (TTL)
- Event-based invalidation (on data update)
- Version-based cache keys (bust cache on deploy)

#### Scalability
**Horizontal Scaling**:
- API servers: Kubernetes auto-scaling (2-20 pods based on load)
- Background workers: Celery workers (5-50 workers based on queue depth)
- Database: Read replicas for queries, write to primary

**Load Balancing**:
- Application Load Balancer (ALB) for HTTP traffic
- Round-robin distribution to healthy pods
- Health checks every 30 seconds

### Disaster Recovery

#### Backup Strategy
**Database Backups**:
- Full backup: Daily at 2 AM UTC
- Incremental backup: Every 6 hours
- Transaction log backup: Every 15 minutes
- Retention: 30 days online, 7 years archived

**File Backups**:
- Uploaded files (consent forms, documents): Backed up to S3 Glacier
- Retention: 7 years

**Backup Testing**:
- Monthly restore test to verify backup integrity
- Quarterly disaster recovery drill (full system restore)

#### High Availability
**Uptime Target**: 99.9% (< 44 minutes downtime per month)

**Redundancy**:
- Multi-AZ database deployment (automatic failover)
- Multiple API server instances (minimum 2)
- Cross-region backup replication

**Failover Procedures**:
- Automatic database failover (< 60 seconds)
- Manual application failover (< 5 minutes)
- Documented runbooks for common failures

## Compliance and Certification

### HIPAA Compliance
**Administrative Safeguards**:
- [ ] Security Management Process
- [ ] Assigned Security Responsibility
- [ ] Workforce Security (background checks, access termination)
- [ ] Information Access Management
- [ ] Security Awareness Training
- [ ] Security Incident Procedures
- [ ] Contingency Plan (disaster recovery)
- [ ] Business Associate Agreements

**Physical Safeguards**:
- [ ] Facility Access Controls (data center security)
- [ ] Workstation Use and Security
- [ ] Device and Media Controls

**Technical Safeguards**:
- [ ] Access Control (unique user IDs, emergency access)
- [ ] Audit Controls (log all PHI access)
- [ ] Integrity Controls (detect unauthorized data changes)
- [ ] Transmission Security (encryption in transit)

### HITRUST Certification
**Goal**: Achieve HITRUST CSF Certification (healthcare industry security standard)

**Domains**:
1. Information Security Management Program
2. Access Control
3. Human Resources Security
4. Risk Management
5. Security Policy
6. Organization of Information Security
7. Compliance
8. Business Continuity Management
9. Information Systems Acquisition, Development, and Maintenance
10. Incident Management

**Timeline**: 12-18 months for initial certification, annual re-certification

### SOC 2 Type II
**Trust Service Criteria**:
- **Security**: System is protected against unauthorized access
- **Availability**: System is available for operation as committed
- **Confidentiality**: Confidential information is protected
- **Processing Integrity**: System processing is complete, valid, accurate, timely
- **Privacy**: Personal information is collected, used, retained, disclosed per commitments

**Audit Process**:
- 12-month audit period
- Third-party auditor reviews controls
- Annual re-audit

### GDPR Compliance (For EU Patients)
**Requirements**:
- [ ] Lawful basis for processing (consent)
- [ ] Data minimization (collect only necessary data)
- [ ] Right to access (patients can download their data)
- [ ] Right to erasure ("right to be forgotten")
- [ ] Right to data portability (export in machine-readable format)
- [ ] Data Protection Impact Assessment (DPIA)
- [ ] Data Protection Officer (DPO) appointed
- [ ] Breach notification (within 72 hours)
- [ ] Privacy by design and default

## Future Enhancements Roadmap

### Phase 1 (Next 6 Months)
- [ ] Integration with additional EMR systems (Athenahealth, eClinicalWorks)
- [ ] Mobile app for patient portal (iOS and Android)
- [ ] Real-time cohort monitoring dashboard
- [ ] Expanded marketplace with 50+ data products
- [ ] Patient community forum

### Phase 2 (6-12 Months)
- [ ] AI-powered cohort recommendation ("Similar studies used these criteria...")
- [ ] Federated learning support (train models without data leaving institutions)
- [ ] Genomic data integration (link clinical data to genomic databases)
- [ ] Natural language processing for clinical notes (extract structured data from text)
- [ ] Predictive analytics for trial recruitment (predict enrollment rates)

### Phase 3 (12-24 Months)
- [ ] International expansion (EU, Canada, Australia)
- [ ] Real-world evidence (RWE) platform for regulatory submissions
- [ ] Patient-reported outcomes (PRO) mobile app with wearable integration
- [ ] Decentralized clinical trial infrastructure
- [ ] API marketplace (third-party developers build on HealthDB)
