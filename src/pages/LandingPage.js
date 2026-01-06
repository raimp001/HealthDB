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
            <h1 className="heading-display text-5xl md:text-7xl lg:text-8xl text-white mb-8 text-glow">
              Oncology Data
              <br />
              <span className="text-white/60">Infrastructure</span>
            </h1>
            
            <p className="text-lg md:text-xl text-white/50 max-w-2xl mx-auto mb-12 font-light">
              A secure platform for longitudinal cancer research data. 
              EMR integration. De-identification. Real-world evidence.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register" className="btn-primary">
                Get Started
              </Link>
              <Link to="/marketplace" className="btn-secondary">
                View Platform
              </Link>
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

      {/* Divider */}
      <div className="divider" />

      {/* Capabilities Section */}
      <section className="py-32 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="mb-20"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Capabilities
            </p>
            <h2 className="heading-display text-4xl md:text-5xl lg:text-6xl text-white/90">
              Building the infrastructure
              <br />
              <span className="text-white/40">for cancer research</span>
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-px bg-white/5">
            {[
              {
                number: '01',
                title: 'EMR Integration',
                description: 'Direct connections to Epic, Cerner, and other electronic medical record systems via FHIR APIs and secure database links.',
              },
              {
                number: '02',
                title: 'De-identification',
                description: 'HIPAA-compliant data anonymization with cryptographic hashing, ensuring patient privacy while preserving research utility.',
              },
              {
                number: '03',
                title: 'Longitudinal Tracking',
                description: 'Follow patient journeys across diagnosis, treatment lines, responses, and outcomes over extended time periods.',
              },
            ].map((item, index) => (
              <motion.div
                key={item.number}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card-glass card-hover p-10"
              >
                <span className="text-xs text-white/30 font-mono">{item.number}</span>
                <h3 className="text-xl font-medium text-white mt-4 mb-4">
                  {item.title}
                </h3>
                <p className="text-white/40 text-sm leading-relaxed">
                  {item.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="divider" />

      {/* How It Works */}
      <section className="py-32 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-20">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
            >
              <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
                Process
              </p>
              <h2 className="heading-display text-4xl md:text-5xl text-white/90 mb-6">
                How it works
              </h2>
              <p className="text-white/40 text-lg leading-relaxed">
                A systematic approach to aggregating and anonymizing oncology data 
                while maintaining the granularity needed for meaningful research.
              </p>
            </motion.div>

            <div className="space-y-8">
              {[
                {
                  step: '01',
                  title: 'Connect',
                  description: 'Healthcare institutions connect their EMR systems through secure, encrypted channels.',
                },
                {
                  step: '02',
                  title: 'Transform',
                  description: 'Patient data is de-identified and standardized into a common research-ready format.',
                },
                {
                  step: '03',
                  title: 'Analyze',
                  description: 'Researchers query aggregated datasets to build cohorts and conduct retrospective studies.',
                },
              ].map((item, index) => (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.15 }}
                  viewport={{ once: true }}
                  className="flex gap-6 group"
                >
                  <span className="text-3xl font-light text-white/20 group-hover:text-[#00d4aa]/50 transition-colors">
                    {item.step}
                  </span>
                  <div>
                    <h3 className="text-lg font-medium text-white mb-2">
                      {item.title}
                    </h3>
                    <p className="text-white/40 text-sm leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="divider" />

      {/* Data Types */}
      <section className="py-32 px-6 relative overflow-hidden">
        {/* Background accent */}
        <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-[#00d4aa]/5 to-transparent" />
        
        <div className="max-w-6xl mx-auto relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Data Categories
            </p>
            <h2 className="heading-display text-4xl md:text-5xl text-white/90">
              Comprehensive
              <br />
              <span className="text-white/40">clinical data</span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              'Demographics',
              'Diagnoses',
              'Pathology',
              'Cytogenetics',
              'Molecular Data',
              'Treatments',
              'Responses',
              'Outcomes',
            ].map((item, index) => (
              <motion.div
                key={item}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                viewport={{ once: true }}
                className="py-4 px-5 border border-white/10 hover:border-white/20 hover:bg-white/5 transition-all cursor-default"
              >
                <span className="text-sm text-white/70">{item}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="divider" />

      {/* CTA Section */}
      <section className="py-32 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="heading-display text-4xl md:text-5xl lg:text-6xl text-white/90 mb-6">
              Partner with us
            </h2>
            <p className="text-white/40 text-lg mb-12 max-w-xl mx-auto">
              We're working with healthcare institutions and researchers to build 
              the future of oncology data infrastructure.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a href="mailto:contact@healthdb.ai" className="btn-primary">
                Contact Us
              </a>
              <Link to="/register" className="btn-secondary">
                Create Account
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
                Oncology data infrastructure for the research community.
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-white/30 mb-4">Platform</p>
              <ul className="space-y-3">
                <li><Link to="/marketplace" className="text-white/50 hover:text-white text-sm transition-colors">Data Marketplace</Link></li>
                <li><Link to="/research" className="text-white/50 hover:text-white text-sm transition-colors">For Researchers</Link></li>
                <li><Link to="/patient" className="text-white/50 hover:text-white text-sm transition-colors">Patient Portal</Link></li>
              </ul>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-white/30 mb-4">Company</p>
              <ul className="space-y-3">
                <li><a href="#" className="text-white/50 hover:text-white text-sm transition-colors">About</a></li>
                <li><a href="#" className="text-white/50 hover:text-white text-sm transition-colors">Careers</a></li>
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
              HIPAA Compliant · SOC 2 Type II
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
