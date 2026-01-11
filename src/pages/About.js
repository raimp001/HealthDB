import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const About = () => {
  const values = [
    {
      icon: '🤝',
      title: 'Patient-First',
      description: 'Patients own their data. Every contribution is voluntary, transparent, and compensated.',
    },
    {
      icon: '⚡',
      title: 'Speed Research',
      description: 'Reduce time from study concept to data access from months to weeks.',
    },
    {
      icon: '🔒',
      title: 'Privacy by Design',
      description: 'HIPAA compliance, de-identification, and audit trails are built into every layer.',
    },
    {
      icon: '🌐',
      title: 'Collaborative',
      description: 'Break down silos between institutions to enable large-scale multi-center studies.',
    },
  ];

  const milestones = [
    { year: '2024', event: 'Founded with mission to democratize cancer research data' },
    { year: '2024', event: 'First institutional partner (OHSU Knight Cancer Institute)' },
    { year: '2025', event: 'Launched patient contribution portal' },
    { year: '2025', event: 'Central sIRB approval for multi-site studies' },
    { year: '2025', event: 'First publication using HealthDB data' },
  ];

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-block px-3 py-1 text-xs font-medium tracking-wider text-emerald-400 border border-emerald-500/30 rounded-full mb-6">
              ABOUT US
            </span>
            <h1 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight">
              Accelerating cancer research through better data infrastructure
            </h1>
            <p className="text-xl text-neutral-400 leading-relaxed">
              We believe that every cancer patient's journey holds insights that could help future patients. 
              HealthDB builds the infrastructure to unlock that potential—ethically, securely, and at scale.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-24 px-6 border-t border-neutral-800">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <h2 className="text-3xl font-bold mb-6">Our Mission</h2>
              <p className="text-neutral-400 mb-4">
                Cancer research is held back by fragmented data, regulatory complexity, and lack of patient agency. 
                A researcher with a promising hypothesis might wait 6+ months just to access the data they need.
              </p>
              <p className="text-neutral-400 mb-4">
                We're building a different model: one where patients voluntarily contribute their health data, 
                institutions share securely through pre-negotiated agreements, and researchers can move from 
                idea to insight in weeks instead of months.
              </p>
              <p className="text-neutral-400">
                Our goal is to make every cancer patient's data count—while giving them full ownership 
                and transparency over how it's used.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-8"
            >
              <h3 className="text-lg font-semibold mb-6 text-emerald-400">The Problem We Solve</h3>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <span className="text-red-400">✕</span>
                  <div>
                    <div className="font-medium">6+ months for IRB/DUA approvals</div>
                    <div className="text-sm text-neutral-500">Researchers lose momentum waiting</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-red-400">✕</span>
                  <div>
                    <div className="font-medium">Data siloed in EMR systems</div>
                    <div className="text-sm text-neutral-500">Epic, Cerner, proprietary formats</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-red-400">✕</span>
                  <div>
                    <div className="font-medium">Patients have no visibility</div>
                    <div className="text-sm text-neutral-500">No ownership, no control, no benefit</div>
                  </div>
                </div>
              </div>
              <div className="my-6 border-t border-neutral-700" />
              <h3 className="text-lg font-semibold mb-6 text-emerald-400">How We Fix It</h3>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <span className="text-emerald-400">✓</span>
                  <div>
                    <div className="font-medium">Central sIRB + pre-negotiated DUAs</div>
                    <div className="text-sm text-neutral-500">Approval in weeks, not months</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-emerald-400">✓</span>
                  <div>
                    <div className="font-medium">Direct EMR integration</div>
                    <div className="text-sm text-neutral-500">FHIR, Cosmos, secure file transfer</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-emerald-400">✓</span>
                  <div>
                    <div className="font-medium">Patient-owned data with rewards</div>
                    <div className="text-sm text-neutral-500">Full transparency and compensation</div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-24 px-6 border-t border-neutral-800">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Our Values</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((value, index) => (
              <motion.div
                key={value.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="p-6 bg-neutral-900/50 border border-neutral-800 rounded-lg"
              >
                <span className="text-3xl mb-4 block">{value.icon}</span>
                <h3 className="text-lg font-semibold mb-2">{value.title}</h3>
                <p className="text-sm text-neutral-400">{value.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="py-24 px-6 border-t border-neutral-800">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Our Journey</h2>
          <div className="space-y-6">
            {milestones.map((milestone, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="flex gap-6"
              >
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 bg-emerald-500/10 border border-emerald-500/30 rounded-full flex items-center justify-center text-sm font-mono text-emerald-400">
                    {milestone.year}
                  </div>
                  {index < milestones.length - 1 && (
                    <div className="w-px h-full bg-neutral-800 my-2" />
                  )}
                </div>
                <div className="flex-1 pb-8">
                  <p className="text-neutral-300">{milestone.event}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Partners */}
      <section className="py-24 px-6 border-t border-neutral-800 bg-neutral-900/30">
        <div className="max-w-6xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Our Partners</h2>
          <p className="text-neutral-400 mb-12 max-w-2xl mx-auto">
            We're proud to work with leading cancer centers and research institutions.
          </p>
          <div className="flex flex-wrap justify-center items-center gap-12 md:gap-16 opacity-60">
            <span className="text-2xl font-semibold tracking-tight">OHSU Knight</span>
            <span className="text-2xl font-semibold tracking-tight">Fred Hutch</span>
            <span className="text-2xl font-semibold tracking-tight">Emory Winship</span>
            <span className="text-2xl font-semibold tracking-tight">ASH</span>
          </div>
        </div>
      </section>

      {/* Team Placeholder */}
      <section className="py-24 px-6 border-t border-neutral-800">
        <div className="max-w-6xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Our Team</h2>
          <p className="text-neutral-400 mb-12 max-w-2xl mx-auto">
            Built by researchers, clinicians, and technologists who've experienced the pain of fragmented data firsthand.
          </p>
          <div className="grid md:grid-cols-3 gap-8 max-w-3xl mx-auto">
            {[
              { role: 'CEO & Co-Founder', desc: 'Former oncology researcher' },
              { role: 'CTO & Co-Founder', desc: 'Health tech veteran' },
              { role: 'Chief Medical Officer', desc: 'Practicing oncologist' },
            ].map((member, index) => (
              <motion.div
                key={member.role}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="p-6"
              >
                <div className="w-20 h-20 bg-neutral-800 rounded-full mx-auto mb-4" />
                <h3 className="font-semibold">{member.role}</h3>
                <p className="text-sm text-neutral-500">{member.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-neutral-800">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Join us in accelerating cancer research</h2>
          <p className="text-neutral-400 mb-8">
            Whether you're a patient, researcher, or institution—there's a place for you in our mission.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register"
              className="px-8 py-4 bg-emerald-500 text-black font-medium hover:bg-emerald-400 transition-colors"
            >
              Get Started
            </Link>
            <a
              href="mailto:contact@healthdb.ai"
              className="px-8 py-4 border border-white/20 text-white hover:bg-white/5 transition-colors"
            >
              Contact Us
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default About;
