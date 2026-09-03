import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import TargetArchitectureBanner from '../components/TargetArchitectureBanner';

const pipelineStages = [
  {
    id: 'connector',
    name: 'Connector',
    color: 'text-red-400',
    border: 'border-red-400/20',
    bg: 'bg-red-400/5',
    phiPresent: true,
    phiDetail: 'Raw PHI received from source systems — MRN, names, DOB, SSN.',
    description: 'Authenticate and pull data from EHR systems and external feeds.',
    dataSources: ['Epic FHIR R4', 'Cerner FHIR R4', 'HL7v2 ADT/ORU feeds', 'Claims 837/835 files', 'Lab ORU messages'],
    technicalDetail: 'SMART-on-FHIR OAuth 2.0 + Bulk FHIR $export. HL7v2 via MLLP TCP listener. Credentials stored in AWS KMS-backed vault.',
    authBoundary: 'Token vault scoped per connector. No cross-connector credential access.',
  },
  {
    id: 'ingestion',
    name: 'Ingestion',
    color: 'text-orange-400',
    border: 'border-orange-400/20',
    bg: 'bg-orange-400/5',
    phiPresent: true,
    phiDetail: 'PHI in transit — resources validated and queued for normalization.',
    description: 'Validate, parse, and queue incoming clinical data resources.',
    dataSources: ['FHIR Bundle entries', 'HL7v2 parsed segments', 'CSV/flat file uploads'],
    technicalDetail: 'Schema validation (FHIR StructureDefinition). Error quarantine queue with retry. Deduplication via resource ID + lastUpdated.',
    authBoundary: 'Service role only. No user-facing access to raw ingestion queue.',
  },
  {
    id: 'normalize',
    name: 'Normalize',
    color: 'text-amber-400',
    border: 'border-amber-400/20',
    bg: 'bg-amber-400/5',
    phiPresent: true,
    phiDetail: 'Last stage with PHI — data mapped to OMOP CDM before de-identification.',
    description: 'Map source vocabularies to OMOP CDM v5.4 standard concepts.',
    dataSources: ['OMOP vocabulary tables', 'ICD-10 → SNOMED mappings', 'RxNorm drug concepts', 'LOINC lab codes'],
    technicalDetail: 'Concept mapping via OMOP vocabulary. Unmapped terms queued for manual review. Source-to-standard concept lineage tracked.',
    authBoundary: 'Internal service. Normalization workers run in isolated containers.',
  },
  {
    id: 'store',
    name: 'Store',
    color: 'text-emerald-400',
    border: 'border-emerald-400/20',
    bg: 'bg-emerald-400/5',
    phiPresent: false,
    phiDetail: 'De-identified data only. PHI boundary enforced before write.',
    description: 'Persist de-identified, normalized data in Supabase PostgreSQL with RLS.',
    dataSources: ['OMOP CDM tables (person, condition, drug, procedure, measurement, observation, visit)'],
    technicalDetail: 'Supabase PostgreSQL with Row-Level Security. AES-256 encryption at rest. PgBouncer connection pooling. Partitioned by site_id.',
    authBoundary: 'RLS policies enforce study-scoped access. No direct table access for users.',
  },
  {
    id: 'query',
    name: 'Query',
    color: 'text-cyan-400',
    border: 'border-cyan-400/20',
    bg: 'bg-cyan-400/5',
    phiPresent: false,
    phiDetail: 'Queries run against de-identified data. Results filtered by RLS.',
    description: 'Cohort builder and feasibility queries against de-identified OMOP tables.',
    dataSources: ['Cohort definition (JSON)', 'Variable selection config', 'Feasibility count cache'],
    technicalDetail: 'Parameterized SQL via Supabase client. Real-time N counts. Query versioning for reproducibility. Study-scoped result caching.',
    authBoundary: 'JWT claim study_id used by RLS. Researchers see only their approved cohorts.',
  },
  {
    id: 'export',
    name: 'Export',
    color: 'text-blue-400',
    border: 'border-blue-400/20',
    bg: 'bg-blue-400/5',
    phiPresent: false,
    phiDetail: 'Final re-identification risk check before release.',
    description: 'Generate de-identified dataset exports with data dictionaries.',
    dataSources: ['Query result sets', 'Data dictionary templates', 'Export format configs (CSV, Parquet, REDCap)'],
    technicalDetail: 'k-anonymity verification (k >= 5). Signed download URLs (24h TTL). Export logged to immutable audit store. Auto-generated data dictionary.',
    authBoundary: 'Export requires study approval + researcher identity match. One-time download links.',
  },
];

