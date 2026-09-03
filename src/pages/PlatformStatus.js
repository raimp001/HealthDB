import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { StatusRow } from '../components/StatusBadge';
import { FEATURES, STATUS, featuresByStatus } from '../data/featureStatus';

const GROUPS = [
  { prefix: 'ingest.', title: 'Data ingestion' },
  { prefix: 'privacy.', title: 'Privacy and de-identification' },
  { prefix: 'security.', title: 'Security' },
  { prefix: 'research.', title: 'Research workflow' },
  { prefix: 'governance.', title: 'Governance' },
  { prefix: 'patient.', title: 'Patient controls' },
];

/**
 * The manifest rendered in full. Every status badge elsewhere in the product
 * resolves through the same file, so this page and the rest of the site
 * cannot disagree.
 */
const PlatformStatus = () => {
  const counts = Object.fromEntries(
    Object.keys(STATUS).map((s) => [s, featuresByStatus(s).length])
  );

  return (
    <div className="bg-black text-white min-h-screen pt-24">
      <div className="max-w-4xl mx-auto px-6 py-16">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">Platform status</h1>
          <p className="text-white/60 max-w-2xl mb-8">
            What HealthDB does today, what runs only in the closed pilot, and what
            is not built. Every status badge elsewhere on this site reads from this
            same list.
          </p>
        </motion.div>

        <div className="grid grid-cols-3 gap-4 mb-12">
          {Object.entries(STATUS).map(([key, meta]) => (
            <div key={key} className="p-4 border border-white/10">
              <div className="text-2xl font-bold">{counts[key]}</div>
              <div className={`inline-block border px-2 py-0.5 text-xs uppercase tracking-wider mt-2 ${meta.className}`}>
                {meta.label}
              </div>
              <p className="text-xs text-white/50 mt-2">{meta.description}</p>
            </div>
          ))}
        </div>

        {GROUPS.map((group) => {
          const keys = Object.keys(FEATURES).filter((k) => k.startsWith(group.prefix));
          if (!keys.length) return null;
          return (
            <section key={group.prefix} className="mb-12">
              <h2 className="text-xl font-bold mb-4">{group.title}</h2>
              <div className="border border-white/10 px-5">
                {keys.map((key) => <StatusRow key={key} featureKey={key} />)}
              </div>
            </section>
          );
        })}

        <div className="p-6 border border-amber-400/30 bg-amber-400/5">
          <p className="text-amber-300 font-medium mb-2">No certifications held</p>
          <p className="text-white/60 text-sm">
            HealthDB has completed no third-party audit and holds no compliance
            certification. It has no executed business associate agreements, data
            use agreements or IRB reliance agreements, and does not accept real
            patient data. See{' '}
            <Link to="/institutions" className="underline hover:text-white">
              Security &amp; Compliance
            </Link>.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PlatformStatus;
