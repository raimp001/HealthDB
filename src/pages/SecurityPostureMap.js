import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import TargetArchitectureBanner from '../components/TargetArchitectureBanner';

const securityZones = [
  {
    id: 'external',
    name: 'External Zone',
    color: 'text-red-400',
    bg: 'bg-red-400/5',
    border: 'border-red-400/20',
    components: ['EHR Systems (Epic, Cerner)', 'Patient Browsers/Apps', 'Researcher Clients', 'ClinicalTrials.gov API'],
    controls: ['TLS 1.3 in transit', 'IP allowlisting', 'Rate limiting (100 req/min)', 'WAF (OWASP Top 10)'],
    phiPresent: true,
    phiDetail: 'PHI originates here — raw EHR data, patient demographics, clinical notes.',
  },
  {
    id: 'dmz',
    name: 'DMZ / API Gateway',
    color: 'text-orange-400',
    bg: 'bg-orange-400/5',
    border: 'border-orange-400/20',
    components: ['FHIR Proxy (SMART-on-FHIR)', 'HL7v2 MLLP Listener', 'API Gateway (Kong/AWS)', 'OAuth 2.0 Authorization Server'],
    controls: ['JWT validation & scope checks', 'Request schema validation', 'CORS policy enforcement', 'DDoS protection'],
    phiPresent: true,
    phiDetail: 'PHI passes through — tokens exchanged, data validated before ingestion.',
  },
  {
    id: 'app',
    name: 'Application Zone',
    color: 'text-amber-400',
    bg: 'bg-amber-400/5',
    border: 'border-amber-400/20',
    components: ['Ingestion Workers', 'OMOP Normalizer', 'De-identification Engine', 'Cohort Builder API', 'Dataset Export Service'],
    controls: ['Service-to-service mTLS', 'Supabase auth middleware', 'PHI boundary enforcement', 'Input sanitization'],
    phiPresent: true,
    phiDetail: 'PHI processed here — ingested, normalized, then de-identified before storage.',
  },
  {
    id: 'data',
    name: 'Data Zone',
    color: 'text-emerald-400',
    bg: 'bg-emerald-400/5',
    border: 'border-emerald-400/20',
    components: ['Supabase PostgreSQL (RLS)', 'OMOP CDM Tables', 'Audit Log Store', 'Token Vault (AWS KMS)'],
    controls: ['Row-Level Security (25+ policies)', 'AES-256 encryption at rest', 'Backup encryption (AWS KMS)', 'Connection pooling (PgBouncer)'],
    phiPresent: false,
    phiDetail: 'De-identified data only. Tokenized linkage keys stored separately in vault.',
  },
  {
    id: 'export',
    name: 'Export Zone',
    color: 'text-blue-400',
    bg: 'bg-blue-400/5',
    border: 'border-blue-400/20',
    components: ['Dataset Builder', 'Export Pipeline', 'Signed URL Generator', 'Data Dictionary Service'],
    controls: ['Study-scoped access only', 'Re-identification risk check', 'Expiring download links (24h)', 'Export audit logging'],
    phiPresent: false,
    phiDetail: 'De-identified exports only. Re-identification risk assessed before release.',
  },
];

const accessPaths = [
  {
    name: 'Researcher Access',
    color: 'text-emerald-400',
    steps: [
      { zone: 'External', action: 'Login via Supabase Auth (email/OAuth)' },
      { zone: 'DMZ', action: 'JWT issued with study_id claims' },
      { zone: 'App', action: 'Cohort builder queries OMOP tables' },
      { zone: 'Data', action: 'RLS filters rows to approved study cohort' },
      { zone: 'Export', action: 'De-identified dataset generated & signed URL returned' },
    ],
  },
  {
    name: 'EHR Ingestion',
    color: 'text-blue-400',
    steps: [
      { zone: 'External', action: 'EHR initiates Bulk FHIR $export or HL7v2 feed' },
      { zone: 'DMZ', action: 'SMART-on-FHIR token validated; schema checked' },
      { zone: 'App', action: 'Ingestion worker → OMOP normalizer → De-ID engine' },
      { zone: 'Data', action: 'De-identified records stored; linkage tokens vaulted' },
    ],
  },
  {
    name: 'Patient Portal',
    color: 'text-purple-400',
    steps: [
      { zone: 'External', action: 'Patient logs in via Epic MyChart or Supabase Auth' },
      { zone: 'DMZ', action: 'FHIR proxy fetches patient data with patient scope' },
      { zone: 'App', action: 'Consent manager stores granular consent preferences' },
      { zone: 'Data', action: 'Patient sees own data (RLS: user_id = auth.uid())' },
    ],
  },
  {
    name: 'Admin / Compliance',
    color: 'text-amber-400',
    steps: [
      { zone: 'External', action: 'Admin logs in with MFA (TOTP or WebAuthn)' },
      { zone: 'DMZ', action: 'Admin JWT with role=admin claim' },
      { zone: 'App', action: 'Access audit logs, user management, RLS policy editor' },
      { zone: 'Data', action: 'Read-only audit store; no direct PHI table access' },
    ],
  },
];

