import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import TargetArchitectureBanner from '../components/TargetArchitectureBanner';

const focusAreas = [
  {
    id: 'fhir-ingestion',
    title: 'FHIR/HL7 Ingestion & Normalization',
    icon: '⚡',
    color: 'text-emerald-400',
    borderColor: 'border-emerald-400/20',
    description: 'Ingest clinical data from EHR systems via FHIR R4, Bulk FHIR, and HL7v2 interfaces. Normalize to OMOP CDM for cross-site analysis.',
    dataSources: ['EHR (Epic, Cerner)', 'FHIR R4 / Bulk FHIR', 'HL7v2 ADT/ORU', 'Claims (837/835)', 'Lab Results (LOINC)'],
    capabilities: [
      'SMART-on-FHIR OAuth 2.0 registration',
      'Bulk FHIR $export with _since tracking',
      'HL7v2 MLLP listener with ACK/NAK',
      'OMOP CDM v5.4 vocabulary mapping',
      'Incremental sync with deduplication',
      'Error quarantine and retry queues',
    ],
    metrics: { throughput: '10K resources/min', latency: '<200ms per resource', uptime: '99.9%' },
  },
  {
    id: 'connector-vault',
    title: 'Connector Auth & Token Vault',
    icon: '🔐',
    color: 'text-blue-400',
    borderColor: 'border-blue-400/20',
    description: 'Securely manage OAuth tokens, client credentials, and API keys for every connected EHR system. Automatic refresh with zero downtime.',
    dataSources: ['SMART-on-FHIR tokens', 'Service account credentials', 'API keys (site-specific)', 'X.509 certificates'],
    capabilities: [
      'AWS KMS envelope encryption at rest',
      'Automatic OAuth 2.0 token refresh',
      'Credential rotation without downtime',
      'Per-connector scoped access policies',
      'Audit trail for every credential access',
      'HSM-backed key storage option',
    ],
    metrics: { secrets: '200+ managed', rotation: 'Auto every 90d', incidents: '0 breaches' },
  },
  {
    id: 'phi-boundary',
    title: 'PHI Boundary & De-identification',
    icon: '🛡️',
    color: 'text-amber-400',
    borderColor: 'border-amber-400/20',
    description: 'Enforce strict PHI boundaries between ingestion and research data stores. HIPAA Safe Harbor removal of all 18 identifiers.',
    dataSources: ['Raw EHR extracts (PHI present)', 'Patient demographics', 'Clinical notes (NLP)', 'Genomic identifiers'],
    capabilities: [
      'HIPAA Safe Harbor — 18 identifier removal',
      'Tokenized re-linkage for longitudinal studies',
      'PHI detection in unstructured text (NLP)',
      'Date shifting (±180 day random offset)',
      'Geographic generalization (3-digit ZIP)',
      'Expert determination mode (k-anonymity)',
    ],
    metrics: { identifiers: '18/18 covered', falseNeg: '<0.1%', reLink: 'Token-based' },
  },
  {
    id: 'audit-rls',
    title: 'Audit Logging & Access Control (RLS)',
    icon: '📋',
    color: 'text-purple-400',
    borderColor: 'border-purple-400/20',
    description: 'Row-Level Security via Supabase ensures researchers see only approved cohorts. Every data access is immutably logged.',
    dataSources: ['Supabase auth JWT claims', 'Study approval records', 'IRB protocol metadata', 'Role assignments'],
    capabilities: [
      'Supabase RLS policies per table',
      'JWT claim-based row filtering',
      'Immutable append-only audit log',
      'Real-time access anomaly alerts',
      'Study-scoped data partitioning',
      'Service role isolation (no RLS bypass)',
    ],
    metrics: { policies: '25+ RLS rules', logRetention: '7 years', alertLatency: '<30s' },
  },
  {
    id: 'dataset-builder',
    title: 'Research Dataset Builder & Export',
    icon: '📊',
    color: 'text-cyan-400',
    borderColor: 'border-cyan-400/20',
    description: 'Visual cohort builder with variable selection across 50+ OMOP CDM fields. Export de-identified datasets in standard formats.',
    dataSources: ['OMOP CDM tables', 'Condition/Drug/Procedure', 'Measurement/Observation', 'Visit occurrence'],
    capabilities: [
      'Visual drag-and-drop cohort builder',
      'ICD-10, SNOMED, RxNorm code search',
      'Real-time feasibility N counts',
      'CSV, Parquet, REDCap export formats',
      'Automated data dictionary generation',
      'Reproducible query versioning',
    ],
    metrics: { variables: '50+ fields', formats: '4 export types', avgExport: '< 3 weeks' },
  },
  {
    id: 'trial-matching',
    title: 'Clinical Trial Matching Pipeline',
    icon: '🔬',
    color: 'text-rose-400',
    borderColor: 'border-rose-400/20',
    description: 'Match patient cohorts to active clinical trials using structured eligibility criteria from ClinicalTrials.gov.',
    dataSources: ['ClinicalTrials.gov API', 'Patient cohort profiles', 'Site capability data', 'Drug/device registries'],
    capabilities: [
      'NLP parsing of eligibility criteria',
      'Structured matching against OMOP cohorts',
      'Site feasibility scoring',
      'Patient notification (opt-in only)',
      'Regulatory compliance tracking',
      'Multi-arm trial support',
    ],
    metrics: { trials: '1,200+ indexed', matchRate: '85% precision', sites: '8 active' },
  },
];

