import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const LandingPage = () => {
  return (
    <div className="bg-black text-white">
      {/* Hero */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
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
              Revolutionize
              <br />
              <span className="text-white/50">Health Care Research</span>
            </h1>
            
            <p className="text-lg text-white/40 max-w-xl mx-auto mb-10">
              Multi-center data access in weeks. Pre-negotiated IRBs. Direct EMR integration.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
              <Link to="/researchers" className="px-8 py-4 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
                For Researchers
              </Link>
              <Link to="/patients" className="px-8 py-4 border border-white/20 hover:bg-white/5 transition-colors">
                For Patients
              </Link>
            </div>

            <div className="flex justify-center gap-16">
              {[
                { value: '12K+', label: 'Patients' },
                { value: '50+', label: 'Variables' },
                { value: '8', label: 'Sites' },
              ].map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <div className="text-xs text-white/30 uppercase tracking-wider">{stat.label}</div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Partners */}
      <section className="py-12 border-y border-white/5">
        <div className="max-w-4xl mx-auto px-6">
          <div className="flex flex-wrap justify-center items-center gap-12 opacity-40">
            <span className="text-lg font-medium">OHSU</span>
            <span className="text-lg font-medium">Fred Hutch</span>
            <span className="text-lg font-medium">Emory</span>
            <span className="text-lg font-medium">ASH</span>
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
                    <div className="text-white/40">ICD-10, treatments, outcomes</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-emerald-400">2</span>
                  <div>
                    <div className="text-white">Run feasibility</div>
                    <div className="text-white/40">Instant N counts</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-emerald-400">3</span>
                  <div>
                    <div className="text-white">Submit to sIRB</div>
                    <div className="text-white/40">Auto-generated protocol</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-emerald-400">4</span>
                  <div>
                    <div className="text-white">Get data</div>
                    <div className="text-white/40">3 weeks avg</div>
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
                    <div className="text-white/40">Epic MyChart or manual</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-blue-400">2</span>
                  <div>
                    <div className="text-white">Choose consent level</div>
                    <div className="text-white/40">Granular control</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-blue-400">3</span>
                  <div>
                    <div className="text-white">Contribute data</div>
                    <div className="text-white/40">Help future patients</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="text-blue-400">4</span>
                  <div>
                    <div className="text-white">Earn rewards</div>
                    <div className="text-white/40">Compensation for contributions</div>
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
            <h3 className="text-sm text-red-400/70 uppercase tracking-wider mb-4">The Problem</h3>
            <h2 className="text-2xl font-bold mb-6">Multi-center research is slow</h2>
            <ul className="space-y-3 text-white/50 text-sm">
              <li>6+ months for IRB approvals</li>
              <li>Manual DUAs with each site</li>
              <li>Data siloed in EMR systems</li>
              <li>No patient data ownership</li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm text-emerald-400/70 uppercase tracking-wider mb-4">Our Solution</h3>
            <h2 className="text-2xl font-bold mb-6">HealthDB removes friction</h2>
            <ul className="space-y-3 text-white/50 text-sm">
              <li>Central sIRB with pre-negotiated agreements</li>
              <li>Auto-generated DUAs with DocuSign</li>
              <li>Direct EMR integration via FHIR</li>
              <li>Patient-owned data with rewards</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Capabilities */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold mb-12">Platform</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { title: 'IRB Protocol Generator', desc: 'Auto-populate NIH templates' },
              { title: 'DUA Templates', desc: 'Pre-negotiated with major centers' },
              { title: 'EMR Integration', desc: 'Epic, Cerner via FHIR' },
              { title: 'Cohort Builder', desc: 'Visual query interface' },
              { title: 'Variable Selector', desc: '50+ OMOP CDM fields' },
              { title: 'De-identification', desc: 'HIPAA Safe Harbor' },
            ].map((item) => (
              <div key={item.title} className="p-6 border border-white/10">
                <h3 className="font-medium mb-2">{item.title}</h3>
                <p className="text-sm text-white/40">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Start your research</h2>
          <p className="text-white/40 mb-8">Get from hypothesis to data in weeks</p>
          <div className="flex gap-4 justify-center">
            <a href="https://calendly.com/healthdb/demo" className="px-8 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
              Schedule Demo
            </a>
            <Link to="/register" className="px-8 py-3 border border-white/20 hover:bg-white/5 transition-colors">
              Create Account
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            <div>
              <div className="font-medium mb-4">HealthDB</div>
              <p className="text-white/30 text-sm">Cancer research data infrastructure</p>
            </div>
            <div>
              <p className="text-xs text-white/30 uppercase tracking-wider mb-4">Platform</p>
              <ul className="space-y-2 text-sm">
                <li><Link to="/researchers" className="text-white/50 hover:text-white">Researchers</Link></li>
                <li><Link to="/patients" className="text-white/50 hover:text-white">Patients</Link></li>
                <li><Link to="/pricing" className="text-white/50 hover:text-white">Pricing</Link></li>
              </ul>
            </div>
            <div>
              <p className="text-xs text-white/30 uppercase tracking-wider mb-4">Company</p>
              <ul className="space-y-2 text-sm">
                <li><Link to="/about" className="text-white/50 hover:text-white">About</Link></li>
                <li><a href="mailto:contact@healthdb.ai" className="text-white/50 hover:text-white">Contact</a></li>
              </ul>
            </div>
            <div>
              <p className="text-xs text-white/30 uppercase tracking-wider mb-4">Legal</p>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="text-white/50 hover:text-white">Privacy</a></li>
                <li><a href="#" className="text-white/50 hover:text-white">Terms</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-white/5 flex justify-between text-xs text-white/30">
            <p>© 2024 HealthDB</p>
            <p>HIPAA Compliant · SOC 2</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
