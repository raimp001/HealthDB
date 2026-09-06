import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const ForInstitutions = () => (
  <div className="bg-black text-white min-h-screen">
    <section className="relative py-28 px-6">
      <div className="absolute inset-0 bg-gradient-to-b from-purple-500/5 to-transparent" />
      <div className="max-w-5xl mx-auto relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="max-w-3xl"
        >
          <p className="text-xs text-purple-300 uppercase tracking-[0.2em] mb-5">For institutions · design partnership</p>
          <h1 className="text-4xl md:text-6xl font-medium mb-7">Define the governance bar before connecting a health system.</h1>
          <p className="text-lg text-white/50 max-w-2xl mb-9 leading-relaxed">
            HealthDB is seeking research, privacy, security, and informatics reviewers to evaluate
            a synthetic-data prototype. There are no production integrations or institutional agreements today.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link to="/contact?interest=institution" className="px-7 py-3.5 bg-white text-black text-center font-medium hover:bg-gray-100 transition-colors">
              Discuss a design pilot
            </Link>
            <Link to="/security-posture" className="px-7 py-3.5 border border-white/20 text-center hover:bg-white/5 transition-colors">
              Review security status
            </Link>
          </div>
        </motion.div>
      </div>
    </section>

    <section className="py-20 px-6 border-t border-white/5">
      <div className="max-w-5xl mx-auto">
        <p className="text-xs uppercase tracking-[0.2em] text-emerald-300 mb-3">Available to review</p>
        <h2 className="text-3xl font-medium mb-10">A prototype for structured feedback</h2>
        <div className="grid md:grid-cols-3 gap-5">
          {[
            ['Governance workflow', 'Study, site, agreement, regulatory, and extraction states can be evaluated with synthetic records.'],
            ['Access boundaries', 'Role checks and study-scoped access patterns provide a concrete starting point for review.'],
            ['Architecture targets', 'Public diagrams distinguish current controls from proposed infrastructure and integrations.'],
          ].map(([title, description]) => (
            <article key={title} className="p-6 border border-white/10">
              <h3 className="font-medium text-lg mb-3">{title}</h3>
              <p className="text-sm text-white/45 leading-relaxed">{description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>

    <section className="py-20 px-6 border-t border-white/5">
      <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-purple-300 mb-3">Questions for reviewers</p>
          <h2 className="text-3xl font-medium mb-6">Where would this fail your process?</h2>
          <ul className="space-y-4 text-sm text-white/50">
            <li>Which identity, authorization, and separation-of-duty controls are missing?</li>
            <li>What evidence must exist before a site, study, or export can be approved?</li>
            <li>How should consent changes propagate into queries and existing extracts?</li>
            <li>Which data-quality and provenance checks are mandatory at ingestion?</li>
          </ul>
        </div>
        <aside className="p-6 border border-amber-400/20">
          <p className="text-xs uppercase tracking-[0.2em] text-amber-300 mb-4">Not represented as complete</p>
          <ul className="space-y-4 text-sm text-white/50">
            <li>No BAA, DUA, reliance agreement, or central IRB</li>
            <li>No production EHR connector or live data pipeline</li>
            <li>No penetration test, SOC 2 audit, or compliance certification</li>
            <li>No named partner sites, network size, or implementation timeline</li>
          </ul>
        </aside>
      </div>
    </section>

    <section className="py-20 px-6 border-t border-white/5">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl font-medium mb-8">A practical first engagement</h2>
        <ol className="grid md:grid-cols-4 gap-px bg-white/10 border border-white/10">
          {[
            ['01', 'Choose one study workflow'],
            ['02', 'Use synthetic test records'],
            ['03', 'Run a governance review'],
            ['04', 'Agree on go/no-go evidence'],
          ].map(([step, label]) => (
            <li key={step} className="bg-black p-5 min-h-32">
              <span className="text-xs font-mono text-white/25">{step}</span>
              <p className="text-sm text-white/65 mt-7">{label}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>

    <section className="py-20 px-6 border-t border-white/5 text-center">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-3xl font-medium mb-4">Review the prototype with your real requirements</h2>
        <p className="text-white/45 mb-8">No integration or data transfer is required for an initial design review.</p>
        <Link to="/contact?interest=institution" className="inline-block px-8 py-3.5 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
          Start a design conversation
        </Link>
      </div>
    </section>
  </div>
);

export default ForInstitutions;