const PlatformFocusAreas = () => {
  const [activeTab, setActiveTab] = useState(focusAreas[0].id);
  const active = focusAreas.find((f) => f.id === activeTab);

  return (
    <div className="bg-black text-white min-h-screen pt-24">
      <div className="max-w-6xl mx-auto px-6 py-16">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">Platform Roadmap</h1>
          <p className="text-white/60 max-w-2xl mb-12">
            HealthDB's core infrastructure modules — from EHR ingestion through de-identified research export.
          </p>
        </motion.div>
        <TargetArchitectureBanner
          implemented={["FHIR R4 ingest", "Safe Harbor de-identification", "Consent management and access logs", "Cohort feasibility with small-cell suppression"]}
          planned={["Connector token vault (AWS KMS)", "OMOP CDM normalization", "Clinical trial matching pipeline", "Bulk FHIR and HL7v2 connectors"]}
        />

        {/* Tab Navigation */}
        <div className="flex flex-wrap gap-2 mb-12">
          {focusAreas.map((area) => (
            <button
              key={area.id}
              onClick={() => setActiveTab(area.id)}
              className={`px-4 py-2 text-sm border transition-colors ${
                activeTab === area.id
                  ? 'bg-white/10 border-white/20 text-white'
                  : 'border-white/5 text-white/60 hover:text-white/70 hover:border-white/10'
              }`}
            >
              <span className="mr-2">{area.icon}</span>
              {area.title}
            </button>
          ))}
        </div>

        {/* Active Area Detail */}
        {active && (
          <motion.div key={active.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }} className="space-y-8">
            <div className={`p-8 border ${active.borderColor}`}>
              <h2 className={`text-2xl font-bold mb-3 ${active.color}`}>
                {active.icon} {active.title}
              </h2>
              <p className="text-white/50 mb-6">{active.description}</p>

              <div className="grid md:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-sm text-white/50 uppercase tracking-wider mb-3">Capabilities</h3>
                  <ul className="space-y-2">
                    {active.capabilities.map((cap) => (
                      <li key={cap} className="text-sm text-white/60 flex items-start gap-2">
                        <span className={active.color}>→</span> {cap}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm text-white/50 uppercase tracking-wider mb-3">Data Sources</h3>
                  <ul className="space-y-2 mb-6">
                    {active.dataSources.map((ds) => (
                      <li key={ds} className="text-sm text-white/60 flex items-start gap-2">
                        <span className="text-white/20">●</span> {ds}
                      </li>
                    ))}
                  </ul>

                  <h3 className="text-sm text-white/50 uppercase tracking-wider mb-3">Design targets (not measured)</h3>
                  <div className="space-y-2">
                    {Object.entries(active.metrics).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-sm">
                        <span className="text-white/60">{k}</span>
                        <span className="text-white/80 font-medium">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Architecture Summary */}
        <div className="mt-16 p-8 border border-white/10">
          <h2 className="text-xl font-bold mb-6">HealthDB Pipeline Architecture</h2>
          <div className="overflow-x-auto">
            <div className="flex items-center gap-0 text-xs min-w-[700px]">
              {['Connector', 'Ingestion', 'Normalize', 'Store', 'Query', 'Export'].map((stage, i) => (
                <React.Fragment key={stage}>
                  <div className={`flex-1 p-4 border text-center ${i < 3 ? 'border-red-400/20 bg-red-400/5' : 'border-emerald-400/20 bg-emerald-400/5'}`}>
                    <div className="font-medium text-white mb-1">{stage}</div>
                    <div className="text-white/50">{i < 3 ? 'PHI Present' : 'De-identified'}</div>
                  </div>
                  {i < 5 && (
                    <div className={`px-2 ${i === 2 ? 'text-amber-400 font-bold' : 'text-white/20'}`}>
                      {i === 2 ? '🛡️→' : '→'}
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
            <div className="mt-2 text-center text-xs text-amber-400/60">
              ▲ PHI Boundary — HIPAA Safe Harbor de-identification applied between Normalize and Store
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="mt-12 flex flex-wrap gap-4">
          <Link to="/security-posture" className="px-6 py-3 border border-white/20 text-sm hover:bg-white/5 transition-colors">
            Security Posture Map →
          </Link>
          <Link to="/data-flow" className="px-6 py-3 border border-white/20 text-sm hover:bg-white/5 transition-colors">
            Data Flow Diagram →
          </Link>
          <Link to="/repo-analyzer" className="px-6 py-3 border border-white/20 text-sm hover:bg-white/5 transition-colors">
            Repo Analyzer →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default PlatformFocusAreas;
