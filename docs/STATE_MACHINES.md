# HealthDB Platform - Complete Architecture & State Machines

HealthDB.ai eliminates regulatory friction and data fragmentation for multi-center clinical research while giving patients ownership of their health data.

---

## Table of Contents

1. [Patient Data Contribution Flow](#1-patient-data-contribution-flow)
2. [Researcher Study Creation Flow](#2-researcher-study-creation-flow)
3. [EMR Integration Flow](#3-emr-integration-flow)
4. [Cohort Query Engine](#4-cohort-query-engine)
5. [Regulatory Automation Engine](#5-regulatory-automation-engine)
6. [Collaboration Workspace](#6-collaboration-workspace)
7. [Data Extraction Pipeline](#7-data-extraction-pipeline)
8. [Authentication & Authorization](#8-authentication--authorization)
9. [System Architecture](#9-system-architecture)
10. [API Reference](#10-api-reference)

---

## 1. Patient Data Contribution Flow

### 1.1 Complete State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PATIENT DATA CONTRIBUTION STATE MACHINE                  │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   VISITOR    │
                              └──────┬───────┘
                                     │ Register
                                     ▼
                              ┌──────────────┐
                              │  ONBOARDED   │ ─► +100 pts welcome bonus
                              │  (Identity   │
                              │  Verified)   │
                              └──────┬───────┘
                                     │ Sign Consent
                                     ▼
                        ┌────────────────────────┐
                        │    CONSENT_GRANTED     │ ─► +50 pts per consent type
                        │  (Master Consent +     │
                        │   Granular Prefs)      │
                        └────────────┬───────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
     ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
     │ MANUAL_ENTRY   │    │  EMR_LINKED    │    │  DEVICE_SYNC   │
     │ (Forms/PROs)   │    │ (Epic/Cerner)  │    │ (Wearables)    │
     │                │    │ +100 pts       │    │ +50 pts        │
     └───────┬────────┘    └───────┬────────┘    └───────┬────────┘
             │                     │                     │
             └──────────────┬──────┴─────────────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │ DATA_VALIDATED │
                   │ (QC + Mapping  │
                   │  to OMOP CDM)  │
                   └───────┬────────┘
                           │
                           ▼
                   ┌────────────────┐
                   │  DATA_BANKED   │◄────────────────────┐
                   │ (Available for │                     │
                   │   Queries)     │                     │
                   └───────┬────────┘                     │
                           │                              │
              ┌────────────┼────────────┐                 │
              │            │            │                 │
              ▼            ▼            ▼                 │
         ┌────────┐  ┌──────────┐  ┌────────────┐        │
         │QUERIED │  │CONSENTED │  │ WITHDRAWN  │────────┘
         │(Stats  │  │_TO_STUDY │  │ (Patient   │  (Partial)
         │only)   │  │(Specific │  │  Revokes)  │
         │+10 pts │  │ project) │  │            │
         └────────┘  │+25 pts   │  └────────────┘
                     └──────────┘
```

### 1.2 Consent Tiers

| Tier | Description | Data Access | Patient Control |
|------|-------------|-------------|-----------------|
| **Tier 1** | De-identified aggregate only | Stats and counts | Default, lowest risk |
| **Tier 2** | Limited dataset for approved research | Demographics, diagnosis, treatment (no dates) | Per-study approval |
| **Tier 3** | Identifiable for re-contact | Full profile for trial matching | Explicit opt-in |
| **Tier 4** | Ongoing EMR linkage | Real-time data sync | Richest data, highest rewards |

### 1.3 Patient Dashboard Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PATIENT DASHBOARD                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   MY CONSENT    │  │  MY DATA        │  │   MY REWARDS    │             │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤             │
│  │ ✓ Research      │  │ ● Epic MyChart  │  │ Balance: 450 pts│             │
│  │ ✓ Trial Match   │  │   (Connected)   │  │ ≈ $4.50 value   │             │
│  │ ○ AI Training   │  │ ○ Apple Health  │  │                 │             │
│  │                 │  │   (Not linked)  │  │ [Redeem]        │             │
│  │ [Manage]        │  │ [+ Connect]     │  │ [History]       │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      WHO ACCESSED MY DATA                              │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ Jan 10  Dr. Smith's MM Study     Aggregate only    OHSU               │ │
│  │ Jan 08  HealthDB Quality Check   De-identified     Internal           │ │
│  │ Jan 05  DREAMM-8 Trial Match     Identified*       Fred Hutch         │ │
│  │         * You were contacted about eligibility                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      MY CONTRIBUTED DATA                               │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ Category        Records    Quality    Last Updated                     │ │
│  │ Demographics    1          95%        Jan 11, 2025                     │ │
│  │ Diagnosis       3          87%        Jan 10, 2025                     │ │
│  │ Treatments      8          92%        Jan 10, 2025                     │ │
│  │ Lab Results     45         78%        Jan 09, 2025                     │ │
│  │ Molecular       2          100%       Dec 15, 2024                     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  [⚠️ WITHDRAW ALL DATA] ─► One-click revoke with downstream propagation    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Researcher Study Creation Flow

### 2.1 Complete State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RESEARCHER STUDY CREATION STATE MACHINE                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ RESEARCHER   │
│ (Registered) │
└──────┬───────┘
       │ Create Study Request
       ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           STUDY_DRAFT                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Define:                                                             │   │
│  │ • Research Question                                                 │   │
│  │ • Target Population (ICD codes, demographics, treatment history)    │   │
│  │ • Required Variables (labs, vitals, outcomes, genomics)             │   │
│  │ • Data Level (de-identified / limited dataset / identifiable)       │   │
│  │ • Timeline & Budget                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   │ Submit
                                   ▼
                        ┌────────────────────┐
                        │  FEASIBILITY_CHECK │
                        │  ┌──────────────┐  │
                        │  │ Auto-query:  │  │
                        │  │ • N eligible │  │
                        │  │ • Data       │  │
                        │  │   completeness│  │
                        │  │ • Cost est.  │  │
                        │  └──────────────┘  │
                        └─────────┬──────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
           ┌───────────────┐          ┌────────────────┐
           │ INSUFFICIENT  │          │ FEASIBLE       │
           │ (Modify query)│          │ (Proceed)      │
           └───────────────┘          └───────┬────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REGULATORY_PIPELINE                                 │
│                                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌────────────┐  │
│   │ IRB_CENTRAL │───►│ DUA_GEN     │───►│ INST_IRB    │───►│ EMR_ACCESS │  │
│   │ (HealthDB's │    │ (Auto-gen   │    │ (Reliance   │    │ (Site-     │  │
│   │  sIRB)      │    │  template)  │    │  Agreement) │    │  specific) │  │
│   └─────────────┘    └─────────────┘    └─────────────┘    └────────────┘  │
│                                                                             │
│   States: PENDING → SUBMITTED → UNDER_REVIEW → APPROVED / REVISION_REQ     │
└─────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              │ All Approved
                                              ▼
                                   ┌────────────────────┐
                                   │   COHORT_LOCKED    │
                                   │ (MRNs identified,  │
                                   │  variables mapped) │
                                   └─────────┬──────────┘
                                             │
                                             ▼
                                   ┌────────────────────┐
                                   │  DATA_EXTRACTION   │
                                   │ ┌────────────────┐ │
                                   │ │ Pull from:     │ │
                                   │ │ • HealthDB     │ │
                                   │ │ • Linked EMRs  │ │
                                   │ │ • Registries   │ │
                                   │ └────────────────┘ │
                                   └─────────┬──────────┘
                                             │
                                             ▼
                                   ┌────────────────────┐
                                   │  DATASET_DELIVERED │
                                   │  (Secure download  │
                                   │   or API access)   │
                                   └─────────┬──────────┘
                                             │
                                             ▼
                                   ┌────────────────────┐
                                   │  STUDY_COMPLETE    │
                                   │  (Results linked   │
                                   │   to publications) │
                                   └────────────────────┘
```

### 2.2 Researcher Self-Service Workflow

| Step | Action | System Support |
|------|--------|----------------|
| 1. **Explore** | Browse de-identified cohort sizes by disease/treatment | Pre-computed counts, no approval needed |
| 2. **Define** | Build cohort with visual query builder | ICD-10, CPT, drug codes, temporal logic |
| 3. **Feasibility** | Instant N counts + data completeness scores | Federated query, no PHI exposed |
| 4. **Request** | Submit for regulatory review | Auto-generated IRB protocol |
| 5. **Track** | Dashboard shows IRB/DUA status across sites | Status: PENDING → APPROVED |
| 6. **Extract** | Secure download or API access | De-identification pipeline |
| 7. **Publish** | Link results back to HealthDB | Outcome tracking |

---

## 3. EMR Integration Flow

### 3.1 Integration State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     EMR INTEGRATION STATE MACHINE                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌────────────────┐
│ INSTITUTION    │
│ (Onboarding)   │
└───────┬────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────────┐
│                    INTEGRATION_SETUP                           │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Requirements:                                           │   │
│  │ • BAA signed with HealthDB                              │   │
│  │ • IT Security Review completed                          │   │
│  │ • FHIR endpoint configured OR                           │   │
│  │   Epic Cosmos/Cerner Real-World Data access granted     │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬───────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │ FHIR_DIRECT    │ │ FLAT_FILE      │ │ API_BROKER     │
     │ (Real-time     │ │ (Batch export, │ │ (Cosmos,       │
     │  R4 API)       │ │  SFTP)         │ │  TriNetX)      │
     └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
             │                  │                  │
             └──────────────────┼──────────────────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │  DATA_TRANSFORMER  │
                     │  ┌──────────────┐  │
                     │  │ • Parse      │  │
                     │  │ • Validate   │  │
                     │  │ • Map to     │  │
                     │  │   OMOP CDM   │  │
                     │  │ • De-identify│  │
                     │  └──────────────┘  │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │   LINKED_ACTIVE    │
                     │  (Institution in   │
                     │   HealthDB network)│
                     └────────────────────┘
```

### 3.2 EMR Connection Matrix

| EMR System | Integration Method | Latency | Coverage |
|------------|-------------------|---------|----------|
| **Epic** | FHIR R4 / Epic Cosmos | Real-time / Daily | Full chart |
| **Cerner** | FHIR / Cerner RWD | Real-time / Weekly | Full chart |
| **Meditech** | HL7v2 → FHIR bridge | Daily | Core data |
| **Allscripts** | FHIR + flat file | Daily | Most data |
| **Others** | Secure SFTP | Weekly | Structured |

### 3.3 Patient EMR Linkage Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PATIENT EMR LINKAGE FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. PATIENT SIGNS CONSENT (Tier 4 - Ongoing EMR Linkage)                   │
│     └─► System checks which EMR patient uses                                │
│                                                                             │
│  2. SELECT EMR SOURCE                                                       │
│     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐               │
│     │ Epic MyChart   │ │ Cerner         │ │ Manual Upload  │               │
│     │ [Connect]      │ │ [Connect]      │ │ [Upload Files] │               │
│     └────────┬───────┘ └────────┬───────┘ └────────┬───────┘               │
│              │                  │                  │                        │
│  3. OAUTH FLOW (Epic/Cerner)                                                │
│     └─► Redirect to MyChart → Patient logs in → Grants access              │
│     └─► Receive OAuth token → Store encrypted                               │
│                                                                             │
│  4. INITIAL DATA PULL                                                       │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ Query patient record for:                                        │    │
│     │ • Demographics (age range, sex, race)                            │    │
│     │ • Conditions (ICD-10 codes)                                      │    │
│     │ • Medications (NDC codes, dates)                                 │    │
│     │ • Procedures (CPT codes)                                         │    │
│     │ • Lab Results (LOINC codes, values)                              │    │
│     │ • Vitals (height, weight, BP)                                    │    │
│     │ • Encounters (dates, types)                                      │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  5. DE-IDENTIFICATION                                                       │
│     └─► Apply HIPAA Safe Harbor (remove 18 identifiers)                    │
│     └─► Generalize: DOB → age range, dates → month/year                    │
│     └─► Truncate: zip → 3 digits                                           │
│                                                                             │
│  6. MAP TO OMOP CDM                                                         │
│     └─► ICD-10 → SNOMED CT                                                 │
│     └─► NDC → RxNorm                                                       │
│     └─► LOINC → OMOP concepts                                              │
│                                                                             │
│  7. STORE IN HEALTHDB                                                       │
│     └─► Patient sees summary in dashboard                                   │
│     └─► Data available for research queries                                │
│     └─► +100 points awarded                                                │
│                                                                             │
│  8. ONGOING SYNC (if Tier 4)                                                │
│     └─► Background job refreshes data weekly                               │
│     └─► Patient notified of new data added                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Cohort Query Engine

### 4.1 Variable Extraction State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COHORT QUERY ENGINE STATE MACHINE                        │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │ QUERY_INPUT  │
                              └──────┬───────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COHORT DEFINITION                                   │
│                                                                             │
│  Inclusion Criteria (AND/OR logic):                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Diagnosis: ICD-10 codes (e.g., C90.0 - Multiple Myeloma)          │    │
│  │ • Treatment: Drug classes, regimens (e.g., VRd, Dara-KRd)           │    │
│  │ • Demographics: Age range, sex, race/ethnicity                       │    │
│  │ • Labs: Threshold values (e.g., creatinine > 2.0)                    │    │
│  │ • Temporal: Diagnosis date range, follow-up duration                 │    │
│  │ • Prior lines: # of prior therapies, specific exposures              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Exclusion Criteria:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Concurrent malignancies                                            │    │
│  │ • Missing critical data fields                                       │    │
│  │ • Consent withdrawal                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
                            ┌────────────────────┐
                            │ COHORT_IDENTIFIED  │
                            │ • N = X patients   │
                            │ • MRNs flagged     │
                            │   (internal only)  │
                            └─────────┬──────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      VARIABLE SELECTION                                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Available Variable Categories:                                       │    │
│  │                                                                       │    │
│  │ DEMOGRAPHICS      LABS/BIOMARKERS     TREATMENTS                     │    │
│  │ ├─ Age            ├─ CBC w/ diff      ├─ Regimen name                │    │
│  │ ├─ Sex            ├─ CMP              ├─ Start/stop dates            │    │
│  │ ├─ Race           ├─ LDH              ├─ Dose/schedule               │    │
│  │ ├─ Zip (3-digit)  ├─ Beta-2 micro     ├─ Cycles completed            │    │
│  │ └─ Insurance      ├─ SPEP/UPEP        ├─ Reason for d/c              │    │
│  │                   ├─ Free light chains│                              │    │
│  │ STAGING           └─ Cytogenetics     OUTCOMES                       │    │
│  │ ├─ ISS/R-ISS                          ├─ Best response               │    │
│  │ ├─ Bone lesions                       ├─ PFS (per IMWG)              │    │
│  │ └─ Extramedullary                     ├─ OS                          │    │
│  │                                        ├─ MRD status                  │    │
│  │ TOXICITIES        PROCEDURES          └─ Subsequent therapy          │    │
│  │ ├─ CRS grade      ├─ SCT date/type                                   │    │
│  │ ├─ ICANS grade    ├─ Radiation                                       │    │
│  │ ├─ Cytopenias     └─ Supportive care                                 │    │
│  │ └─ Infections                                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
                            ┌────────────────────┐
                            │ DATA_EXTRACTED     │
                            │ • Flat file (CSV)  │
                            │ • REDCap export    │
                            │ • API stream       │
                            └────────────────────┘
```

### 4.2 Disease-Specific Variable Sets

| Disease | Core Variables | Staging | Molecular | Outcomes |
|---------|---------------|---------|-----------|----------|
| **Multiple Myeloma** | Age, sex, race, insurance | ISS, R-ISS, bone lesions | del(17p), t(4;14), t(14;16), 1q+ | PFS, OS, MRD, best response |
| **DLBCL** | Age, sex, race, ECOG | Ann Arbor, IPI | Cell of origin, BCL2/MYC | CR rate, EFS, OS |
| **AML** | Age, sex, race, WBC | ELN risk | FLT3, NPM1, IDH1/2, TP53 | CR rate, OS, relapse rate |
| **Breast Cancer** | Age, sex, race, menopausal | TNM, grade | ER, PR, HER2, BRCA | PFS, OS, pCR |
| **NSCLC** | Age, sex, race, smoking | TNM, stage | EGFR, ALK, KRAS, PD-L1 | PFS, OS, ORR |

---

## 5. Regulatory Automation Engine

### 5.1 Complete Regulatory Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REGULATORY AUTOMATION PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1: CENTRAL IRB (HealthDB as sIRB of Record)                         │
│  ──────────────────────────────────────────────────                         │
│                                                                             │
│  ┌──────────────┐                                                           │
│  │ STUDY_DRAFT  │ ─► Researcher completes protocol form                    │
│  └──────┬───────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────┐                                                       │
│  │ PROTOCOL_GEN     │ ─► Auto-populate NIH/OHRP template                   │
│  │                  │ ─► Include: study aims, cohort criteria,             │
│  │                  │    data elements, de-ID method                       │
│  └──────┬───────────┘                                                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────┐                                                       │
│  │ IRB_SUBMITTED    │ ─► Electronic submission to HealthDB IRB             │
│  │                  │ ─► Expedited review (minimal risk)                   │
│  │                  │ ─► Full board (identifiable data)                    │
│  └──────┬───────────┘                                                       │
│         │                                                                   │
│         ├─────────────────────────────┐                                     │
│         ▼                             ▼                                     │
│  ┌──────────────────┐         ┌──────────────────┐                         │
│  │ IRB_APPROVED     │         │ REVISION_REQ     │ ─► Modify and resubmit  │
│  │ Protocol #HDB-   │         │ (Specific fixes  │                         │
│  │ YYYY-NNNN        │         │  requested)      │                         │
│  └──────┬───────────┘         └──────────────────┘                         │
│         │                                                                   │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  PHASE 2: DATA USE AGREEMENT (Auto-Generated)                              │
│  ──────────────────────────────────────────────                            │
│                                                                             │
│  ┌──────────────────┐                                                       │
│  │ DUA_DRAFT        │ ─► Pre-templated based on data level:                │
│  │                  │    • Limited dataset                                  │
│  │                  │    • De-identified                                    │
│  │                  │    • Identifiable (stricter terms)                   │
│  └──────┬───────────┘                                                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────┐                                                       │
│  │ DUA_SENT         │ ─► DocuSign to PI and institution                    │
│  └──────┬───────────┘                                                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────┐                                                       │
│  │ DUA_SIGNED       │ ─► All parties have signed                           │
│  │                  │ ─► Expires: 2 years from signature                   │
│  └──────┬───────────┘                                                       │
│         │                                                                   │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  PHASE 3: SITE RELIANCE AGREEMENTS (Per Institution)                       │
│  ────────────────────────────────────────────────────                      │
│                                                                             │
│  For each participating site:                                               │
│                                                                             │
│  ┌──────────────────┐                                                       │
│  │ RELIANCE_INIT    │ ─► Send agreement to site IRB                        │
│  └──────┬───────────┘    (Pre-negotiated template available)               │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────┐                                                       │
│  │ SITE_REVIEW      │ ─► Site IRB reviews and signs                        │
│  │                  │ ─► Typical: 1-3 weeks                                │
│  └──────┬───────────┘                                                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────┐                                                       │
│  │ SITE_APPROVED    │ ─► Site can contribute data to study                 │
│  └──────────────────┘                                                       │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  PHASE 4: EMR ACCESS AUTHORIZATION                                          │
│  ──────────────────────────────────                                         │
│                                                                             │
│  ┌──────────────────┐                                                       │
│  │ EMR_ACCESS_REQ   │ ─► Request specific variables from site EMR          │
│  └──────┬───────────┘                                                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────┐                                                       │
│  │ DATA_EXTRACTION  │ ─► Pull data for approved cohort                     │
│  │ _AUTHORIZED      │ ─► Apply de-identification                           │
│  └──────────────────┘                                                       │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  DASHBOARD: Track All Statuses                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Study: Bispecific Ab Outcomes in R/R MM                               │ │
│  │ ─────────────────────────────────────────────────────────────────     │ │
│  │ [✓] Central IRB (HealthDB sIRB)         APPROVED   2025-01-05        │ │
│  │ [✓] Data Use Agreement                   SIGNED    2025-01-06        │ │
│  │ [◐] OHSU Reliance Agreement             PENDING   (~3 days)          │ │
│  │ [ ] Fred Hutch Reliance Agreement       NOT STARTED                  │ │
│  │ [ ] Emory Reliance Agreement            NOT STARTED                  │ │
│  │                                                                       │ │
│  │ [Download Protocol]  [Download DUA]  [Send Reminder]  [View Timeline] │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Pre-Negotiated Agreements

| Institution | Reliance Agreement | Typical Turnaround | EMR System |
|-------------|-------------------|-------------------|------------|
| OHSU Knight Cancer Institute | ✓ Active | 5 days | Epic |
| Fred Hutchinson Cancer Center | ✓ Active | 7 days | Epic |
| Emory Winship Cancer Institute | ✓ Active | 10 days | Cerner |
| Mayo Clinic | ◐ Pending | TBD | Epic |
| MD Anderson | ◐ In Progress | TBD | Epic |

---

## 6. Collaboration Workspace

### 6.1 Collaboration State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COLLABORATION WORKSPACE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STUDY TEAM MANAGEMENT                                                      │
│  ─────────────────────                                                      │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Principal Investigator (Owner)                                        │  │
│  │ • Full access to all study data                                       │  │
│  │ • Can invite/remove team members                                      │  │
│  │ • Signs DUA on behalf of team                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Co-Investigators                                                      │  │
│  │ • Full data access (per DUA)                                          │  │
│  │ • Can run queries, export data                                        │  │
│  │ • Cannot modify study settings                                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Data Analysts                                                         │  │
│  │ • View de-identified data only                                        │  │
│  │ • Run pre-approved queries                                            │  │
│  │ • Cannot export raw data                                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Statisticians                                                         │  │
│  │ • Access to analysis workspace                                        │  │
│  │ • Can run statistical models                                          │  │
│  │ • Export aggregate results only                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  SHARED WORKSPACE FEATURES                                                  │
│  ──────────────────────────                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │ │ Documents   │  │ Data Files  │  │ Analysis    │  │ Discussion  │   │ │
│  │ │             │  │             │  │             │  │             │   │ │
│  │ │ - Protocol  │  │ - Raw data  │  │ - R/Python  │  │ - Comments  │   │ │
│  │ │ - DUA       │  │ - Cleaned   │  │   notebooks │  │ - Decisions │   │ │
│  │ │ - IRB docs  │  │ - Analysis  │  │ - Results   │  │ - Questions │   │ │
│  │ │ - Consent   │  │   ready     │  │ - Figures   │  │ - Approvals │   │ │
│  │ └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  INVITE FLOW                                                                │
│  ──────────                                                                 │
│                                                                             │
│  PI clicks "Invite Collaborator"                                            │
│       │                                                                     │
│       ▼                                                                     │
│  ┌──────────────────┐                                                       │
│  │ Enter email      │                                                       │
│  │ Select role      │                                                       │
│  │ Set permissions  │                                                       │
│  └──────┬───────────┘                                                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────┐                                                       │
│  │ INVITE_SENT      │ ─► Email with secure link                            │
│  └──────┬───────────┘                                                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────┐                                                       │
│  │ INVITE_ACCEPTED  │ ─► User creates account or links existing            │
│  │                  │ ─► Signs individual DUA acknowledgment               │
│  └──────┬───────────┘                                                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────┐                                                       │
│  │ ACCESS_GRANTED   │ ─► Full access per role                              │
│  │                  │ ─► Activity logged                                   │
│  └──────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Multi-Center Study Coordination

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-CENTER COORDINATION DASHBOARD                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Study: Bispecific Ab Outcomes in R/R MM                                   │
│  Status: Data Collection (3/5 sites active)                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Site                 │ Patients │ Regulatory │ Data Status │ Contact  │ │
│  ├──────────────────────┼──────────┼────────────┼─────────────┼──────────┤ │
│  │ OHSU Knight          │    847   │ ✓ Approved │ ✓ Complete  │ Dr. A    │ │
│  │ Fred Hutchinson      │    512   │ ✓ Approved │ ◐ 75%       │ Dr. B    │ │
│  │ Emory Winship        │    234   │ ◐ Pending  │ ○ Not started│ Dr. C   │ │
│  │ Mayo Clinic          │    389   │ ○ Invited  │ ○ Not started│ Dr. D   │ │
│  │ MD Anderson          │    156   │ ○ Not sent │ ○ Not started│ -       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Total Enrolled: 1,593 (Target: 2,000)                                     │
│  Projected Completion: March 2025                                          │
│                                                                             │
│  [Send Reminder to Pending] [Generate Progress Report] [Schedule Meeting]  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Data Extraction Pipeline

### 7.1 End-to-End Extraction Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATA EXTRACTION PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TRIGGER: All regulatory approvals complete                                 │
│           │                                                                 │
│           ▼                                                                 │
│  ┌────────────────────┐                                                     │
│  │ 1. COHORT QUERY    │                                                     │
│  │    ┌────────────┐  │                                                     │
│  │    │ Apply:     │  │                                                     │
│  │    │ - ICD-10   │  │ ─► Returns list of de-identified patient IDs       │
│  │    │ - Age      │  │    matching criteria across all sites              │
│  │    │ - Treatment│  │                                                     │
│  │    │ - Stage    │  │    Example: 1,593 patients                         │
│  │    └────────────┘  │                                                     │
│  └─────────┬──────────┘                                                     │
│            │                                                                │
│            ▼                                                                │
│  ┌────────────────────┐                                                     │
│  │ 2. VARIABLE PULL   │                                                     │
│  │    ┌────────────┐  │                                                     │
│  │    │ For each   │  │                                                     │
│  │    │ patient:   │  │                                                     │
│  │    │            │  │                                                     │
│  │    │ ✓ Age      │  │ ─► Pull from OMOP CDM tables                       │
│  │    │ ✓ Sex      │  │    (condition_occurrence, drug_exposure,           │
│  │    │ ✓ Stage    │  │     measurement, procedure, etc.)                  │
│  │    │ ✓ Regimen  │  │                                                     │
│  │    │ ✓ PFS      │  │                                                     │
│  │    │ ✓ CRS grade│  │                                                     │
│  │    └────────────┘  │                                                     │
│  └─────────┬──────────┘                                                     │
│            │                                                                │
│            ▼                                                                │
│  ┌────────────────────┐                                                     │
│  │ 3. DE-IDENTIFICATION│                                                    │
│  │    ┌────────────┐  │                                                     │
│  │    │ Apply HIPAA│  │                                                     │
│  │    │ Safe Harbor│  │                                                     │
│  │    │            │  │                                                     │
│  │    │ Remove:    │  │ ─► All 18 HIPAA identifiers stripped               │
│  │    │ - Names    │  │    Dates generalized to month/year                 │
│  │    │ - MRNs     │  │    Ages >89 capped at 90                           │
│  │    │ - DOB      │  │    Zip codes truncated to 3 digits                 │
│  │    │ - Addresses│  │                                                     │
│  │    │ - SSN      │  │                                                     │
│  │    │ - etc.     │  │                                                     │
│  │    └────────────┘  │                                                     │
│  └─────────┬──────────┘                                                     │
│            │                                                                │
│            ▼                                                                │
│  ┌────────────────────┐                                                     │
│  │ 4. QUALITY CHECK   │                                                     │
│  │    ┌────────────┐  │                                                     │
│  │    │ Validate:  │  │                                                     │
│  │    │ - Complete-│  │ ─► Data quality score per variable                 │
│  │    │   ness     │  │    Flag missing/outlier values                     │
│  │    │ - Ranges   │  │    Verify de-identification complete               │
│  │    │ - Formats  │  │                                                     │
│  │    │ - Re-ID    │  │                                                     │
│  │    │   risk     │  │                                                     │
│  │    └────────────┘  │                                                     │
│  └─────────┬──────────┘                                                     │
│            │                                                                │
│            ▼                                                                │
│  ┌────────────────────┐                                                     │
│  │ 5. OUTPUT FORMAT   │                                                     │
│  │    ┌────────────┐  │                                                     │
│  │    │ Export as: │  │                                                     │
│  │    │            │  │                                                     │
│  │    │ • CSV      │◄─┼─── Standard flat file                              │
│  │    │ • REDCap   │◄─┼─── Import-ready format                             │
│  │    │ • FHIR     │◄─┼─── API stream (real-time)                          │
│  │    │ • SAS      │◄─┼─── Statistical analysis                            │
│  │    └────────────┘  │                                                     │
│  └─────────┬──────────┘                                                     │
│            │                                                                │
│            ▼                                                                │
│  ┌────────────────────┐                                                     │
│  │ 6. SECURE DELIVERY │                                                     │
│  │                    │                                                     │
│  │ • Encrypted        │ ─► Download link expires in 7 days                 │
│  │   download         │    Access logged for audit                         │
│  │ • Secure enclave   │    Terms of use acknowledged                       │
│  │   (no download)    │                                                     │
│  │ • API access       │                                                     │
│  │   (rate-limited)   │                                                     │
│  └────────────────────┘                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Authentication & Authorization

### 8.1 Role-Based Access Control

| Role | Patient Portal | Researcher Portal | Admin Portal | Data Access |
|------|---------------|-------------------|--------------|-------------|
| **Patient** | ✓ Full | ✗ | ✗ | Own data only |
| **Researcher** | ✗ | ✓ Full | ✗ | Approved studies only |
| **Institution Admin** | ✗ | ✓ Limited | ✓ Institution | Institution data |
| **HealthDB Admin** | ✓ View | ✓ View | ✓ Full | All data (audit logged) |

---

## 9. System Architecture

### 9.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HEALTHDB ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                              USERS                                          │
│           ┌──────────┬──────────┬──────────┬──────────┐                    │
│           │ Patients │Researchers│Institutions│ Admins │                    │
│           └────┬─────┴────┬─────┴────┬─────┴────┬────┘                     │
│                │          │          │          │                          │
│                ▼          ▼          ▼          ▼                          │
│    ┌─────────────────────────────────────────────────────────┐             │
│    │                     FRONTEND                             │             │
│    │                   (React SPA)                            │             │
│    │                                                          │             │
│    │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │             │
│    │  │Patient │ │Researcher│ │Cohort │ │Collab  │ │Admin   │ │             │
│    │  │Portal  │ │Dashboard│ │Builder│ │Space   │ │Portal  │ │             │
│    │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │             │
│    └───────────────────────────┬─────────────────────────────┘             │
│                                │                                            │
│                                ▼                                            │
│    ┌─────────────────────────────────────────────────────────┐             │
│    │                     API LAYER                            │             │
│    │                    (FastAPI)                             │             │
│    │                                                          │             │
│    │  /auth  /patient  /researcher  /study  /regulatory       │             │
│    │  /cohort  /extraction  /collaboration  /emr  /admin      │             │
│    └───────────────────────────┬─────────────────────────────┘             │
│                                │                                            │
│                                ▼                                            │
│    ┌─────────────────────────────────────────────────────────┐             │
│    │                   DATA LAYER                             │             │
│    │                                                          │             │
│    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │             │
│    │  │ PostgreSQL  │  │ Redis       │  │ S3/Blob     │      │             │
│    │  │ (OMOP CDM)  │  │ (Cache/     │  │ (Documents/ │      │             │
│    │  │             │  │  Sessions)  │  │  Exports)   │      │             │
│    │  └─────────────┘  └─────────────┘  └─────────────┘      │             │
│    └───────────────────────────┬─────────────────────────────┘             │
│                                │                                            │
│                                ▼                                            │
│    ┌─────────────────────────────────────────────────────────┐             │
│    │              EMR INTEGRATION LAYER                       │             │
│    │                                                          │             │
│    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │             │
│    │  │ FHIR R4     │  │ Epic Cosmos │  │ Cerner RWD  │      │             │
│    │  │ Connector   │  │ Connector   │  │ Connector   │      │             │
│    │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │             │
│    │         │                │                │              │             │
│    │         ▼                ▼                ▼              │             │
│    │  ┌─────────────────────────────────────────────────┐    │             │
│    │  │              OMOP CDM Mapper                     │    │             │
│    │  │          (Standardization Layer)                 │    │             │
│    │  └─────────────────────────────────────────────────┘    │             │
│    └───────────────────────────┬─────────────────────────────┘             │
│                                │                                            │
│                                ▼                                            │
│    ┌─────────────────────────────────────────────────────────┐             │
│    │                  PARTNER INSTITUTIONS                    │             │
│    │                                                          │             │
│    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │             │
│    │  │   OHSU   │  │Fred Hutch│  │  Emory   │  │  Mayo    │ │             │
│    │  │  (Epic)  │  │  (Epic)  │  │ (Cerner) │  │  (Epic)  │ │             │
│    │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │             │
│    └─────────────────────────────────────────────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. API Reference

### 10.1 Core Endpoints

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Auth** | `/api/auth/register` | POST | Register new user |
| | `/api/auth/login` | POST | Authenticate user |
| **Patient** | `/api/patient/profile` | GET | Get patient profile |
| | `/api/patient/consents` | GET/POST | Manage consents |
| | `/api/patient/connections` | GET/POST | EMR connections |
| | `/api/patient/extracted-data` | GET | View contributed data |
| **Researcher** | `/api/researcher/studies` | GET/POST | Manage studies |
| | `/api/cohort/build` | POST | Build patient cohort |
| | `/api/cohort/save` | POST | Save cohort |
| **Regulatory** | `/api/regulatory/submit` | POST | Submit IRB/DUA |
| | `/api/regulatory/{id}/approve` | POST | Approve submission |
| **Extraction** | `/api/extraction/create` | POST | Create extraction job |
| | `/api/extraction/jobs` | GET | List extraction jobs |
| **Collaboration** | `/api/study/{id}/team` | GET/POST | Manage team |
| | `/api/study/{id}/invite` | POST | Invite collaborator |
| **EMR** | `/api/emr/connections` | GET | List EMR connections |
| | `/api/institutions` | GET | List partner institutions |

---

## Summary: End-to-End Workflow

```
PATIENT FLOW:
Register → Sign Consent → Connect EMR → Data Extracted → Contribute → Earn Rewards

RESEARCHER FLOW:
Create Study → Define Cohort → Check Feasibility → Submit IRB → Sign DUA →
Site Approvals → Extract Data → Analyze → Publish

TIMELINE: 3-4 weeks from study creation to data delivery
(vs. 6+ months traditional)
```

---

## Competitive Differentiation

| Competitor | Gap HealthDB Fills |
|------------|--------------------|
| Flatiron | Oncology-only; no patient ownership |
| TriNetX | No patient portal; institution-only |
| Veradigm | Limited real-time EMR; no multi-center coordination |
| Epic Cosmos | Walled garden; no external researcher access |
| **HealthDB** | Patient-owned + researcher self-service + regulatory automation |
