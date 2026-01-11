import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const ForResearchers = () => {
  return (
    <div className="bg-black text-white min-h-screen">
      {/* Hero */}
      <section className="py-32 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-sm text-blue-400 uppercase tracking-wider mb-4">For Researchers</p>
            <h1 className="text-4xl md:text-5xl font-bold mb-6">
              Multi-center oncology data
            </h1>
            <p className="text-lg text-white/40 max-w-2xl mb-8">
              Access de-identified patient data, create studies, apply for IRB, 
              and collaborate across institutions in weeks instead of months.
            </p>
            <div className="flex gap-4">
              <Link to="/register?type=researcher" className="px-8 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
                Apply for Access
              </Link>
              <Link to="/cohort-builder" className="px-8 py-3 border border-white/20 hover:bg-white/5 transition-colors">
                Try Cohort Builder
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Workflow */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-12">Research Workflow</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: '01', title: 'Define Study', desc: 'Protocol, criteria, endpoints' },
              { step: '02', title: 'IRB Approval', desc: 'Templates and guidance' },
              { step: '03', title: 'Build Cohort', desc: 'Visual query builder' },
              { step: '04', title: 'Analyze', desc: 'Export and publish' },
            ].map((item) => (
              <div key={item.step} className="p-6 border border-white/10">
                <span className="text-xs text-white/30 font-mono">{item.step}</span>
                <h3 className="font-medium mt-2 mb-2">{item.title}</h3>
                <p className="text-sm text-white/40">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Study Types */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12">
          <div>
            <h2 className="text-2xl font-bold mb-6">Supported research</h2>
            <p className="text-white/40">
              Retrospective studies, real-world evidence, comparative effectiveness, 
              epidemiology, biomarker discovery, and health economics.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              'Retrospective', 'Real-World Evidence', 'Comparative', 'Epidemiological',
              'Biomarker', 'Health Economics'
            ].map((item) => (
              <div key={item} className="p-4 border border-white/10 text-sm">
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* IRB */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">IRB Support</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { title: 'Protocol Templates', features: ['Chart review', 'RWE', 'Registry'] },
              { title: 'Fast-Track', features: ['Minimal risk', 'HIPAA Safe Harbor', 'Pre-negotiated DUAs'] },
              { title: 'Central sIRB', features: ['Single submission', 'All sites covered', 'Faster turnaround'] },
            ].map((item) => (
              <div key={item.title} className="p-6 border border-white/10">
                <h3 className="font-medium mb-4">{item.title}</h3>
                <ul className="space-y-2 text-sm text-white/40">
                  {item.features.map((f) => <li key={f}>→ {f}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Multi-Center */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12">
          <div>
            <h2 className="text-2xl font-bold mb-6">Multi-center studies</h2>
            <p className="text-white/40 mb-6">
              Partner with cancer centers to increase study power and validate findings.
            </p>
            <div className="space-y-4">
              {[
                { title: 'Federated Network', desc: 'Query without data leaving firewall' },
                { title: 'Harmonized Model', desc: 'Common data elements across sites' },
                { title: 'Collaboration', desc: 'Shared workspaces for teams' },
              ].map((item) => (
                <div key={item.title} className="border-l-2 border-blue-400/30 pl-4">
                  <div className="font-medium">{item.title}</div>
                  <div className="text-sm text-white/40">{item.desc}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="p-6 border border-white/10">
            <h3 className="font-medium mb-4">Partner Institutions</h3>
            <p className="text-sm text-white/40 mb-4">Building partnerships with leading centers</p>
            <div className="grid grid-cols-2 gap-3 mb-6">
              {['Academic', 'NCI-Designated', 'Community', 'International'].map((type) => (
                <div key={type} className="p-3 bg-white/5 text-center text-sm text-white/50">{type}</div>
              ))}
            </div>
            <a href="mailto:partnerships@healthdb.ai" className="text-blue-400 text-sm hover:underline">
              Become a partner →
            </a>
          </div>
        </div>
      </section>

      {/* Data */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">Available Data</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { cat: 'Demographics', items: ['Age', 'Sex', 'Race', 'Insurance'] },
              { cat: 'Diagnosis', items: ['Cancer type', 'ICD-10', 'Staging', 'Histology'] },
              { cat: 'Molecular', items: ['NGS', 'Mutations', 'Biomarkers'] },
              { cat: 'Treatment', items: ['Regimens', 'Lines', 'Dosing'] },
              { cat: 'Response', items: ['RECIST', 'MRD', 'Best response'] },
              { cat: 'Outcomes', items: ['PFS', 'OS', 'Survival'] },
            ].map((item) => (
              <div key={item.cat} className="p-4 border border-white/10">
                <h3 className="font-medium mb-3">{item.cat}</h3>
                <ul className="space-y-1 text-sm text-white/40">
                  {item.items.map((i) => <li key={i}>· {i}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">Access Tiers</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { tier: 'Explorer', price: 'Free', features: ['Aggregate stats', 'Cohort estimates', 'Data dictionary'], cta: 'Start Free' },
              { tier: 'Researcher', price: 'Custom', features: ['Patient-level data', 'IRB-approved', 'Export', 'API'], cta: 'Apply', featured: true },
              { tier: 'Enterprise', price: 'Custom', features: ['Unlimited', 'Dedicated support', 'Custom integrations'], cta: 'Contact' },
            ].map((item) => (
              <div key={item.tier} className={`p-6 border ${item.featured ? 'border-blue-400/30' : 'border-white/10'}`}>
                <h3 className="font-medium">{item.tier}</h3>
                <p className="text-2xl font-bold my-2">{item.price}</p>
                <ul className="space-y-2 text-sm text-white/40 mb-6">
                  {item.features.map((f) => <li key={f}>✓ {f}</li>)}
                </ul>
                <Link to="/register?type=researcher" className={`block text-center py-2 text-sm ${item.featured ? 'bg-white text-black' : 'bg-white/10'}`}>
                  {item.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Accelerate your research</h2>
          <p className="text-white/40 mb-8">From hypothesis to data in weeks</p>
          <div className="flex gap-4 justify-center">
            <Link to="/register?type=researcher" className="px-8 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
              Apply for Access
            </Link>
            <a href="mailto:research@healthdb.ai" className="px-8 py-3 border border-white/20 hover:bg-white/5 transition-colors">
              Contact Us
            </a>
          </div>
          <p className="text-white/30 text-sm mt-6">
            Already have access? <Link to="/login" className="text-blue-400 hover:underline">Sign in</Link>
          </p>
        </div>
      </section>
    </div>
  );
};

export default ForResearchers;
