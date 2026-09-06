import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const controls = [
  {
    control: 'Password storage',
    status: 'Implemented in code',
    evidence: 'PBKDF2-HMAC-SHA256 with 600,000 iterations; legacy hashes upgrade after login.',
    gap: 'No independent penetration test or identity-system assessment.',
  },
  {
    control: 'API authorization',
    status: 'Implemented in code',
    evidence: 'JWT authentication plus database-resolved role checks on protected endpoints.',
    gap: 'No MFA, enterprise SSO, or formal access-review process.',
  },
  {
    control: 'Pilot feature gates',
    status: 'Implemented in code',
    evidence: 'Registration and synthetic FHIR import are opt-in environment flags and default closed.',
    gap: 'Operators still need documented change control and environment verification.',
  },
  {
    control: 'Data minimization prototype',
    status: 'Implemented in code',
    evidence: 'Supported FHIR fields are minimized and scanned for a defined set of residual identifiers.',
    gap: 'Not independently validated; not approved for PHI or production de-identification.',
  },
  {
    control: 'Cohort safeguards',
    status: 'Implemented in code',
    evidence: 'Active acknowledgement checks, role checks, and configurable small-cell suppression.',
    gap: 'No governed dataset-release workflow or expert disclosure review.',
  },
  {
    control: 'Request logging',
    status: 'Partial',
    evidence: 'Security-relevant API paths emit application logs with status and duration.',
    gap: 'Logs are not proven immutable; retention, alerting, and incident response are not documented here.',
  },
  {
    control: 'Infrastructure controls',
    status: 'Not evidenced',
    evidence: 'TLS and platform protections may be supplied by the hosting environment.',
    gap: 'Encryption-at-rest, backups, WAF, key management, and disaster recovery have not been independently verified.',
  },
  {
    control: 'Compliance certification',
    status: 'Not available',
    evidence: 'HealthDB makes no current HIPAA, SOC 2, HITRUST, or regulatory certification claim.',
    gap: 'Policies, risk analysis, vendor agreements, audits, and operating evidence would be required.',
  },
];

const statusTone = (status) => {
  if (status === 'Implemented in code') return 'text-emerald-400 border-emerald-400/25 bg-emerald-400/5';
  if (status === 'Partial') return 'text-blue-400 border-blue-400/25 bg-blue-400/5';
  return 'text-amber-400 border-amber-400/25 bg-amber-400/5';
};

const SecurityPostureMap = () => (
  <div className="bg-black text-white min-h-screen pt-24">
    <div className="max-w-6xl mx-auto px-6 py-16">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <p className="text-sm text-emerald-400 uppercase tracking-wider mb-4">Trust center preview</p>
        <h1 className="text-4xl md:text-5xl font-bold mb-5">Security posture, without shortcuts</h1>
        <p className="text-white/50 max-w-3xl mb-5 leading-relaxed">
          This page distinguishes controls visible in the repository from operational controls that still need evidence. “Implemented in code” does not mean independently audited, compliant, or production-ready.
        </p>
        <div className="border border-amber-400/30 bg-amber-400/5 p-5 mb-12">
          <p className="text-amber-300 font-medium mb-1">Closed pilot boundary</p>
          <p className="text-white/45 text-sm">Use synthetic data only. Do not use HealthDB for clinical decisions, regulated research, or protected health information.</p>
        </div>
      </motion.div>

      <div className="space-y-3">
        {controls.map((item, index) => (
          <motion.article
            key={item.control}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.035 }}
            className="grid lg:grid-cols-[190px_170px_1fr_1fr] gap-4 border border-white/10 p-5"
          >
            <h2 className="font-medium">{item.control}</h2>
            <span className={`h-fit w-fit border px-2.5 py-1 text-xs ${statusTone(item.status)}`}>{item.status}</span>
            <div>
              <p className="text-xs uppercase tracking-wider text-white/25 mb-2">Repository evidence</p>
              <p className="text-white/55 text-sm leading-relaxed">{item.evidence}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-white/25 mb-2">Known gap</p>
              <p className="text-white/40 text-sm leading-relaxed">{item.gap}</p>
            </div>
          </motion.article>
        ))}
      </div>

      <div className="mt-14 grid md:grid-cols-2 gap-5">
        <div className="border border-white/10 p-6">
          <p className="text-xs text-emerald-400 uppercase tracking-wider mb-3">Next evidence milestone</p>
          <h2 className="text-xl font-semibold mb-3">Independent pilot security review</h2>
          <p className="text-white/40 text-sm leading-relaxed">Threat-model the synthetic workflow, test authorization boundaries, verify deployment configuration, and publish dated remediation results.</p>
        </div>
        <div className="border border-white/10 p-6">
          <p className="text-xs text-blue-400 uppercase tracking-wider mb-3">Next operational milestone</p>
          <h2 className="text-xl font-semibold mb-3">Document ownership and response</h2>
          <p className="text-white/40 text-sm leading-relaxed">Assign control owners, create incident and access-review procedures, define log retention, and test recovery before expanding the pilot.</p>
        </div>
      </div>

      <div className="mt-12 flex flex-wrap gap-3">
        <Link to="/data-flow" className="px-5 py-3 border border-white/20 text-sm hover:bg-white/5">Review data flow</Link>
        <Link to="/contact?interest=pilot" className="px-5 py-3 bg-white text-black text-sm font-medium hover:bg-gray-100">Discuss a pilot review</Link>
      </div>
    </div>
  </div>
);

export default SecurityPostureMap;
