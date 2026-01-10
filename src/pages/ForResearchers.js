import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const ForResearchers = () => {
  return (
    <div className="bg-black text-white min-h-screen">
      {/* Hero Section */}
      <section className="relative min-h-[80vh] flex items-center overflow-hidden pt-20">
        <div className="absolute inset-0 gradient-bg" />
        <div className="absolute inset-0 grid-pattern" />
        
        {/* Accent glow */}
        <div className="absolute top-1/3 left-0 w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-[150px]" />

        <div className="relative z-10 max-w-6xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
          >
            <p className="text-xs uppercase tracking-[0.3em] text-blue-400 mb-4">
              For Researchers
            </p>
            <h1 className="heading-display text-4xl md:text-5xl lg:text-6xl text-white mb-6">
              Large-scale
              <br />
              <span className="text-white/60">oncology research</span>
            </h1>
            <p className="text-lg text-white/50 mb-8 leading-relaxed">
              Access de-identified patient data, create studies, apply for IRB approval, 
              and collaborate with institutions for multi-center research.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/register?type=researcher" className="btn-primary">
                Apply for Access
              </Link>
              <a href="#capabilities" className="btn-secondary">
                View Capabilities
              </a>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="hidden lg:block"
          >
            <div className="card-glass p-8">
              <h3 className="text-white font-medium mb-6">Platform Capabilities</h3>
              <div className="space-y-4">
                {[
                  { icon: '🔬', label: 'Cohort Builder', desc: 'Build patient cohorts with precise criteria' },
                  { icon: '📋', label: 'IRB Management', desc: 'Streamlined ethics approval workflow' },
                  { icon: '🏥', label: 'Multi-Center Studies', desc: 'Collaborate across institutions' },
                  { icon: '📊', label: 'Real-World Evidence', desc: 'Longitudinal outcomes data' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-4 p-3 bg-white/5">
                    <span className="text-2xl">{item.icon}</span>
                    <div>
                      <p className="text-white font-medium">{item.label}</p>
                      <p className="text-white/40 text-sm">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Research Workflow */}
      <section id="capabilities" className="py-24 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Research Workflow
            </p>
            <h2 className="heading-display text-3xl md:text-4xl text-white/90">
              From hypothesis to publication
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-px bg-white/5">
            {[
              {
                step: '01',
                title: 'Define Study',
                description: 'Create your research protocol with study objectives, inclusion/exclusion criteria, and endpoints.',
                icon: '📝',
              },
              {
                step: '02',
                title: 'IRB Approval',
                description: 'Submit your protocol for institutional review board approval. We provide templates and guidance.',
                icon: '✅',
              },
              {
                step: '03',
                title: 'Build Cohort',
                description: 'Use our cohort builder to identify eligible patients based on diagnosis, treatment, and outcomes.',
                icon: '👥',
              },
              {
                step: '04',
                title: 'Analyze & Publish',
                description: 'Access de-identified data, run analyses, and generate insights for your research publications.',
                icon: '📈',
              },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card-glass p-8"
              >
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-2xl">{item.icon}</span>
                  <span className="text-xs font-mono text-white/30">{item.step}</span>
                </div>
                <h3 className="text-lg font-medium text-white mb-3">{item.title}</h3>
                <p className="text-white/40 text-sm leading-relaxed">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Study Types */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-20">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
                Supported Research
              </p>
              <h2 className="heading-display text-3xl md:text-4xl text-white/90 mb-6">
                Study types we enable
              </h2>
              <p className="text-white/40 text-lg leading-relaxed">
                Our platform supports a wide range of oncology research methodologies, 
                from retrospective observational studies to prospective real-world evidence generation.
              </p>
            </motion.div>

            <div className="grid grid-cols-2 gap-4">
              {[
                { title: 'Retrospective Studies', desc: 'Historical patient data analysis' },
                { title: 'Real-World Evidence', desc: 'Outcomes in clinical practice' },
                { title: 'Comparative Effectiveness', desc: 'Treatment comparisons' },
                { title: 'Epidemiological', desc: 'Disease patterns and trends' },
                { title: 'Biomarker Discovery', desc: 'Molecular correlations' },
                { title: 'Health Economics', desc: 'Cost-effectiveness analysis' },
              ].map((item, index) => (
                <motion.div
                  key={item.title}
                  initial={{ opacity: 0, scale: 0.95 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.4, delay: index * 0.05 }}
                  viewport={{ once: true }}
                  className="card-glass p-5"
                >
                  <h3 className="text-white font-medium mb-1 text-sm">{item.title}</h3>
                  <p className="text-white/40 text-xs">{item.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* IRB & Compliance */}
      <section className="py-24 px-6 border-t border-white/5 bg-gradient-to-b from-transparent to-blue-500/5">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Compliance & Ethics
            </p>
            <h2 className="heading-display text-3xl md:text-4xl text-white/90">
              IRB & regulatory support
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: '📋',
                title: 'Protocol Templates',
                description: 'Pre-approved protocol templates for common study types to accelerate your IRB submission.',
                features: ['Retrospective chart review', 'Real-world evidence', 'Registry studies'],
              },
              {
                icon: '⚡',
                title: 'Fast-Track Approval',
                description: 'Our standardized data use agreements and de-identification methods qualify for expedited review.',
                features: ['Minimal risk designation', 'HIPAA Safe Harbor', 'Pre-negotiated DUAs'],
              },
              {
                icon: '🏛️',
                title: 'Central IRB',
                description: 'For multi-center studies, use our central IRB partnership for streamlined approval.',
                features: ['Single submission', 'All institutions covered', 'Faster turnaround'],
              },
            ].map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card-glass p-8"
              >
                <span className="text-3xl mb-4 block">{item.icon}</span>
                <h3 className="text-lg font-medium text-white mb-3">{item.title}</h3>
                <p className="text-white/40 text-sm mb-4">{item.description}</p>
                <ul className="space-y-2">
                  {item.features.map((f) => (
                    <li key={f} className="text-white/50 text-xs flex items-center gap-2">
                      <span className="text-blue-400">→</span> {f}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Multi-Center Collaboration */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <p className="text-xs uppercase tracking-[0.3em] text-blue-400 mb-4">
                Institutional Collaboration
              </p>
              <h2 className="heading-display text-3xl md:text-4xl text-white/90 mb-6">
                Multi-center studies made simple
              </h2>
              <p className="text-white/40 text-lg leading-relaxed mb-8">
                Partner with multiple cancer centers to increase your study power, 
                validate findings across diverse populations, and accelerate enrollment.
              </p>

              <div className="space-y-6">
                {[
                  {
                    title: 'Federated Data Network',
                    description: 'Query across institutions without data leaving their firewall. Results are aggregated centrally.',
                  },
                  {
                    title: 'Harmonized Data Model',
                    description: 'Common data elements across all sites ensure consistent, comparable results.',
                  },
                  {
                    title: 'Collaborative Workspaces',
                    description: 'Shared environments for multi-site research teams to analyze and discuss findings.',
                  },
                ].map((item) => (
                  <div key={item.title} className="border-l-2 border-blue-400/30 pl-4">
                    <h3 className="text-white font-medium mb-1">{item.title}</h3>
                    <p className="text-white/40 text-sm">{item.description}</p>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
              className="card-glass p-8"
            >
              <h3 className="text-white font-medium mb-6">Partner Institutions</h3>
              <p className="text-white/40 text-sm mb-6">
                We're building partnerships with leading cancer centers. Interested in joining?
              </p>
              <div className="grid grid-cols-2 gap-4 mb-8">
                {[
                  'Academic Medical Centers',
                  'NCI-Designated Centers',
                  'Community Oncology',
                  'International Sites',
                ].map((type) => (
                  <div key={type} className="p-3 bg-white/5 text-center">
                    <p className="text-white/60 text-sm">{type}</p>
                  </div>
                ))}
              </div>
              <a href="mailto:partnerships@healthdb.ai" className="btn-secondary w-full text-center block">
                Become a Partner Institution
              </a>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Data Categories */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="mb-12"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Available Data
            </p>
            <h2 className="heading-display text-3xl md:text-4xl text-white/90">
              Comprehensive oncology data
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { category: 'Demographics', items: ['Age range', 'Sex', 'Race/Ethnicity', 'Insurance type'] },
              { category: 'Diagnosis', items: ['Cancer type', 'ICD-10 codes', 'Staging', 'Histology'] },
              { category: 'Molecular', items: ['NGS results', 'Mutations', 'Biomarkers', 'Gene expression'] },
              { category: 'Treatment', items: ['Regimens', 'Lines of therapy', 'Dosing', 'Modifications'] },
              { category: 'Response', items: ['RECIST/Lugano', 'MRD status', 'Best response', 'Duration'] },
              { category: 'Outcomes', items: ['PFS/OS', 'Relapse', 'Survival status', 'Follow-up'] },
            ].map((item, index) => (
              <motion.div
                key={item.category}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                viewport={{ once: true }}
                className="card-glass p-6"
              >
                <h3 className="text-white font-medium mb-4">{item.category}</h3>
                <ul className="space-y-2">
                  {item.items.map((i) => (
                    <li key={i} className="text-white/40 text-sm flex items-center gap-2">
                      <span className="w-1 h-1 rounded-full bg-blue-400"></span> {i}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Access Tiers
            </p>
            <h2 className="heading-display text-3xl md:text-4xl text-white/90">
              Flexible data access options
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                tier: 'Explorer',
                price: 'Free',
                description: 'For feasibility and hypothesis generation',
                features: ['Aggregate statistics only', 'Cohort size estimates', 'Data dictionary access', 'No patient-level data'],
                cta: 'Start Free',
              },
              {
                tier: 'Researcher',
                price: 'Custom',
                description: 'For academic and non-profit research',
                features: ['Patient-level de-identified data', 'IRB-approved studies', 'Export capabilities', 'API access'],
                cta: 'Apply for Access',
                featured: true,
              },
              {
                tier: 'Enterprise',
                price: 'Custom',
                description: 'For pharma and large-scale studies',
                features: ['Unlimited queries', 'Dedicated support', 'Custom integrations', 'Multi-site collaboration'],
                cta: 'Contact Sales',
              },
            ].map((item, index) => (
              <motion.div
                key={item.tier}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                viewport={{ once: true }}
                className={`card-glass p-8 ${item.featured ? 'border border-blue-400/30' : ''}`}
              >
                <div className="mb-6">
                  <h3 className="text-white font-medium text-lg mb-1">{item.tier}</h3>
                  <p className="text-2xl font-light text-white">{item.price}</p>
                  <p className="text-white/40 text-sm mt-2">{item.description}</p>
                </div>
                <ul className="space-y-3 mb-8">
                  {item.features.map((f) => (
                    <li key={f} className="text-white/50 text-sm flex items-center gap-2">
                      <span className="text-blue-400">✓</span> {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to="/register?type=researcher"
                  className={item.featured ? 'btn-primary w-full text-center block' : 'btn-secondary w-full text-center block'}
                >
                  {item.cta}
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="heading-display text-3xl md:text-4xl lg:text-5xl text-white/90 mb-6">
              Ready to accelerate your research?
            </h2>
            <p className="text-white/40 text-lg mb-10 max-w-xl mx-auto">
              Join researchers from leading institutions who are using HealthDB 
              to power their oncology studies.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register?type=researcher" className="btn-primary text-lg px-10 py-4">
                Apply for Researcher Access
              </Link>
              <a href="mailto:research@healthdb.ai" className="btn-secondary text-lg px-10 py-4">
                Schedule Demo
              </a>
            </div>
            <p className="text-white/30 text-sm mt-8">
              Already have access? <Link to="/login" className="text-blue-400 hover:underline">Sign in to your dashboard</Link>
            </p>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default ForResearchers;
