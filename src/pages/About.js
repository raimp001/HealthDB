import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const About = () => {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero */}
      <section className="py-32 px-6">
        <div className="max-w-3xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-sm text-emerald-400 uppercase tracking-wider mb-4">About</p>
            <h1 className="text-4xl md:text-5xl font-bold mb-6">
              Accelerating cancer research through better data
            </h1>
            <p className="text-lg text-white/60">
              Every patient's journey holds insights for future patients. 
              We build the infrastructure to unlock that potential—ethically and securely.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12">
          <div>
            <h2 className="text-2xl font-bold mb-6">Mission</h2>
            <p className="text-white/60 mb-4">
              Cancer research is held back by fragmented data and regulatory complexity. 
              A researcher with a promising hypothesis might wait 6+ months for data access.
            </p>
            <p className="text-white/60">
              We're building a different model: patients contribute voluntarily, 
              institutions share under agreements they control, researchers 
              move from idea to insight in weeks.
            </p>
          </div>
          <div className="p-6 border border-white/10">
            <div className="mb-6">
              <h3 className="text-sm text-red-400 uppercase tracking-wider mb-4">Problem</h3>
              <ul className="space-y-2 text-sm text-white/60">
                <li>6+ months for approvals</li>
                <li>Data siloed in EMRs</li>
                <li>No patient visibility</li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm text-emerald-400 uppercase tracking-wider mb-4">Solution</h3>
              <ul className="space-y-2 text-sm text-white/60">
                <li>Patient-consented contribution</li>
                <li>Safe Harbor de-identification</li>
                <li>Patient-visible access logs</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">Values</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { title: 'Patient-First', desc: 'Voluntary, transparent, compensated' },
              { title: 'Speed', desc: 'Weeks, not months' },
              { title: 'Privacy', desc: 'HIPAA, de-identification, audits' },
              { title: 'Collaborative', desc: 'Multi-center studies' },
            ].map((item) => (
              <div key={item.title} className="p-6 border border-white/10">
                <h3 className="font-medium mb-2">{item.title}</h3>
                <p className="text-sm text-white/60">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">Timeline</h2>
          <div className="space-y-4">
            {[
              { status: 'Built', event: 'Patient portal, consent management and access logging' },
              { status: 'Built', event: 'FHIR record import and Safe Harbor de-identification' },
              { status: 'Built', event: 'Cohort feasibility with small-cell suppression' },
              { status: 'Planned', event: 'Independent security assessment' },
              { status: 'Planned', event: 'IRB reliance and institutional agreements' },
              { status: 'Planned', event: 'First research partner site' },
            ].map((item, i) => (
              <div key={i} className="flex gap-6">
                <span className={`text-xs font-mono w-16 shrink-0 ${
                  item.status === 'Built' ? 'text-emerald-400' : 'text-amber-400'
                }`}>{item.status}</span>
                <span className="text-white/60">{item.event}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Partners section removed: HealthDB has no institutional partners to name. */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Partners</h2>
          <p className="text-white/60 mb-6">
            HealthDB is pre-partnership. We have no institutional agreements in place
            and name no partner sites.
          </p>
          <Link to="/contact" className="text-emerald-400 text-sm hover:underline">
            Talk to us about a pilot →
          </Link>
        </div>
      </section>

      {/* Team */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Team</h2>
          <p className="text-white/60 mb-8">
            Built by researchers, clinicians, and technologists who've experienced fragmented data firsthand.
          </p>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Join us</h2>
          <p className="text-white/60 mb-8">Patient, researcher, or institution—there's a place for you</p>
          <div className="flex gap-4 justify-center">
            <Link to="/register" className="px-8 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
              Get Started
            </Link>
            <a href="mailto:contact@healthdb.ai" className="px-8 py-3 border border-white/20 hover:bg-white/5 transition-colors">
              Contact
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default About;