const dataSourceTypes = [
  { name: 'Epic EHR', type: 'EHR', protocol: 'FHIR R4 / Bulk FHIR', dataTypes: 'Patient, Encounter, Condition, MedicationRequest, Observation', phiAtEntry: true },
  { name: 'Cerner EHR', type: 'EHR', protocol: 'FHIR R4', dataTypes: 'Patient, Encounter, Condition, Procedure, DiagnosticReport', phiAtEntry: true },
  { name: 'HL7v2 Lab Feed', type: 'Labs', protocol: 'HL7v2 ORU', dataTypes: 'OBX segments (lab results with LOINC codes)', phiAtEntry: true },
  { name: 'Claims (837)', type: 'Claims', protocol: 'X12 837/835', dataTypes: 'Professional/institutional claims, diagnosis, procedure codes', phiAtEntry: true },
  { name: 'Tumor Registry', type: 'Registry', protocol: 'CSV/API', dataTypes: 'Cancer staging, histology, treatment summaries', phiAtEntry: true },
  { name: 'ClinicalTrials.gov', type: 'Public', protocol: 'REST API', dataTypes: 'Trial eligibility, status, endpoints', phiAtEntry: false },
  { name: 'OMOP Vocabularies', type: 'Reference', protocol: 'Athena download', dataTypes: 'Concept mappings (ICD-10, SNOMED, RxNorm, LOINC)', phiAtEntry: false },
  { name: 'Patient Portal Upload', type: 'Patient', protocol: 'HTTPS upload', dataTypes: 'Patient-reported outcomes, uploaded documents', phiAtEntry: true },
  { name: 'Genomic Data', type: 'Labs', protocol: 'VCF/FHIR Genomics', dataTypes: 'Variant calls, gene panels, pharmacogenomics', phiAtEntry: true },
];

const views = ['Pipeline Overview', 'Data Sources', 'PHI Tracking'];

