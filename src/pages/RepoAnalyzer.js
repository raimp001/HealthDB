import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import TargetArchitectureBanner from '../components/TargetArchitectureBanner';

const repoModules = [
  {
    id: 'emr-connectors',
    name: 'emr-connectors',
    description: 'FHIR R4, Bulk FHIR, and HL7v2 connector implementations for EHR data ingestion.',
    dataSources: [
      { name: 'Epic FHIR R4', type: 'EHR' },
      { name: 'Cerner FHIR R4', type: 'EHR' },
      { name: 'HL7v2 ADT/ORU', type: 'HL7' },
      { name: 'Bulk FHIR $export', type: 'FHIR' },
    ],
    phiEntryPoints: [
      { location: 'fhir-client.ts:fetchPatientBundle()', risk: 'high', detail: 'Raw Patient, Encounter, Condition resources with MRN, name, DOB' },
      { location: 'hl7-parser.ts:parsePID()', risk: 'high', detail: 'PID segment contains name, SSN, address, phone' },
      { location: 'bulk-export.ts:downloadNDJSON()', risk: 'high', detail: 'Bulk export NDJSON files contain all patient identifiers' },
    ],
    phiStorage: [
      { location: 'ingestion_staging table', persistence: 'Temporary (72h TTL)', encrypted: true },
      { location: 'Raw NDJSON files (S3)', persistence: 'Temporary (24h TTL)', encrypted: true },
    ],
    deIdSteps: ['None at this layer — PHI passed through to normalization pipeline'],
    authBoundaries: [
      'SMART-on-FHIR OAuth 2.0 token per EHR connection',
      'Connector credentials stored in AWS KMS vault',
      'Service role only — no user-facing access',
    ],
  },
  {
    id: 'data-collection',
    name: 'data-collection',
    description: 'Normalization and de-identification pipeline. Maps raw data to OMOP CDM and strips PHI.',
    dataSources: [
      { name: 'OMOP Vocabulary (Athena)', type: 'Reference' },
      { name: 'ICD-10 → SNOMED maps', type: 'Reference' },
      { name: 'RxNorm concepts', type: 'Reference' },
      { name: 'LOINC lab codes', type: 'Reference' },
    ],
    phiEntryPoints: [
      { location: 'normalizer.ts:mapToOMOP()', risk: 'high', detail: 'Receives raw resources with PHI for vocabulary mapping' },
      { location: 'deid-engine.ts:processRecord()', risk: 'critical', detail: 'PHI boundary — this function strips all 18 HIPAA identifiers' },
    ],
    phiStorage: [
      { location: 'normalization_queue', persistence: 'Temporary (in-memory)', encrypted: true },
      { location: 'omop_cdm.person (post de-ID)', persistence: 'Permanent', encrypted: true },
    ],
    deIdSteps: [
      'Remove names, SSN, MRN (SHA-256 hash + salt)',
      'Date shift (±180 day per-patient offset)',
      'ZIP generalization (3-digit prefix)',
      'Age suppression (> 89)',
      'NLP scan for PHI in free-text',
      'k-anonymity check (k >= 5)',
    ],
    authBoundaries: [
      'Internal service — no external access',
      'De-ID engine runs in isolated container',
      'Output validated before write to OMOP tables',
    ],
  },
  {
    id: 'api',
    name: 'api',
    description: 'REST API layer serving cohort builder, dataset export, and study management endpoints.',
    dataSources: [
      { name: 'Supabase PostgreSQL', type: 'Database' },
      { name: 'OMOP CDM tables', type: 'Database' },
    ],
    phiEntryPoints: [
      { location: 'routes/patients.ts:getOwnRecord()', risk: 'medium', detail: 'Patient can view own data (re-linked via token)' },
    ],
    phiStorage: [
      { location: 'API response cache (Redis)', persistence: 'Temporary (5min TTL)', encrypted: true },
    ],
    deIdSteps: ['Serves de-identified data only (except patient-own-data endpoint)'],
    authBoundaries: [
      'Supabase Auth JWT validation on every request',
      'RLS policies enforce study-scoped access',
      'Rate limiting: 100 req/min per user',
      'CORS restricted to app domains',
    ],
  },
  {
    id: 'patient-portal',
    name: 'patient-portal',
    description: 'Patient-facing UI for consent management, record viewing, and data contribution.',
    dataSources: [
      { name: 'Epic MyChart (FHIR)', type: 'EHR' },
      { name: 'Patient uploads', type: 'Patient' },
    ],
    phiEntryPoints: [
      { location: 'MyChartConnect.tsx:fetchRecords()', risk: 'medium', detail: 'Patient-scoped FHIR data fetched via MyChart OAuth' },
      { location: 'UploadForm.tsx:handleUpload()', risk: 'medium', detail: 'Patient-uploaded documents may contain PHI' },
    ],
    phiStorage: [
      { location: 'Browser memory only', persistence: 'Session', encrypted: false },
    ],
    deIdSteps: ['Patient data displayed to patient (not de-identified for owner)', 'Uploaded documents scanned for PHI before storage'],
    authBoundaries: [
      'Supabase Auth (email/OAuth) or Epic MyChart OAuth',
      'RLS: patient_id = auth.uid()',
      'Consent stored per data category',
    ],
  },
  {
    id: 'security',
    name: 'security',
    description: 'Audit logging, access control policies, credential vault, and compliance monitoring.',
    dataSources: [
      { name: 'Audit event stream', type: 'Internal' },
      { name: 'AWS KMS', type: 'Infrastructure' },
    ],
    phiEntryPoints: [
      { location: 'audit-logger.ts:logAccess()', risk: 'low', detail: 'Logs user_id and resource_id — no PHI content logged' },
    ],
    phiStorage: [
      { location: 'audit_logs table', persistence: '7 years', encrypted: true },
      { location: 'Token vault (KMS)', persistence: 'Study + 7 years', encrypted: true },
    ],
    deIdSteps: ['Audit logs contain resource IDs only, no PHI content', 'Token vault stores encrypted linkage keys (HSM-backed)'],
    authBoundaries: [
      'Admin role required for audit log access',
      'Token vault: dual-custodian access control',
      'No direct database access — API-only',
    ],
  },
  {
    id: 'research',
    name: 'research',
    description: 'Cohort builder, feasibility engine, dataset export, and clinical trial matching.',
    dataSources: [
      { name: 'OMOP CDM (de-identified)', type: 'Database' },
      { name: 'ClinicalTrials.gov', type: 'Public' },
    ],
    phiEntryPoints: [
      { location: 'No PHI entry points', risk: 'none', detail: 'Operates on de-identified OMOP data only' },
    ],
    phiStorage: [
      { location: 'cohort_results table', persistence: 'Study duration', encrypted: true },
      { location: 'export_files (S3)', persistence: '30 days', encrypted: true },
    ],
    deIdSteps: ['Input is already de-identified', 'k-anonymity check on export (k >= 5)', 'Re-identification risk assessment before download'],
    authBoundaries: [
      'RLS: study_id must match researcher assignment',
      'Export requires IRB approval status = approved',
      'Download via signed URLs (24h TTL)',
    ],
  },
  {
    id: 'oncology',
    name: 'oncology',
    description: 'Cancer-specific data models, staging calculations, and outcome tracking.',
    dataSources: [
      { name: 'Tumor registry data', type: 'Registry' },
      { name: 'AJCC staging tables', type: 'Reference' },
      { name: 'Treatment protocols', type: 'Reference' },
    ],
    phiEntryPoints: [
      { location: 'registry-import.ts:importRecords()', risk: 'high', detail: 'Tumor registry CSV files contain patient identifiers' },
    ],
    phiStorage: [
      { location: 'registry_staging', persistence: 'Temporary (72h)', encrypted: true },
    ],
    deIdSteps: ['Registry records de-identified through standard pipeline', 'Cancer staging computed on de-identified data'],
    authBoundaries: [
      'Registry import restricted to institution admin role',
      'De-identified oncology data follows standard RLS policies',
    ],
  },
  {
    id: 'infrastructure',
    name: 'infrastructure',
    description: 'Deployment, monitoring, CI/CD, and infrastructure-as-code configurations.',
    dataSources: [
      { name: 'AWS CloudWatch', type: 'Infrastructure' },
      { name: 'Terraform state', type: 'Infrastructure' },
    ],
    phiEntryPoints: [
      { location: 'No PHI entry points', risk: 'none', detail: 'Infrastructure layer does not process clinical data' },
    ],
    phiStorage: [],
    deIdSteps: ['N/A — no clinical data at this layer'],
    authBoundaries: [
      'AWS IAM roles with least-privilege',
      'Terraform state encrypted at rest',
      'CI/CD secrets via GitHub Actions encrypted secrets',
    ],
  },
];

