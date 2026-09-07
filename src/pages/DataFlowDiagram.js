import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const currentFlow = [
  {
    step: '01',
    title: 'Invited test account',
    detail: 'An approved evaluator signs in. Public self-service registration is closed by default.',
  },
  {
    step: '02',
    title: 'Synthetic acknowledgement',
    detail: 'The evaluator reviews a clearly labeled prototype acknowledgement. It is not a real research consent.',
  },
  {
    step: '03',
    title: 'Synthetic FHIR input',
    detail: 'When an operator explicitly enables the feature, a fictional FHIR R4 Bundle can exercise the parser.',
  },
  {
    step: '04',
    title: 'Identifier-removal checks',
    detail: 'Supported fields are minimized and scanned for residual identifiers before test records are stored.',
  },
  {
    step: '05',
    title: 'Disclosure-risk measurement',
    detail: 'Each extract is measured for k-anonymity and l-diversity per subject. Release is blocked below the configured threshold. The measurement is recorded; it is not a de-identification determination.',
  },
  {
    step: '06',
    title: 'Authorized prototype query',
    detail: 'Role checks, active test consent, access logging, and small-cell suppression constrain cohort feasibility results.',
  },
];

const roadmap = [
  ['Source connections', 'SMART on FHIR, Bulk FHIR, HL7v2, claims, and lab feeds', 'Not built'],
  ['Normalization', 'Validated mappings to a production clinical data model', 'Not built'],
  ['PHI environment', 'Isolated, governed processing environment with verified retention controls', 'Not available'],
  ['Release governance', 'IRB/data-use approval, disclosure review, and controlled export', 'Not built'],
  ['Operational evidence', 'Independent security review, monitoring evidence, and incident procedures', 'Not validated'],
];

const DataFlowDiagram = () => (
  <div className="bg-black text-white min-h-screen pt-24">
    <div className="max-w-6xl mx-auto px-6 py-16">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <p className="text-sm text-emerald-400 uppercase tracking-wider mb-4">Data boundary</p>
        <h1 className="text-4xl md:text-5xl font-bold mb-5">Current synthetic-data flow</h1>
        <p className="text-white/50 max-w-3xl mb-10 leading-relaxed">
          This is the flow implemented in the pilot code. It is intentionally narrower than a production clinical-data pipeline and must not receive real patient information.
        </p>
      </motion.div>

      <div className="space-y-3 mb-16">
        {currentFlow.map((item, index) => (
          <motion.div
            key={item.step}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="grid md:grid-cols-[72px_240px_1fr] gap-4 items-start border border-white/10 p-5"
          >
            <span className="font-mono text-emerald-400">{item.step}</span>
            <h2 className="font-semibold">{item.title}</h2>
            <p className="text-white/45 text-sm leading-relaxed">{item.detail}</p>
          </motion.div>
        ))}
      </div>

      <section>
        <div className="flex items-end justify-between gap-4 mb-6">
          <div>
            <p className="text-xs text-amber-400 uppercase tracking-wider mb-2">Target architecture</p>
            <h2 className="text-2xl font-semibold">Required before real-world use</h2>
          </div>
          <span className="text-xs text-white/30">Planning, not evidence</span>
        </div>
        <div className="border border-white/10 overflow-x-auto">
          <div className="min-w-[720px]">
            {roadmap.map(([area, requirement, status]) => (
              <div key={area} className="grid grid-cols-[180px_1fr_130px] gap-5 p-4 border-b border-white/10 last:border-b-0 text-sm">
                <span className="text-white/75">{area}</span>
                <span className="text-white/40">{requirement}</span>
                <span className="text-amber-400">{status}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="mt-12 flex flex-wrap gap-3">
        <Link to="/platform" className="px-5 py-3 border border-white/20 text-sm hover:bg-white/5">Product status</Link>
        <Link to="/security-posture" className="px-5 py-3 border border-white/20 text-sm hover:bg-white/5">Security status</Link>
      </div>
    </div>
  </div>
);

export default DataFlowDiagram;
