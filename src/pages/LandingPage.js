import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const LandingPage = () => {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="bg-black text-white">
      {/* Hero Section - Full Screen */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 gradient-bg" />
        <div className="absolute inset-0 grid-pattern" />
        
        {/* Subtle glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#00d4aa]/5 rounded-full blur-[120px]" />

        {/* Content */}
        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, ease: [0.25, 0.1, 0.25, 1] }}
          >
            <h1 className="heading-display text-4xl md:text-6xl lg:text-7xl text-white mb-6 text-glow">
              The Cancer Research Database
              <br />
              <span className="text-white/60">That Solves Regulatory Friction</span>
            </h1>
            
            <p className="text-lg md:text-xl text-white/50 max-w-2xl mx-auto mb-8 font-light">
              Multi-center data access in weeks, not months. Pre-negotiated IRBs. 
              Auto-generated DUAs. Direct EMR integration.
            </p>

            {/* User Type CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Link 
                to="/researchers" 
                className="group px-8 py-4 bg-white text-black font-medium hover:bg-gray-100 transition-all flex items-center justify-center gap-3"
              >
                <span className="text-xl">🔬</span>
                <div className="text-left">
                  <div className="text-sm font-semibold">I'm a Researcher</div>
                  <div className="text-xs text-black/60">Access data for studies</div>
                </div>
              </Link>
              <Link 
                to="/patients" 
                className="group px-8 py-4 border border-white/20 text-white hover:bg-white/5 transition-all flex items-center justify-center gap-3"
              >
                <span className="text-xl">👤</span>
                <div className="text-left">
                  <div className="text-sm font-semibold">I'm a Patient</div>
                  <div className="text-xs text-white/60">Contribute my data</div>
                </div>
              </Link>
              <Link 
                to="/marketplace" 
                className="group px-8 py-4 border border-white/20 text-white hover:bg-white/5 transition-all flex items-center justify-center gap-3"
              >
                <span className="text-xl">🏥</span>
                <div className="text-left">
                  <div className="text-sm font-semibold">I'm an Institution</div>
                  <div className="text-xs text-white/60">Join the network</div>
                </div>
              </Link>
            </div>

            {/* Stats */}
            <div className="flex justify-center gap-12 md:gap-16">
              {[
                { value: '12,000+', label: 'Patients' },
                { value: '50+', label: 'Variables' },
                { value: '8', label: 'Institutions' },
                { value: '3', label: 'Publications' },
              ].map((stat, i) => (
                <motion.div 
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.5 + i * 0.1 }}
                  className="text-center"
                >
                  <div className="text-2xl md:text-3xl font-bold text-white">{stat.value}</div>
                  <div className="text-xs text-white/40 uppercase tracking-wider">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 scroll-indicator">
          <div className="w-6 h-10 border border-white/20 rounded-full flex justify-center pt-2">
            <div className="w-1 h-2 bg-white/40 rounded-full" />
          </div>
        </div>
      </section>

      {/* Trusted By */}
      <section className="py-12 border-y border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-center text-xs uppercase tracking-[0.3em] text-white/30 mb-8">
            Trusted By Leading Institutions
          </p>
          <div className="flex flex-wrap justify-center items-center gap-12 md:gap-16 opacity-50">
            <span className="text-xl font-semibold tracking-tight">OHSU Knight</span>
            <span className="text-xl font-semibold tracking-tight">Fred Hutch</span>
            <span className="text-xl font-semibold tracking-tight">Emory Winship</span>
            <span className="text-xl font-semibold tracking-tight">ASH</span>
          </div>
        </div>
      </section>

      {/* How It Works - Split by User Type */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              How It Works
            </p>
            <h2 className="heading-display text-4xl md:text-5xl text-white/90">
              Your path to faster research
            </h2>
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-12">
            {/* For Researchers */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="card-glass p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <span className="text-2xl">🔬</span>
                <h3 className="text-xl font-semibold">For Researchers</h3>
              </div>
              <div className="space-y-4">
                {[
                  { step: '1', title: 'Define Cohort', desc: 'Use visual query builder with ICD-10, treatments, outcomes' },
                  { step: '2', title: 'Run Feasibility', desc: 'Instant N counts across all institutions' },
                  { step: '3', title: 'Submit IRB', desc: 'Auto-generated protocol → central sIRB approval' },
                  { step: '4', title: 'Get Data', desc: 'Avg 3 weeks vs 6 months traditional' },
                ].map((item) => (
                  <div key={item.step} className="flex gap-4">
                    <span className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 text-xs flex items-center justify-center flex-shrink-0">
                      {item.step}
                    </span>
                    <div>
                      <div className="text-sm font-medium text-white">{item.title}</div>
                      <div className="text-xs text-white/50">{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
              <Link 
                to="/researchers" 
                className="inline-block mt-6 text-emerald-400 text-sm font-medium hover:text-emerald-300 transition-colors"
              >
                Learn more →
              </Link>
            </motion.div>

            {/* For Patients */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="card-glass p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <span className="text-2xl">👤</span>
                <h3 className="text-xl font-semibold">For Patients</h3>
              </div>
              <div className="space-y-4">
                {[
                  { step: '1', title: 'Connect Records', desc: 'Link Epic MyChart or upload manually' },
                  { step: '2', title: 'Choose Consent Level', desc: 'Granular control over what you share' },
                  { step: '3', title: 'Contribute to Research', desc: 'Your data helps future patients' },
                  { step: '4', title: 'Earn Rewards', desc: 'Compensation for your contributions' },
                ].map((item) => (
                  <div key={item.step} className="flex gap-4">
                    <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs flex items-center justify-center flex-shrink-0">
                      {item.step}
                    </span>
                    <div>
                      <div className="text-sm font-medium text-white">{item.title}</div>
                      <div className="text-xs text-white/50">{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
              <Link 
                to="/patients" 
                className="inline-block mt-6 text-blue-400 text-sm font-medium hover:text-blue-300 transition-colors"
              >
                Learn more →
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="divider" />

      {/* Key Problem/Solution */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
            >
              <p className="text-xs uppercase tracking-[0.3em] text-red-400/70 mb-4">
                The Problem
              </p>
              <h2 className="heading-display text-3xl md:text-4xl text-white/90 mb-6">
                Multi-center research takes too long
              </h2>
              <div className="space-y-4 text-white/50">
                <p>• <strong className="text-white/70">6+ months</strong> for IRB approvals across institutions</p>
                <p>• <strong className="text-white/70">Manual DUAs</strong> with each collaborating site</p>
                <p>• <strong className="text-white/70">Data silos</strong> in Epic, Cerner, proprietary systems</p>
                <p>• <strong className="text-white/70">No patient ownership</strong> of their own health data</p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              viewport={{ once: true }}
            >
              <p className="text-xs uppercase tracking-[0.3em] text-emerald-400/70 mb-4">
                Our Solution
              </p>
              <h2 className="heading-display text-3xl md:text-4xl text-white/90 mb-6">
                HealthDB removes the friction
              </h2>
              <div className="space-y-4 text-white/50">
                <p>• <strong className="text-emerald-400">Central sIRB</strong> with pre-negotiated reliance agreements</p>
                <p>• <strong className="text-emerald-400">Auto-generated DUAs</strong> with DocuSign integration</p>
                <p>• <strong className="text-emerald-400">Direct EMR integration</strong> via FHIR, Epic Cosmos, flat files</p>
                <p>• <strong className="text-emerald-400">Patient-owned data</strong> with tiered consent and rewards</p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="divider" />

      {/* Capabilities Grid */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Platform Capabilities
            </p>
            <h2 className="heading-display text-4xl md:text-5xl text-white/90">
              Everything you need
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: '📋',
                title: 'IRB Protocol Generator',
                description: 'Auto-populate NIH/OHRP templates with your study details. Submit to central sIRB.',
              },
              {
                icon: '📝',
                title: 'DUA Template Engine',
                description: 'Pre-negotiated templates for major centers. E-signature via DocuSign.',
              },
              {
                icon: '🔗',
                title: 'EMR Integration Hub',
                description: 'Connect Epic, Cerner, Meditech via FHIR, Cosmos, or secure file transfer.',
              },
              {
                icon: '🔍',
                title: 'Cohort Query Builder',
                description: 'Visual interface for ICD-10, treatments, labs, outcomes. Instant feasibility.',
              },
              {
                icon: '📊',
                title: 'Variable Selector',
                description: '50+ standardized OMOP CDM fields. Data completeness scoring.',
              },
              {
                icon: '🛡️',
                title: 'De-identification Pipeline',
                description: 'HIPAA Safe Harbor and Expert Determination. Tiered data access levels.',
              },
            ].map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card-glass p-6 card-hover"
              >
                <span className="text-2xl mb-4 block">{item.icon}</span>
                <h3 className="text-lg font-medium text-white mb-2">{item.title}</h3>
                <p className="text-sm text-white/50">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="divider" />

      {/* Data Categories */}
      <section className="py-24 px-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-[#00d4aa]/5 to-transparent" />
        
        <div className="max-w-6xl mx-auto relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="mb-12"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Available Data
            </p>
            <h2 className="heading-display text-4xl md:text-5xl text-white/90">
              Comprehensive clinical variables
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              { 
                category: 'Demographics', 
                items: ['Age at diagnosis', 'Sex', 'Race/ethnicity', 'Insurance type'] 
              },
              { 
                category: 'Labs & Biomarkers', 
                items: ['CBC w/ diff', 'CMP', 'LDH', 'Beta-2 microglobulin', 'Free light chains', 'Cytogenetics'] 
              },
              { 
                category: 'Treatments', 
                items: ['Regimen name', 'Start/stop dates', 'Dose/schedule', 'Cycles completed', 'Reason for d/c'] 
              },
              { 
                category: 'Outcomes', 
                items: ['Best response', 'PFS', 'OS', 'MRD status', 'CRS/ICANS grade', 'Toxicities'] 
              },
            ].map((group, index) => (
              <motion.div
                key={group.category}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <h3 className="text-sm font-semibold text-emerald-400 mb-4 uppercase tracking-wider">
                  {group.category}
                </h3>
                <ul className="space-y-2">
                  {group.items.map((item) => (
                    <li key={item} className="text-sm text-white/50 flex items-center gap-2">
                      <span className="w-1 h-1 bg-white/30 rounded-full" />
                      {item}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="divider" />

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="heading-display text-4xl md:text-5xl text-white/90 mb-6">
              Ready to accelerate your research?
            </h2>
            <p className="text-white/40 text-lg mb-8 max-w-xl mx-auto">
              Schedule a demo to see how HealthDB can reduce your time to data from months to weeks.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a 
                href="https://calendly.com/healthdb/demo" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn-primary"
              >
                Schedule Demo
              </a>
              <Link to="/register" className="btn-secondary">
                Create Free Account
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-16 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-4 gap-12 mb-16">
            <div>
              <div className="text-xl font-medium mb-4">HealthDB</div>
              <p className="text-white/40 text-sm">
                The cancer research database that solves regulatory friction.
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-white/30 mb-4">Platform</p>
              <ul className="space-y-3">
                <li><Link to="/marketplace" className="text-white/50 hover:text-white text-sm transition-colors">About</Link></li>
                <li><Link to="/researchers" className="text-white/50 hover:text-white text-sm transition-colors">For Researchers</Link></li>
                <li><Link to="/patients" className="text-white/50 hover:text-white text-sm transition-colors">For Patients</Link></li>
                <li><Link to="/pricing" className="text-white/50 hover:text-white text-sm transition-colors">Pricing</Link></li>
              </ul>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-white/30 mb-4">Company</p>
              <ul className="space-y-3">
                <li><Link to="/about" className="text-white/50 hover:text-white text-sm transition-colors">About Us</Link></li>
                <li><Link to="/resources" className="text-white/50 hover:text-white text-sm transition-colors">Resources</Link></li>
                <li><a href="mailto:contact@healthdb.ai" className="text-white/50 hover:text-white text-sm transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-white/30 mb-4">Legal</p>
              <ul className="space-y-3">
                <li><a href="#" className="text-white/50 hover:text-white text-sm transition-colors">Privacy</a></li>
                <li><a href="#" className="text-white/50 hover:text-white text-sm transition-colors">Terms</a></li>
                <li><a href="#" className="text-white/50 hover:text-white text-sm transition-colors">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-white/30 text-xs">
              © 2024 HealthDB. All rights reserved.
            </p>
            <p className="text-white/30 text-xs">
              HIPAA Compliant · SOC 2 Type II · HITRUST
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
