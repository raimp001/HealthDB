import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const LandingPage = () => {
  return (
    <div className="bg-black text-white">
      {/* Hero */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-40 pb-16 sm:pt-32">
        <div className="absolute inset-0 gradient-bg" />
        <div className="absolute inset-0 grid-pattern" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#00d4aa]/5 rounded-full blur-[120px]" />

        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
              Build consented
              <br />
              <span className="text-white/50">oncology research cohorts</span>
            </h1>
            
            <p className="text-lg text-white/60 max-w-xl mx-auto mb-10">
              Patients contribute their own records. HealthDB de-identifies them. Approved
              researchers run aggregate cohort feasibility.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
              <Link to="/researchers" className="px-8 py-4 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
                For Researchers
              </Link>
              <Link to="/patients" className="px-8 py-4 border border-white/20 hover:bg-white/5 transition-colors">
                For Patients
              </Link>
              <Link to="/institutions" className="px-8 py-4 border border-white/20 hover:bg-white/5 transition-colors">
                For Institutions
              </Link>
            </div>

            <div className="inline-flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 px-4 py-3 border border-amber-400/30 bg-amber-400/5 text-center sm:text-left">
              <span className="text-amber-400 text-xs uppercase tracking-wider whitespace-nowrap">
                Closed pilot
              </span>
              <span className="text-white/60 text-sm">
                Onboarding research partners — not yet open for self-service use
              </span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Standards the platform builds on. Not partners, not endorsements. */}
      <section className="py-12 border-y border-white/5">
        <div className="max-w-4xl mx-auto px-6">
          <p className="text-center text-xs text-white/50 uppercase tracking-wider mb-6">
            Built on open healthcare standards
          </p>
          <div className="flex flex-wrap justify-center items-center gap-12 text-white/60">
            <span className="text-lg font-medium">FHIR R4</span>
            <span className="text-lg font-medium">HL7v2</span>
            <span className="text-lg font-medium">OMOP CDM</span>
            <span className="text-lg font-medium">LOINC</span>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-16">How It Works</h2>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="p-8 border border-white/10">
              <h3 className="text-lg font-medium mb-6">Researchers</h3>
              <div className="space-y-4 text-sm">
                <div className="flex gap-4">
                  <span className="text-emerald-400">1</span>
                  <div>
                    <div className="text-white">Define cohort</div>
                    <div className="text-white/60">ICD-10, treatments, outcomes</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-emerald-400">2</span>
                  <div>
                    <div className="text-white">Run feasibility</div>
                    <div className="text-white/60">Instant N counts</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-emerald-400">3</span>
                  <div>
                    <div className="text-white">Prepare IRB protocol</div>
                    <div className="text-white/60">Draft generated from your cohort</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-emerald-400">4</span>
                  <div>
                    <div className="text-white">Receive dataset</div>
                    <div className="text-white/60">After approval</div>
                  </div>
                </div>
              </div>
              <Link to="/researchers" className="text-emerald-400 text-sm mt-6 inline-block hover:underline">
                Learn more →
              </Link>
            </div>

            <div className="p-8 border border-white/10">
              <h3 className="text-lg font-medium mb-6">Patients</h3>
              <div className="space-y-4 text-sm">
                <div className="flex gap-4">
                  <span className="text-blue-400">1</span>
                  <div>
                    <div className="text-white">Connect records</div>
                    <div className="text-white/60">Epic MyChart or manual</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-blue-400">2</span>
                  <div>
                    <div className="text-white">Choose consent level</div>
                    <div className="text-white/60">Granular control</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-blue-400">3</span>
                  <div>
                    <div className="text-white">Contribute data</div>
                    <div className="text-white/60">Help future patients</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-blue-400">4</span>
                  <div>
                    <div className="text-white">Track how it is used</div>
                    <div className="text-white/60">Full access log, revoke anytime</div>
                  </div>
                </div>
              </div>
              <Link to="/patients" className="text-blue-400 text-sm mt-6 inline-block hover:underline">
                Learn more →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Problem/Solution */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-16">
          <div>
            <h3 className="text-sm text-red-400 uppercase tracking-wider mb-4">The Problem</h3>
            <h2 className="text-2xl font-bold mb-6">Multi-center research is slow</h2>
            <ul className="space-y-3 text-white/50 text-sm">
              <li>6+ months for IRB approvals</li>
              <li>Manual DUAs with each site</li>
              <li>Data siloed in EMR systems</li>
              <li>No patient data ownership</li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm text-emerald-400 uppercase tracking-wider mb-4">Our Solution</h3>
            <h2 className="text-2xl font-bold mb-6">HealthDB removes friction</h2>
            <ul className="space-y-3 text-white/50 text-sm">
              <li>Patient-consented contribution, revocable at any time</li>
              <li>Identifier removal and year-only dates before data reaches researchers</li>
              <li>FHIR-based record import</li>
              <li>Aggregate cohort feasibility with small-cell suppression</li>
            </ul>
            <p className="text-xs text-white/50 mt-4">
              IRB reliance, executed DUAs and direct EMR integration are planned, not yet in place.
            </p>
          </div>
        </div>
      </section>

      {/* HealthDB Focus Areas */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold mb-4">Where HealthDB is heading</h2>
          <p className="text-white/60 mb-12">Six planned infrastructure modules. Most are not built yet — each page marks what exists today.</p>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: '⚡', title: 'FHIR/HL7 Ingestion', desc: 'FHIR R4, Bulk FHIR, HL7v2 ingestion with OMOP CDM normalization', color: 'text-emerald-400' },
              { icon: '🔐', title: 'Connector Auth Vault', desc: 'AWS KMS-backed credential storage with auto token refresh', color: 'text-blue-400' },
              { icon: '🛡️', title: 'PHI Boundary & De-ID', desc: 'Identifier removal, year-only dates, age capping. Tokenized re-linkage is planned.', color: 'text-amber-400' },
              { icon: '📋', title: 'Audit & Access Control', desc: 'Supabase RLS policies with immutable append-only audit logging', color: 'text-purple-400' },
              { icon: '📊', title: 'Dataset Builder & Export', desc: 'Visual cohort builder across 50+ OMOP CDM fields with CSV/Parquet export', color: 'text-cyan-400' },
              { icon: '🔬', title: 'Trial Matching Pipeline', desc: 'Match cohorts to ClinicalTrials.gov with NLP eligibility parsing', color: 'text-rose-400' },
            ].map((item) => (
              <div key={item.title} className="p-6 border border-white/10 card-hover">
                <div className={`text-2xl mb-3`}>{item.icon}</div>
                <h3 className={`font-medium mb-2 ${item.color}`}>{item.title}</h3>
                <p className="text-sm text-white/60">{item.desc}</p>
              </div>
            ))}
          </div>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link to="/platform" className="text-emerald-400 text-sm hover:underline">
              See the roadmap →
            </Link>
            <Link to="/security-posture" className="text-blue-400 text-sm hover:underline">
              Target security architecture →
            </Link>
            <Link to="/data-flow" className="text-amber-400 text-sm hover:underline">
              Target data flow →
            </Link>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Start your research</h2>
          <p className="text-white/60 mb-8">Get from hypothesis to data in weeks</p>
          <div className="flex gap-4 justify-center">
            <Link to="/contact" className="px-8 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
              Talk to Us
            </Link>
            <Link to="/register" className="px-8 py-3 border border-white/20 hover:bg-white/5 transition-colors">
              Create Account
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
};

export default LandingPage;