const views = ['Overview', 'Module Explorer', 'PHI Inventory', 'Auth Boundaries'];

const RepoAnalyzer = () => {
  const [activeView, setActiveView] = useState(views[0]);
  const [selectedModule, setSelectedModule] = useState(repoModules[0].id);
  const selected = repoModules.find((m) => m.id === selectedModule);

  const totalDataSources = repoModules.reduce((sum, m) => sum + m.dataSources.length, 0);
  const totalPhiEntry = repoModules.reduce((sum, m) => sum + m.phiEntryPoints.filter((p) => p.risk !== 'none').length, 0);
  const totalPhiStorage = repoModules.reduce((sum, m) => sum + m.phiStorage.length, 0);
  const totalDeId = repoModules.reduce((sum, m) => sum + m.deIdSteps.length, 0);
  const totalAuth = repoModules.reduce((sum, m) => sum + m.authBoundaries.length, 0);

  return (
    <div className="bg-black text-white min-h-screen pt-24">
      <div className="max-w-6xl mx-auto px-6 py-16">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">Target Module Map</h1>
          <p className="text-white/60 max-w-2xl mb-12">
            Inferred labels across all HealthDB modules: data sources, PHI entry points, de-identification steps, and authorization boundaries.
          </p>
        </motion.div>
        <TargetArchitectureBanner
          implemented={["FastAPI + SQLAlchemy service", "Safe Harbor de-identification module", "Consent and audit-log tables"]}
          planned={["Supabase RLS policies", "AWS KMS credential vault", "NLP de-identification of free text", "OMOP CDM tables"]}
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

        {/* Overview */}
        {activeView === 'Overview' && (
          <motion.div key="overview" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
              {[
                { label: 'Data Sources', value: totalDataSources, color: 'text-cyan-400' },
                { label: 'PHI Entry Points', value: totalPhiEntry, color: 'text-red-400' },
                { label: 'PHI Storage', value: totalPhiStorage, color: 'text-amber-400' },
                { label: 'De-ID Steps', value: totalDeId, color: 'text-emerald-400' },
                { label: 'Auth Boundaries', value: totalAuth, color: 'text-purple-400' },
              ].map((s) => (
                <div key={s.label} className="p-4 border border-white/10 text-center">
                  <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
                  <div className="text-xs text-white/50 uppercase tracking-wider mt-1">{s.label}</div>
                </div>
              ))}
            </div>

            <div className="space-y-3">
              {repoModules.map((m) => (
                <div key={m.id} className="p-4 border border-white/10 flex items-center justify-between">
                  <div>
                    <span className="text-white font-medium font-mono text-sm">{m.name}/</span>
                    <span className="text-white/60 text-sm ml-3">{m.description}</span>
                  </div>
                  <div className="flex gap-3 text-xs">
                    <span className="text-cyan-400">{m.dataSources.length} src</span>
                    <span className="text-red-400">{m.phiEntryPoints.filter((p) => p.risk !== 'none').length} phi</span>
                    <span className="text-purple-400">{m.authBoundaries.length} auth</span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Module Explorer */}
        {activeView === 'Module Explorer' && selected && (
          <motion.div key="explorer" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="flex flex-wrap gap-2 mb-8">
              {repoModules.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setSelectedModule(m.id)}
                  className={`px-3 py-1.5 text-xs font-mono border transition-colors ${
                    selectedModule === m.id ? 'bg-white/10 border-white/20 text-white' : 'border-white/5 text-white/60 hover:text-white/70'
                  }`}
                >
                  {m.name}/
                </button>
              ))}
            </div>

            <div className="space-y-6">
              <div className="p-6 border border-white/10">
                <h3 className="font-bold mb-2">{selected.name}/</h3>
                <p className="text-sm text-white/50 mb-4">{selected.description}</p>

                <h4 className="text-xs text-white/50 uppercase tracking-wider mb-2">Data Sources</h4>
                <div className="flex flex-wrap gap-2 mb-4">
                  {selected.dataSources.map((ds) => (
                    <span key={ds.name} className="text-xs px-2 py-1 border border-cyan-400/20 text-cyan-400">
                      {ds.type}: {ds.name}
                    </span>
                  ))}
                </div>

                <h4 className="text-xs text-white/50 uppercase tracking-wider mb-2">PHI Entry Points</h4>
                <div className="space-y-2 mb-4">
                  {selected.phiEntryPoints.map((p) => (
                    <div key={p.location} className="flex items-start gap-3 text-sm">
                      <span className={`text-xs px-2 py-0.5 border flex-shrink-0 ${
                        p.risk === 'critical' ? 'border-red-500 text-red-400' :
                        p.risk === 'high' ? 'border-red-400/50 text-red-400' :
                        p.risk === 'medium' ? 'border-amber-400/50 text-amber-400' :
                        p.risk === 'low' ? 'border-emerald-400/50 text-emerald-400' :
                        'border-white/10 text-white/50'
                      }`}>{p.risk}</span>
                      <div>
                        <div className="text-white/70 font-mono text-xs">{p.location}</div>
                        <div className="text-white/60">{p.detail}</div>
                      </div>
                    </div>
                  ))}
                </div>

                <h4 className="text-xs text-white/50 uppercase tracking-wider mb-2">De-identification Steps</h4>
                <ul className="space-y-1 mb-4">
                  {selected.deIdSteps.map((step) => (
                    <li key={step} className="text-sm text-white/50">✓ {step}</li>
                  ))}
                </ul>

                <h4 className="text-xs text-white/50 uppercase tracking-wider mb-2">Auth Boundaries</h4>
                <ul className="space-y-1">
                  {selected.authBoundaries.map((ab) => (
                    <li key={ab} className="text-sm text-white/50">🔒 {ab}</li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        )}

        {/* PHI Inventory */}
        {activeView === 'PHI Inventory' && (
          <motion.div key="phi" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            {repoModules.filter((m) => m.phiEntryPoints.some((p) => p.risk !== 'none') || m.phiStorage.length > 0).map((m) => (
              <div key={m.id} className="p-6 border border-white/10">
                <h3 className="font-bold font-mono text-sm mb-4">{m.name}/</h3>
                {m.phiEntryPoints.filter((p) => p.risk !== 'none').length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-xs text-red-400 uppercase tracking-wider mb-2">Entry Points</h4>
                    {m.phiEntryPoints.filter((p) => p.risk !== 'none').map((p) => (
                      <div key={p.location} className="text-sm text-white/50 mb-1">
                        <span className="text-red-400">⚠</span> <span className="font-mono text-xs text-white/60">{p.location}</span> — {p.detail}
                      </div>
                    ))}
                  </div>
                )}
                {m.phiStorage.length > 0 && (
                  <div>
                    <h4 className="text-xs text-amber-400 uppercase tracking-wider mb-2">Storage Locations</h4>
                    {m.phiStorage.map((s) => (
                      <div key={s.location} className="text-sm text-white/50 mb-1">
                        <span className="text-amber-400">●</span> {s.location} — {s.persistence} {s.encrypted ? '(encrypted)' : ''}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </motion.div>
        )}

        {/* Auth Boundaries */}
        {activeView === 'Auth Boundaries' && (
          <motion.div key="auth" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
            {repoModules.map((m) => (
              <div key={m.id} className="p-4 border border-white/10">
                <h3 className="font-bold font-mono text-sm mb-3 text-purple-400">{m.name}/</h3>
                <ul className="space-y-1">
                  {m.authBoundaries.map((ab) => (
                    <li key={ab} className="text-sm text-white/50">🔒 {ab}</li>
                  ))}
                </ul>
              </div>
            ))}
          </motion.div>
        )}

        {/* Navigation */}
        <div className="mt-12 flex flex-wrap gap-4">
          <Link to="/platform" className="px-6 py-3 border border-white/20 text-sm hover:bg-white/5 transition-colors">
            ← Platform Focus Areas
          </Link>
          <Link to="/security-posture" className="px-6 py-3 border border-white/20 text-sm hover:bg-white/5 transition-colors">
            Security Posture Map →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RepoAnalyzer;