const rlsPolicies = [
  { table: 'research_datasets', policy: 'study_researcher_access', roles: 'researcher', rule: 'study_id IN (SELECT study_id FROM study_members WHERE user_id = auth.uid())' },
  { table: 'patient_records', policy: 'patient_own_data', roles: 'patient', rule: 'patient_id = auth.uid()' },
  { table: 'cohort_results', policy: 'study_scoped_cohort', roles: 'researcher', rule: 'study_id = current_setting(\'app.current_study\')' },
  { table: 'audit_logs', policy: 'admin_read_only', roles: 'admin', rule: 'role = \'admin\' AND operation = \'SELECT\'' },
  { table: 'consent_records', policy: 'patient_consent_owner', roles: 'patient', rule: 'patient_id = auth.uid()' },
  { table: 'irb_protocols', policy: 'institution_access', roles: 'institution', rule: 'institution_id IN (SELECT inst_id FROM institution_members WHERE user_id = auth.uid())' },
  { table: 'data_exports', policy: 'approved_export_only', roles: 'researcher', rule: 'status = \'approved\' AND researcher_id = auth.uid()' },
  { table: 'token_vault', policy: 'service_role_only', roles: 'service_role', rule: 'FALSE (no direct access; service role only via API)' },
];

const phiBoundary = {
  entry: ['FHIR R4 Patient/Encounter/Observation resources', 'HL7v2 PID/PV1/OBX segments', 'Patient-uploaded documents (PDF, images)', 'Claims data (837/835 with member ID)'],
  processing: ['Name, DOB, SSN, MRN extraction', 'Address geocoding to 3-digit ZIP', 'Planned: date shifting (truncated to year today)', 'Planned: free-text NLP de-identification'],
  storage: [
    { location: 'Ingestion staging (temporary)', encrypted: true, retention: '72 hours max', phiPresent: true },
    { location: 'OMOP CDM tables', encrypted: true, retention: 'Indefinite', phiPresent: false },
    { location: 'Token vault (linkage keys)', encrypted: true, retention: 'Study duration + 7 years', phiPresent: true },
    { location: 'Audit log store', encrypted: true, retention: '7 years', phiPresent: false },
  ],
  deIdSteps: [
    'Remove identifier-bearing fields and redact identifier patterns from text',
    'Replace MRN/SSN with irreversible hash (SHA-256 + salt)',
    'Planned: shift dates by per-patient offset (truncated to year today)',
    'Generalize ZIP to 3-digit prefix',
    'Suppress ages > 89',
    'Planned: NLP scan for PHI in free-text fields',
    'Planned: verify k-anonymity on the output dataset',
  ],
  reLink: 'Tokenized re-linkage available under IRB-approved protocol only. Tokens stored in AWS KMS vault with dual-custodian access.',
  exit: 'Planned: a final re-identification risk check and expiring signed download URLs. Today an export is rejected if residual identifier patterns are detected.',
};

const views = ['Security Zones', 'Access Paths', 'RLS Policies', 'PHI Boundary Map'];

