import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const Pricing = () => {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero */}
      <section className="py-32 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-sm text-emerald-400 uppercase tracking-wider mb-4">Pricing</p>
            <h1 className="text-4xl md:text-5xl font-bold mb-6">
              Simple, transparent
            </h1>
            <p className="text-lg text-white/40">
              Pay for what you need. Academic discounts available.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Tiers */}
      <section className="pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                name: 'Explorer',
                price: 'Free',
                desc: 'Feasibility assessment',
                features: ['Aggregate statistics', 'Cohort estimates', 'Data dictionary', 'Community support'],
                limitations: ['No patient-level data', 'No export'],
                cta: 'Get Started',
                link: '/register',
              },
              {
                name: 'Researcher',
                price: 'Custom',
                note: 'Based on scope',
                desc: 'IRB-approved studies',
                features: ['Patient-level de-identified', 'Cohort builder', 'IRB generator', 'DUA templates', 'sIRB submission', 'Export (CSV, REDCap)', 'Email support'],
                cta: 'Request Access',
                link: '/register',
                featured: true,
              },
              {
                name: 'Enterprise',
                price: 'Custom',
                note: 'Annual',
                desc: 'Pharma & research networks',
                features: ['Everything in Researcher', 'Unlimited queries', 'API access', 'Multi-site tools', 'Dedicated manager', 'Custom pipelines', 'SLA'],
                cta: 'Contact Sales',
                link: 'mailto:sales@healthdb.ai',
              },
            ].map((tier) => (
              <div key={tier.name} className={`p-6 border ${tier.featured ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-white/10'} relative`}>
                {tier.featured && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-emerald-500 text-black text-xs font-medium">
                    Popular
                  </span>
                )}
                <h3 className="font-medium text-lg">{tier.name}</h3>
                <div className="my-3">
                  <span className="text-2xl font-bold">{tier.price}</span>
                  {tier.note && <span className="text-sm text-white/40 ml-2">{tier.note}</span>}
                </div>
                <p className="text-sm text-white/40 mb-4">{tier.desc}</p>
                <ul className="space-y-2 mb-4">
                  {tier.features.map((f) => (
                    <li key={f} className="text-sm flex gap-2">
                      <span className="text-emerald-400">✓</span>
                      <span className="text-white/60">{f}</span>
                    </li>
                  ))}
                  {tier.limitations?.map((f) => (
                    <li key={f} className="text-sm flex gap-2">
                      <span className="text-white/20">×</span>
                      <span className="text-white/30">{f}</span>
                    </li>
                  ))}
                </ul>
                {tier.link.startsWith('mailto') ? (
                  <a href={tier.link} className={`block text-center py-2 text-sm transition-colors ${tier.featured ? 'bg-emerald-500 text-black hover:bg-emerald-400' : 'bg-white/10 hover:bg-white/20'}`}>
                    {tier.cta}
                  </a>
                ) : (
                  <Link to={tier.link} className={`block text-center py-2 text-sm transition-colors ${tier.featured ? 'bg-emerald-500 text-black hover:bg-emerald-400' : 'bg-white/10 hover:bg-white/20'}`}>
                    {tier.cta}
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Institutions */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold mb-4">For Institutions</h2>
            <p className="text-white/40 max-w-xl mx-auto">
              Partner to join our network. No upfront costs—contribute data and enable your researchers.
            </p>
          </div>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { title: 'Network Access', desc: 'Multi-center studies without DUA negotiations' },
              { title: 'Credits', desc: 'Data contribution earns research access' },
              { title: 'Collaboration', desc: 'Pre-negotiated reliance agreements' },
              { title: 'Compliance', desc: 'We handle IRB, DUA, HIPAA' },
            ].map((item) => (
              <div key={item.title} className="p-4 border border-white/10">
                <h3 className="font-medium mb-2">{item.title}</h3>
                <p className="text-sm text-white/40">{item.desc}</p>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
            <a href="mailto:partnerships@healthdb.ai" className="px-8 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors inline-block">
              Become a Partner
            </a>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">FAQ</h2>
          <div className="space-y-4">
            {[
              { q: 'Data access levels?', a: 'Aggregate stats, de-identified patient-level (Safe Harbor), and limited datasets with dates.' },
              { q: 'How long for IRB?', a: '2-3 weeks with central sIRB. Sites with reliance can be added in days.' },
              { q: 'Academic pricing?', a: 'Yes, significant discounts for academic and non-profit.' },
              { q: 'EMR support?', a: 'Epic (Cosmos, FHIR), Cerner, and secure file transfer.' },
              { q: 'Security?', a: 'SOC 2 Type II certified, regular audits, HIPAA compliant.' },
            ].map((item, i) => (
              <div key={i} className="p-4 border border-white/10">
                <h3 className="font-medium mb-2">{item.q}</h3>
                <p className="text-sm text-white/40">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Get started</h2>
          <p className="text-white/40 mb-8">Schedule a demo to see HealthDB in action</p>
          <div className="flex gap-4 justify-center">
            <a href="https://calendly.com/healthdb/demo" className="px-8 py-3 bg-emerald-500 text-black font-medium hover:bg-emerald-400 transition-colors">
              Schedule Demo
            </a>
            <a href="mailto:contact@healthdb.ai" className="px-8 py-3 border border-white/20 hover:bg-white/5 transition-colors">
              Contact
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Pricing;
