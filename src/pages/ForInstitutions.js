import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const ForInstitutions = () => {
  return (
    <div className="bg-black text-white min-h-screen">
      {/* Hero */}
      <section className="relative pt-32 pb-24 px-6">
        <div className="absolute inset-0 bg-gradient-to-b from-purple-500/5 to-transparent" />
        <div className="max-w-4xl mx-auto relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-purple-400 text-sm uppercase tracking-wider mb-4">For Institutions</p>
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Streamline Research
              <br />
              <span className="text-white/50">Compliance</span>
            </h1>
            <p className="text-lg text-white/40 max-w-xl mb-10">
              Centralized IRB management. Pre-negotiated DUAs. Automated reliance agreements. 
              Join the network that removes regulatory friction.
            </p>
            <div className="flex gap-4">
              <Link to="/register" className="px-6 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
                Join Network
              </Link>
              <a href="mailto:institutions@healthdb.ai" className="px-6 py-3 border border-white/20 hover:bg-white/5 transition-colors">
                Contact Us
              </a>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Key Benefits */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-12">Why Institutions Join</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                title: 'Single IRB',
                desc: 'Use our central sIRB for all multi-site studies. Eliminate duplicate reviews.',
                stat: '3 weeks',
                statLabel: 'avg approval'
              },
              {
                title: 'Pre-Negotiated DUAs',
                desc: 'Standard data use agreements ready to sign. Legal reviewed and HIPAA compliant.',
                stat: '24 hours',
                statLabel: 'to execute'
              },
              {
                title: 'Site Reliance',
                desc: 'Automatic reliance agreements with partner sites. No bilateral negotiations.',
                stat: '50+',
                statLabel: 'partner sites'
              }
            ].map((item, i) => (
              <div key={i} className="p-6 border border-white/10">
                <h3 className="font-medium text-lg mb-3">{item.title}</h3>
                <p className="text-white/40 text-sm mb-6">{item.desc}</p>
                <div className="pt-4 border-t border-white/5">
                  <div className="text-2xl font-bold">{item.stat}</div>
                  <div className="text-xs text-white/30 uppercase tracking-wider">{item.statLabel}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Regulatory Dashboard Preview */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-4">Regulatory Dashboard</h2>
          <p className="text-white/40 mb-12">Everything in one place</p>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="p-6 border border-white/10 bg-white/[0.02]">
              <h3 className="font-medium mb-4">IRB Status Tracker</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-2 border-b border-white/5">
                  <span className="text-white/60">Active Protocols</span>
                  <span>View all approved studies</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/5">
                  <span className="text-white/60">Pending Reviews</span>
                  <span>Track submission status</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/5">
                  <span className="text-white/60">Amendments</span>
                  <span>Manage protocol changes</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-white/60">Renewals</span>
                  <span>Auto-reminders for expiring</span>
                </div>
              </div>
            </div>

            <div className="p-6 border border-white/10 bg-white/[0.02]">
              <h3 className="font-medium mb-4">Agreement Management</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-2 border-b border-white/5">
                  <span className="text-white/60">DUAs</span>
                  <span>Data use agreements</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/5">
                  <span className="text-white/60">BAAs</span>
                  <span>Business associate agreements</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/5">
                  <span className="text-white/60">Reliance</span>
                  <span>Site reliance agreements</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-white/60">Contracts</span>
                  <span>Sub-contracts and SOWs</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* EMR Integration */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-2xl font-bold mb-4">EMR Integration</h2>
              <p className="text-white/40 mb-8">
                Connect your EHR system to enable patient-consented data extraction. 
                We support all major vendors with FHIR R4 and bulk data APIs.
              </p>
              <ul className="space-y-3 text-sm text-white/60">
                <li>Epic, Cerner, Meditech, athenahealth</li>
                <li>FHIR R4 and Bulk FHIR support</li>
                <li>SFTP for flat file transfers</li>
                <li>Real-time sync or scheduled batches</li>
              </ul>
            </div>
            <div className="p-6 border border-white/10">
              <div className="space-y-4">
                {['Epic', 'Cerner', 'Meditech', 'athenahealth'].map((emr, i) => (
                  <div key={emr} className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
                    <span className="font-medium">{emr}</span>
                    <span className="text-xs text-green-400 bg-green-400/10 px-2 py-1">Supported</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Compliance */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-12">Compliance & Security</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { title: 'HIPAA', desc: 'Full compliance with BAA' },
              { title: 'SOC 2', desc: 'Type II certified' },
              { title: 'GDPR', desc: 'Data protection ready' },
              { title: '21 CFR 11', desc: 'FDA electronic records' }
            ].map((item, i) => (
              <div key={i} className="text-center p-6 border border-white/10">
                <div className="text-lg font-bold mb-2">{item.title}</div>
                <div className="text-xs text-white/40">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Onboarding Process */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-12">Onboarding Process</h2>
          <div className="grid md:grid-cols-4 gap-4">
            {[
              { step: '1', title: 'Agreement', desc: 'Sign master BAA and DUA', time: 'Day 1' },
              { step: '2', title: 'Integration', desc: 'Connect EMR via FHIR', time: 'Week 1-2' },
              { step: '3', title: 'Validation', desc: 'Data quality checks', time: 'Week 2-3' },
              { step: '4', title: 'Live', desc: 'Start receiving studies', time: 'Week 4' }
            ].map((item, i) => (
              <div key={i} className="p-5 border border-white/10 relative">
                <div className="text-xs text-purple-400 mb-2">{item.time}</div>
                <h3 className="font-medium mb-2">{item.title}</h3>
                <p className="text-xs text-white/40">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Join the Network</h2>
          <p className="text-white/40 mb-8">
            Partner with 50+ academic medical centers and research institutions
          </p>
          <div className="flex gap-4 justify-center">
            <Link to="/register" className="px-8 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
              Get Started
            </Link>
            <a href="https://calendly.com/healthdb/institutions" className="px-8 py-3 border border-white/20 hover:bg-white/5 transition-colors">
              Schedule Call
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default ForInstitutions;
