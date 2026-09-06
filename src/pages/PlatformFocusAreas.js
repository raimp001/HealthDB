import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const capabilities = [
  {
    status: 'Implemented in code',
    tone: 'emerald',
    title: 'Synthetic FHIR bundle parsing',
    detail: 'The API parses a limited set of FHIR R4 resources and runs identifier-removal checks before structured test records are stored.',
    boundary: 'Disabled by default in deployed environments. Not validated for real patient data.',
  },
  {
    status: 'Implemented in code',
    tone: 'emerald',
    title: 'Consent-gated prototype workflows',
    detail: 'Invited test users can exercise acknowledgement, access-log, and cohort-feasibility paths against controlled data.',
    boundary: 'The screens are product simulations, not IRB-approved consent or research enrollment.',
  },
  {
    status: 'Implemented in code',
    tone: 'emerald',
    title: 'Role and aggregate safeguards',
    detail: 'API authorization resolves roles from the database and aggregate cohort results apply a configurable small-cell threshold.',
    boundary: 'These controls have automated tests but no independent security assessment.',
  },
  {
    status: 'Pilot validation',
    tone: 'blue',
    title: 'Research workflow usability',
    detail: 'The study, cohort, and institution screens are ready for structured evaluation with domain experts.',
    boundary: 'No production datasets, exports, or institution integrations are available.',
  },
  {
    status: 'Not built',
    tone: 'amber',
    title: 'Production clinical integrations',
    detail: 'SMART on FHIR, Bulk FHIR, HL7v2, claims feeds, and EHR-specific connectors remain roadmap items.',
    boundary: 'The current product does not connect to Epic, Oracle Health, or another EHR.',
  },
  {
    status: 'Not built',
    tone: 'amber',
    title: 'Governed data release',
    detail: 'OMOP normalization, approved dataset export, re-identification risk review, and signed delivery links remain roadmap items.',
    boundary: 'HealthDB does not currently sell or release research datasets.',
  },
];

const toneClasses = {
  emerald: 'border-emerald-400/25 bg-emerald-400/5 text-emerald-400',
  blue: 'border-blue-400/25 bg-blue-400/5 text-blue-400',
  amber: 'border-amber-400/25 bg-amber-400/5 text-amber-400',
};

const PlatformFocusAreas = () => (
  <div className="bg-black text-white min-h-screen pt-24">
    <div className="max-w-6xl mx-auto px-6 py-16">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <p className="text-sm text-emerald-400 uppercase tracking-wider mb-4">Product status</p>
        <h1 className="text-4xl md:text-5xl font-bold mb-5">What HealthDB can—and cannot—do</h1>
        <p className="text-white/50 max-w-3xl mb-6 leading-relaxed">
          HealthDB is a closed technical pilot for testing oncology research workflows with synthetic data. Status labels below describe the codebase, not a compliance certification or production-readiness claim.
        </p>
        <div className="inline-flex border border-amber-400/30 bg-amber-400/5 px-4 py-3 text-sm text-amber-200 mb-12">
          No clinical use · no real patient records · no production dataset access
        </div>
      </motion.div>

      <div className="grid md:grid-cols-2 gap-5">
        {capabilities.map((item, index) => (
          <motion.article
            key={item.title}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04 }}
            className="border border-white/10 p-6"
          >
            <span className={`inline-block border px-2.5 py-1 text-xs uppercase tracking-wider mb-5 ${toneClasses[item.tone]}`}>
              {item.status}
            </span>
            <h2 className="text-xl font-semibold mb-3">{item.title}</h2>
            <p className="text-white/55 text-sm leading-relaxed mb-4">{item.detail}</p>
            <p className="text-white/30 text-xs leading-relaxed border-t border-white/10 pt-4">
              Boundary: {item.boundary}
            </p>
          </motion.article>
        ))}
      </div>

      <div className="mt-14 border border-white/10 p-8 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Help validate the next milestone</h2>
          <p className="text-white/40 text-sm">We are looking for feedback on workflow fit, governance requirements, and evidence needed for a responsible pilot.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link to="/security-posture" className="px-5 py-3 border border-white/20 text-sm hover:bg-white/5">Review security status</Link>
          <Link to="/contact?interest=pilot" className="px-5 py-3 bg-white text-black text-sm font-medium hover:bg-gray-100">Request pilot review</Link>
        </div>
      </div>
    </div>
  </div>
);

export default PlatformFocusAreas;
