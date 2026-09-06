import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const ForResearchers = () => (
  <div className="bg-black text-white min-h-screen">
    <section className="py-28 px-6">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="max-w-3xl"
        >
          <p className="text-xs text-blue-300 uppercase tracking-[0.2em] mb-5">For researchers · pilot evaluation</p>
          <h1 className="text-4xl md:text-6xl font-medium mb-7">Pressure-test the workflow before you request real data.</h1>
          <p className="text-lg text-white/50 max-w-2xl mb-9 leading-relaxed">
            Use synthetic oncology records to evaluate cohort logic, variable selection, study setup,
            governance states, and controlled extraction. HealthDB does not currently offer production datasets.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link to="/contact?interest=researcher" className="px-7 py-3.5 bg-white text-black text-center font-medium hover:bg-gray-100 transition-colors">
              Request researcher access
            </Link>
            <Link to="/platform" className="px-7 py-3.5 border border-white/20 text-center hover:bg-white/5 transition-colors">
              Review the roadmap
            </Link>
          </div>
        </motion.div>
      </div>
    </section>

    <section className="py-20 px-6 border-t border-white/5">
      <div className="max-w-5xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-5 mb-10">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-emerald-300 mb-3">Working prototype</p>
            <h2 className="text-3xl font-medium">What you can evaluate</h2>
          </div>
          <p className="text-sm text-white/40 max-w-md">These are software workflows, not validated research services or guarantees of data access.</p>
        </div>
        <div className="grid md:grid-cols-2 gap-5">
          {[
            ['Cohort feasibility', 'Define cancer-type criteria and test aggregate results with minimum-cell-size suppression.'],
            ['Variable planning', 'Review disease-specific field inventories and inspect completeness metadata on synthetic records.'],
            ['Study workspace', 'Create study records, organize collaborators, and walk through draft regulatory states.'],
            ['Controlled extraction', 'Evaluate approval gates and download behavior using non-production data.'],
          ].map(([title, description], index) => (
            <article key={title} className="p-6 border border-white/10">
              <span className="text-xs font-mono text-white/25">0{index + 1}</span>
              <h3 className="font-medium text-lg mt-5 mb-3">{title}</h3>
              <p className="text-sm text-white/45 leading-relaxed">{description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>

    <section className="py-20 px-6 border-t border-white/5">
      <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-blue-300 mb-3">Good pilot questions</p>
          <h2 className="text-3xl font-medium mb-6">Bring a real workflow problem</h2>
          <ul className="space-y-4 text-white/50 text-sm">
            <li>Can the cohort criteria represent the population you actually study?</li>
            <li>Are the required oncology variables defined precisely enough?</li>
            <li>Which approvals and attestations must block an extract?</li>
            <li>What provenance and quality information must accompany each field?</li>
          </ul>
        </div>
        <div className="border border-amber-400/20 p-6">
          <p className="text-xs uppercase tracking-[0.2em] text-amber-300 mb-4">Current limits</p>
          <ul className="space-y-4 text-sm text-white/50">
            <li>No real patient records or production datasets</li>
            <li>No central IRB or executed data-use agreements</li>
            <li>No institutional partner network</li>
            <li>No compliance certification or clinical use</li>
          </ul>
        </div>
      </div>
    </section>

    <section className="py-20 px-6 border-t border-white/5 text-center">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-3xl font-medium mb-4">Evaluate one study journey with us</h2>
        <p className="text-white/45 mb-8">Tell us the disease area, study question, and workflow you want to test. Do not include patient information.</p>
        <Link to="/contact?interest=researcher" className="inline-block px-8 py-3.5 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
          Request a guided pilot
        </Link>
        <p className="text-white/30 text-sm mt-6">Already invited? <Link to="/login" className="text-blue-300 hover:underline">Sign in</Link></p>
      </div>
    </section>
  </div>
);

export default ForResearchers;
