/**
 * Single source of truth for what HealthDB actually does today.
 *
 * Every integration, security control, workflow, module and metric shown
 * anywhere in the UI must resolve through this manifest. Copy that asserts a
 * capability without a matching `live` entry is a bug: the manifest is what
 * the content-consistency test checks against.
 *
 * States:
 *   live    — implemented and running. `evidence` names the file or the
 *             external record that backs it.
 *   pilot   — implemented but only exercised in the closed pilot; not
 *             something an outside party can rely on yet.
 *   planned — not built. Must never be described in the present tense.
 */

export const STATUS = {
  live: {
    label: 'Live',
    description: 'Implemented and running today.',
    className: 'border-emerald-400/40 text-emerald-300 bg-emerald-400/10',
  },
  pilot: {
    label: 'Pilot',
    description: 'Implemented, exercised only in the closed pilot.',
    className: 'border-sky-400/40 text-sky-300 bg-sky-400/10',
  },
  planned: {
    label: 'Planned',
    description: 'Not built. Described here as an intention, not a capability.',
    className: 'border-amber-400/40 text-amber-300 bg-amber-400/10',
  },
};

export const FEATURES = {
  // ---- Data ingestion -----------------------------------------------------
  'ingest.fhir-upload': {
    name: 'Manual FHIR bundle upload',
    status: 'live',
    evidence: 'api/fhir_ingest.py, POST /api/patient/connections/fhir',
    note: 'A patient uploads their own FHIR R4 bundle. Consent is required first.',
  },
  'ingest.emr-direct': {
    name: 'Direct EHR connection',
    status: 'planned',
    note: 'No EHR vendor connection exists. Records arrive only by manual upload.',
  },
  'ingest.epic': { name: 'Epic connection', status: 'planned',
    note: 'No Epic integration, sandbox or production.' },
  'ingest.cerner': { name: 'Cerner connection', status: 'planned',
    note: 'No Cerner integration, sandbox or production.' },
  'ingest.bulk-fhir': { name: 'Bulk FHIR $export', status: 'planned' },
  'ingest.hl7v2': { name: 'HL7v2 ingestion', status: 'planned',
    note: 'No MLLP listener and no HL7v2 parser.' },
  'ingest.claims': { name: 'Claims (X12 837/835)', status: 'planned' },
  'ingest.omop': { name: 'OMOP CDM normalization', status: 'planned',
    note: 'No OMOP vocabulary or mapping code in the repository.' },

  // ---- Privacy ------------------------------------------------------------
  'privacy.identifier-removal': {
    name: 'Direct identifier removal (Safe Harbor-oriented, not certified)',
    status: 'live',
    evidence: 'api/deidentification.py',
    note: 'Removes identifier-bearing keys and redacts email, phone, SSN, URL, '
        + 'long digit strings and ZIP patterns from free text. No named-entity '
        + 'recognition, so a name written into prose can survive.',
  },
  'privacy.date-truncation': {
    name: 'Dates reduced to year (truncated, not shifted)',
    status: 'live',
    evidence: 'api/fhir_ingest._year_only, tests/test_date_truncation.py',
    note: 'Month and day are discarded at parse time and never persisted.',
  },
  'privacy.age-capping': {
    name: 'Ages over 89 capped',
    status: 'live',
    evidence: 'api/deidentification._cap_age',
  },
  'privacy.residual-scan': {
    name: 'Residual identifier scan before export',
    status: 'live',
    evidence: 'api/deidentification.find_residual_identifiers',
    note: 'An export whose rows still match identifier patterns fails instead of releasing.',
  },
  'privacy.small-cell': {
    name: 'Small-cell suppression',
    status: 'live',
    evidence: 'min_cell_size in api/main.py',
  },
  'privacy.expert-determination': {
    name: 'Expert Determination review',
    status: 'planned',
    note: 'No qualified statistician has reviewed the pipeline. The automated '
        + 'transformations are Safe Harbor-oriented but have not been certified '
        + 'as meeting any de-identification standard.',
  },
  'privacy.nlp-deid': {
    name: 'NLP de-identification of free text',
    status: 'planned',
    note: 'No named-entity recognition. Names embedded in prose may survive.',
  },
  'privacy.k-anonymity': { name: 'k-anonymity verification', status: 'planned',
    note: 'No k is computed or enforced on any output.' },
  'privacy.date-shifting': { name: 'Date shifting to preserve intervals', status: 'planned',
    note: 'Dates are truncated today, which loses the intervals a shift would keep. '
        + 'Recovering them needs Expert Determination, not Safe Harbor.' },
  'privacy.differential-privacy': { name: 'Differential privacy on aggregates', status: 'planned',
    note: 'No noise is added to aggregate queries.' },
  'privacy.tokenized-relink': { name: 'Tokenized re-linkage', status: 'planned' },

  // ---- Security -----------------------------------------------------------
  'security.rbac': {
    name: 'Database-backed role checks',
    status: 'live',
    evidence: 'api/main.current_user, docs/AUTHORIZATION.md',
    note: 'Roles resolve from the user row on every request; the JWT never grants privilege.',
  },
  'security.researcher-approval': {
    name: 'Explicit researcher approval',
    status: 'live',
    evidence: 'api/main.require_approved_researcher',
  },
  'security.password-hashing': {
    name: 'PBKDF2-SHA256 password hashing',
    status: 'live',
    evidence: 'api/main.hash_password, 600,000 iterations',
  },
  'security.audit-log': {
    name: 'Access audit log',
    status: 'live',
    evidence: 'DataAccessLog, healthdb.audit logger',
    note: 'Ordinary database table. Not tamper-evident.',
  },
  'security.consent-gating': {
    name: 'Consent checked at query time',
    status: 'live',
    evidence: 'api/main.py consent filters',
  },
  'security.mfa': { name: 'Multi-factor authentication', status: 'planned' },
  'security.rls': { name: 'Postgres row-level security', status: 'planned',
    note: 'Authorization is enforced in the application, not by RLS policies.' },
  'security.kms': { name: 'AWS KMS key management', status: 'planned',
    note: 'No KMS integration; no boto3 dependency.' },
  'security.waf': { name: 'Web application firewall', status: 'planned' },
  'security.api-gateway': { name: 'API gateway', status: 'planned' },
  'security.signed-urls': { name: 'Expiring signed download URLs', status: 'planned' },
  'security.pen-test': { name: 'Independent penetration test', status: 'planned',
    note: 'Never performed.' },
  'security.soc2': { name: 'SOC 2 Type II', status: 'planned',
    note: 'No audit commenced.' },

  // ---- Research workflow --------------------------------------------------
  'research.cohort-builder': {
    name: 'Cohort builder',
    status: 'pilot',
    evidence: 'POST /api/cohort/build',
    note: 'Runs against whatever pilot data exists, which is currently very little.',
  },
  'research.feasibility-counts': {
    name: 'Aggregate feasibility counts',
    status: 'pilot',
    note: 'Subject to small-cell suppression.',
  },
  'research.study-management': { name: 'Study records', status: 'pilot' },
  'research.export': {
    name: 'De-identified CSV export',
    status: 'pilot',
    evidence: 'GET /api/extraction/jobs/{job_id}/download',
  },
  'research.federated-query': { name: 'Federated querying', status: 'planned',
    note: 'Single database. No federation.' },
  'research.trial-matching': { name: 'Clinical trial matching', status: 'planned' },

  // ---- Governance ---------------------------------------------------------
  'governance.irb-tracking': {
    name: 'IRB and agreement record-keeping',
    status: 'pilot',
    note: 'Tracks platform state only. A record here is not evidence of a '
        + 'legally executed IRB approval, DUA, reliance agreement or BAA.',
  },
  'governance.central-sirb': { name: 'Central single IRB', status: 'planned',
    note: 'No sIRB arrangement exists.' },
  'governance.prenegotiated-dua': { name: 'Pre-negotiated DUAs', status: 'planned',
    note: 'No executed data use agreements with any institution.' },
  'governance.dual-review': { name: 'Dual review before data release', status: 'planned' },
  'governance.incident-response': { name: 'Incident response procedure', status: 'planned' },

  // ---- Patient ------------------------------------------------------------
  'patient.consent-management': { name: 'Granular consent and revocation', status: 'live',
    evidence: 'POST /api/consent/sign, POST /api/consent/{id}/revoke' },
  'patient.access-log': { name: 'Patient-visible access log', status: 'live',
    evidence: 'GET /api/patient/data-access-log' },
  'patient.deletion-request': { name: 'Data deletion request', status: 'live',
    evidence: 'POST /api/patient/request-deletion' },
  'patient.rewards': {
    name: 'Rewards programme',
    status: 'planned',
    note: 'Points are an internal counter with no monetary value. There is no '
        + 'ledger, no redemption API, no fulfilment provider and no terms. '
        + 'Redemption is disabled and must stay disabled.',
  },
};

/** Look up a feature, failing loudly rather than rendering an unknown claim. */
export function getFeature(key) {
  const feature = FEATURES[key];
  if (!feature) {
    throw new Error(
      `Unknown feature key "${key}". Add it to src/data/featureStatus.js `
      + 'so its status is stated explicitly.'
    );
  }
  return feature;
}

export const isLive = (key) => getFeature(key).status === 'live';

/** Keys grouped by state, for pages that summarise the whole manifest. */
export function featuresByStatus(status) {
  return Object.entries(FEATURES)
    .filter(([, f]) => f.status === status)
    .map(([key, f]) => ({ key, ...f }));
}