const DataFlowDiagram = () => {
  const [activeView, setActiveView] = useState(views[0]);

  return (
    <div className="bg-black text-white min-h-screen pt-24">
      <div className="max-w-6xl mx-auto px-6 py-16">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">Target Data Flow</h1>
          <p className="text-white/60 max-w-2xl mb-12">
            Connector → Ingestion → Normalize → Store → Query → Export — with PHI boundaries and authorization at every stage.
          </p>
        </motion.div>
        <TargetArchitectureBanner
          implemented={["FHIR R4 bundle ingest (api/fhir_ingest.py)", "Safe Harbor de-identification", "Small-cell suppression on aggregates", "Consent-gated cohort queries"]}
          planned={["OMOP CDM normalization", "Bulk FHIR $export and HL7v2 MLLP", "k-anonymity verification", "Tokenized re-linkage vault"]}
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

        {/* Pipeline Overview */}
        {activeView === 'Pipeline Overview' && (
          <motion.div key="pipeline" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
            {/* Visual pipeline */}
            <div className="overflow-x-auto mb-8">
              <div className="flex items-center gap-0 text-xs min-w-[800px]">
                {pipelineStages.map((stage, i) => (
                  <React.Fragment key={stage.id}>
                    <div className={`flex-1 p-3 border text-center ${stage.border} ${stage.bg}`}>
                      <div className={`font-bold ${stage.color}`}>{stage.name}</div>
                      <div className="text-white/50 mt-1">{stage.phiPresent ? 'PHI ⚠' : 'De-ID ✓'}</div>
                    </div>
                    {i < pipelineStages.length - 1 && (
                      <div className={`px-1 text-lg ${i === 2 ? 'text-amber-400' : 'text-white/20'}`}>
                        {i === 2 ? '🛡️' : '→'}
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
              <div className="mt-2 text-center text-xs text-amber-400">
                ▲ PHI Boundary between Normalize and Store
              </div>
            </div>

            {/* Stage details */}
            {pipelineStages.map((stage) => (
              <div key={stage.id} className={`p-6 border ${stage.border}`}>
                <div className="flex items-center justify-between mb-3">
                  <h3 className={`text-lg font-bold ${stage.color}`}>{stage.name}</h3>
                  <span className={`text-xs px-3 py-1 border ${stage.phiPresent ? 'border-red-400/30 text-red-400' : 'border-emerald-400/30 text-emerald-400'}`}>
                    {stage.phiPresent ? 'PHI PRESENT' : 'DE-IDENTIFIED'}
                  </span>
                </div>
                <p className="text-sm text-white/50 mb-4">{stage.description}</p>
                <div className="grid md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <h4 className="text-xs text-white/50 uppercase mb-2">Data In/Out</h4>
                    <ul className="space-y-1">
                      {stage.dataSources.map((d) => (
                        <li key={d} className="text-white/50">• {d}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-xs text-white/50 uppercase mb-2">Technical</h4>
                    <p className="text-white/50">{stage.technicalDetail}</p>
                  </div>
                  <div>
                    <h4 className="text-xs text-white/50 uppercase mb-2">Auth Boundary</h4>
                    <p className="text-white/50">{stage.authBoundary}</p>
                  </div>
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {/* Data Sources */}
        {activeView === 'Data Sources' && (
          <motion.div key="sources" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="border border-white/10">
              <div className="grid grid-cols-5 gap-4 p-4 border-b border-white/10 text-xs text-white/50 uppercase tracking-wider">
                <span>Source</span>
                <span>Type</span>
                <span>Protocol</span>
                <span>Data Types</span>
                <span>PHI at Entry</span>
              </div>
              {dataSourceTypes.map((src) => (
                <div key={src.name} className="grid grid-cols-5 gap-4 p-4 border-b border-white/5 text-sm">
                  <span className="text-white/80 font-medium">{src.name}</span>
                  <span className="text-cyan-400 text-xs">{src.type}</span>
                  <span className="text-white/50 font-mono text-xs">{src.protocol}</span>
                  <span className="text-white/60 text-xs">{src.dataTypes}</span>
                  <span className={`text-xs ${src.phiAtEntry ? 'text-red-400' : 'text-emerald-400'}`}>
                    {src.phiAtEntry ? '⚠ Yes' : '✓ No'}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* PHI Tracking */}
        {activeView === 'PHI Tracking' && (
          <motion.div key="phi" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <p className="text-white/60 text-sm">
              Tracks PHI presence at each pipeline stage. The PHI boundary between Normalize and Store is enforced by the de-identification engine.
            </p>
            {pipelineStages.map((stage, i) => (
              <React.Fragment key={stage.id}>
                <div className={`p-4 border ${stage.border} flex items-center justify-between`}>
                  <div>
                    <span className={`font-bold ${stage.color}`}>{stage.name}</span>
                    <p className="text-xs text-white/60 mt-1">{stage.phiDetail}</p>
                  </div>
                  <span className={`text-xs px-3 py-1 border ${stage.phiPresent ? 'border-red-400/30 text-red-400' : 'border-emerald-400/30 text-emerald-400'}`}>
                    {stage.phiPresent ? 'PHI ⚠' : 'CLEAN ✓'}
                  </span>
                </div>
                {i === 2 && (
                  <div className="text-center py-4">
                    <div className="inline-block px-6 py-3 border-2 border-amber-400/40 bg-amber-400/10">
                      <div className="text-amber-400 font-bold text-sm">🛡️ PHI BOUNDARY</div>
                      <div className="text-xs text-white/60 mt-1">HIPAA Safe Harbor de-identification — 18 identifiers removed</div>
                    </div>
                  </div>
                )}
                {i < pipelineStages.length - 1 && i !== 2 && (
                  <div className="text-center text-white/20 text-sm">↓ Authorization check</div>
                )}
              </React.Fragment>
            ))}
          </motion.div>
        )}

        {/* Navigation */}
        <div className="mt-12 flex flex-wrap gap-4">
          <Link to="/security-posture" className="px-6 py-3 border border-white/20 text-sm hover:bg-white/5 transition-colors">
            ← Security Posture Map
          </Link>
          <Link to="/platform" className="px-6 py-3 border border-white/20 text-sm hover:bg-white/5 transition-colors">
            Platform Focus Areas →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DataFlowDiagram;