const SecurityPostureMap = () => {
  const [activeView, setActiveView] = useState(views[0]);

  return (
    <div className="bg-black text-white min-h-screen pt-24">
      <div className="max-w-6xl mx-auto px-6 py-16">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">Target Security Architecture</h1>
          <p className="text-white/60 max-w-2xl mb-12">
            PHI boundaries, access paths, and authorization controls across every layer of HealthDB.
          </p>
        </motion.div>
        <TargetArchitectureBanner
          implemented={["Role checks resolved from the database", "PBKDF2-SHA256 password hashing (600k iterations)", "Consent checked at query time", "Append-only access logging", "Identifier removal and year-only dates (api/deidentification.py)"]}
          planned={["Supabase / Row-Level Security", "AWS KMS token vault", "API gateway (Kong) and WAF", "MFA (TOTP / WebAuthn)", "Signed expiring download URLs"]}
        />

        {/* View Tabs */}
        <div className="flex flex-wrap gap-2 mb-12">
          {views.map((v) => (
            <button
              key={v}
              onClick={() => setActiveView(v)}
              className={`px-4 py-2 text-sm border transition-colors ${
                activeView === v ? 'bg-white/10 border-white/20 text-white' : 'border-white/5 text-white/60 hover:text-white/70'
              }`}
            >
              {v}
            </button>
          ))}
        </div>

        {/* Security Zones View */}
        {activeView === 'Security Zones' && (
          <motion.div key="zones" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            {securityZones.map((zone) => (
              <div key={zone.id} className={`p-6 border ${zone.border} ${zone.bg}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className={`text-lg font-bold ${zone.color}`}>{zone.name}</h3>
                  <span className={`text-xs px-3 py-1 border ${zone.phiPresent ? 'border-red-400/30 text-red-400' : 'border-emerald-400/30 text-emerald-400'}`}>
                    {zone.phiPresent ? 'PHI PRESENT' : 'DE-IDENTIFIED'}
                  </span>
                </div>
                <p className="text-sm text-white/60 mb-4">{zone.phiDetail}</p>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-xs text-amber-400 uppercase tracking-wider mb-2">Target components — not deployed</h4>
                    <ul className="space-y-1">
                      {zone.components.map((c) => (
                        <li key={c} className="text-sm text-white/60">• {c}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-xs text-amber-400 uppercase tracking-wider mb-2">Target controls — not implemented</h4>
                    <ul className="space-y-1">
                      {zone.controls.map((c) => (
                        <li key={c} className="text-sm text-white/60">✓ {c}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {/* Access Paths View */}
        {activeView === 'Access Paths' && (
          <motion.div key="paths" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
            {accessPaths.map((path) => (
              <div key={path.name} className="p-6 border border-white/10">
                <h3 className={`text-lg font-bold mb-4 ${path.color}`}>{path.name}</h3>
                <div className="space-y-3">
                  {path.steps.map((step, i) => (
                    <div key={i} className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-20 text-xs text-white/50 pt-0.5">{step.zone}</div>
                      <div className={`flex-shrink-0 w-6 h-6 rounded-full border flex items-center justify-center text-xs ${path.color} border-current`}>{i + 1}</div>
                      <div className="text-sm text-white/60">{step.action}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {/* RLS Policies View */}
        {activeView === 'RLS Policies' && (
          <motion.div key="rls" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="border border-white/10">
              <div className="grid grid-cols-4 gap-4 p-4 border-b border-white/10 text-xs text-white/50 uppercase tracking-wider">
                <span>Table</span>
                <span>Policy</span>
                <span>Role</span>
                <span>Rule</span>
              </div>
              {rlsPolicies.map((p, i) => (
                <div key={i} className="grid grid-cols-4 gap-4 p-4 border-b border-white/5 text-sm">
                  <span className="text-emerald-400 font-mono text-xs">{p.table}</span>
                  <span className="text-white/60">{p.policy}</span>
                  <span className="text-blue-400 text-xs">{p.roles}</span>
                  <span className="text-white/60 font-mono text-xs break-all">{p.rule}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* PHI Boundary Map View */}
        {activeView === 'PHI Boundary Map' && (
          <motion.div key="phi" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-6 border border-red-400/20 bg-red-400/5">
                <h3 className="text-red-400 font-bold mb-3">PHI Entry Points</h3>
                <ul className="space-y-2">
                  {phiBoundary.entry.map((e) => (
                    <li key={e} className="text-sm text-white/60">⚠ {e}</li>
                  ))}
                </ul>
              </div>
              <div className="p-6 border border-amber-400/20 bg-amber-400/5">
                <h3 className="text-amber-400 font-bold mb-3">PHI Processing</h3>
                <ul className="space-y-2">
                  {phiBoundary.processing.map((p) => (
                    <li key={p} className="text-sm text-white/60">→ {p}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="p-6 border border-emerald-400/20">
              <h3 className="text-emerald-400 font-bold mb-3">De-identification Steps</h3>
              <div className="grid md:grid-cols-2 gap-2">
                {phiBoundary.deIdSteps.map((step, i) => (
                  <div key={i} className="text-sm text-white/60 flex gap-2">
                    <span className="text-emerald-400">{i + 1}.</span> {step}
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6 border border-white/10">
              <h3 className="text-white font-bold mb-3">PHI Storage Locations</h3>
              <div className="space-y-3">
                {phiBoundary.storage.map((s) => (
                  <div key={s.location} className="flex items-center justify-between p-3 border border-white/5">
                    <div>
                      <div className="text-sm text-white/80">{s.location}</div>
                      <div className="text-xs text-white/50">Retention: {s.retention}</div>
                    </div>
                    <div className="flex gap-3">
                      <span className={`text-xs px-2 py-1 border ${s.phiPresent ? 'border-red-400/30 text-red-400' : 'border-emerald-400/30 text-emerald-400'}`}>
                        {s.phiPresent ? 'PHI' : 'De-ID'}
                      </span>
                      <span className="text-xs px-2 py-1 border border-blue-400/30 text-blue-400">Encrypted</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-6 border border-purple-400/20 bg-purple-400/5">
                <h3 className="text-purple-400 font-bold mb-2">Re-linkage</h3>
                <p className="text-sm text-white/50">{phiBoundary.reLink}</p>
              </div>
              <div className="p-6 border border-blue-400/20 bg-blue-400/5">
                <h3 className="text-blue-400 font-bold mb-2">Data Exit</h3>
                <p className="text-sm text-white/50">{phiBoundary.exit}</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Navigation */}
        <div className="mt-12 flex flex-wrap gap-4">
          <Link to="/platform" className="px-6 py-3 border border-white/20 text-sm hover:bg-white/5 transition-colors">
            ← Platform Focus Areas
          </Link>
          <Link to="/data-flow" className="px-6 py-3 border border-white/20 text-sm hover:bg-white/5 transition-colors">
            Data Flow Diagram →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default SecurityPostureMap;
