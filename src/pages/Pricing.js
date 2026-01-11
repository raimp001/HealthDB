import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const Pricing = () => {
  const tiers = [
    {
      name: 'Explorer',
      price: 'Free',
      description: 'For preliminary research and feasibility assessment',
      features: [
        'Aggregate statistics only',
        'Cohort feasibility counts',
        'Browse data dictionary',
        'Community support',
      ],
      limitations: [
        'No patient-level data',
        'No data export',
      ],
      cta: 'Get Started',
      ctaLink: '/register',
      highlighted: false,
    },
    {
      name: 'Researcher',
      price: 'Custom',
      priceNote: 'Based on study scope',
      description: 'For IRB-approved academic studies',
      features: [
        'Patient-level de-identified data',
        'Visual cohort builder',
        'IRB protocol generator',
        'DUA template library',
        'Central sIRB submission',
        'Data export (CSV, REDCap)',
        'Email support',
      ],
      limitations: [],
      cta: 'Request Access',
      ctaLink: '/register',
      highlighted: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      priceNote: 'Annual contract',
      description: 'For pharma, biotech, and large research networks',
      features: [
        'Everything in Researcher',
        'Unlimited queries',
        'API access',
        'Multi-site collaboration tools',
        'Dedicated account manager',
        'Custom data pipelines',
        'SLA guarantee',
        'Priority support',
      ],
      limitations: [],
      cta: 'Contact Sales',
      ctaLink: 'mailto:sales@healthdb.ai',
      highlighted: false,
    },
  ];

  const institutionBenefits = [
    {
      icon: '🔗',
      title: 'Join the Network',
      description: 'Contribute data and participate in multi-center studies without individual DUA negotiations.',
    },
    {
      icon: '📊',
      title: 'Data Contribution Credits',
      description: 'Institutions receive credits based on data volume and quality, redeemable for research access.',
    },
    {
      icon: '🤝',
      title: 'Collaborative Research',
      description: 'Pre-negotiated reliance agreements mean your researchers can start studies faster.',
    },
    {
      icon: '🛡️',
      title: 'Compliance Handled',
      description: 'We manage IRB coordination, DUAs, and HIPAA compliance for all studies.',
    },
  ];

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-block px-3 py-1 text-xs font-medium tracking-wider text-emerald-400 border border-emerald-500/30 rounded-full mb-6">
              PRICING
            </span>
            <h1 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight">
              Simple, transparent pricing
            </h1>
            <p className="text-xl text-neutral-400 max-w-2xl mx-auto">
              Pay for what you need. No hidden fees. Academic discounts available.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Pricing Tiers */}
      <section className="pb-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-3 gap-6">
            {tiers.map((tier, index) => (
              <motion.div
                key={tier.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={`relative p-8 rounded-lg border ${
                  tier.highlighted 
                    ? 'bg-emerald-500/5 border-emerald-500/30' 
                    : 'bg-neutral-900/50 border-neutral-800'
                }`}
              >
                {tier.highlighted && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="px-3 py-1 bg-emerald-500 text-black text-xs font-semibold rounded-full">
                      MOST POPULAR
                    </span>
                  </div>
                )}
                
                <h3 className="text-xl font-bold mb-2">{tier.name}</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold">{tier.price}</span>
                  {tier.priceNote && (
                    <span className="text-sm text-neutral-400 ml-2">{tier.priceNote}</span>
                  )}
                </div>
                <p className="text-sm text-neutral-400 mb-6">{tier.description}</p>
                
                <ul className="space-y-3 mb-6">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <span className="text-emerald-400 mt-0.5">✓</span>
                      <span className="text-neutral-300">{feature}</span>
                    </li>
                  ))}
                  {tier.limitations.map((limitation) => (
                    <li key={limitation} className="flex items-start gap-2 text-sm">
                      <span className="text-neutral-600 mt-0.5">✕</span>
                      <span className="text-neutral-500">{limitation}</span>
                    </li>
                  ))}
                </ul>
                
                {tier.ctaLink.startsWith('mailto') ? (
                  <a
                    href={tier.ctaLink}
                    className={`block w-full py-3 text-center font-medium rounded transition-colors ${
                      tier.highlighted
                        ? 'bg-emerald-500 text-black hover:bg-emerald-400'
                        : 'bg-white/10 text-white hover:bg-white/20'
                    }`}
                  >
                    {tier.cta}
                  </a>
                ) : (
                  <Link
                    to={tier.ctaLink}
                    className={`block w-full py-3 text-center font-medium rounded transition-colors ${
                      tier.highlighted
                        ? 'bg-emerald-500 text-black hover:bg-emerald-400'
                        : 'bg-white/10 text-white hover:bg-white/20'
                    }`}
                  >
                    {tier.cta}
                  </Link>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* For Institutions */}
      <section className="py-24 px-6 border-t border-neutral-800">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">For Institutions</h2>
            <p className="text-neutral-400 max-w-2xl mx-auto">
              Partner with HealthDB to join our research network. No upfront costs—contribute data, 
              enable your researchers, and accelerate collaborative studies.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {institutionBenefits.map((benefit, index) => (
              <motion.div
                key={benefit.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="p-6 bg-neutral-900/50 border border-neutral-800 rounded-lg"
              >
                <span className="text-2xl mb-4 block">{benefit.icon}</span>
                <h3 className="text-lg font-semibold mb-2">{benefit.title}</h3>
                <p className="text-sm text-neutral-400">{benefit.description}</p>
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-12">
            <a
              href="mailto:partnerships@healthdb.ai"
              className="inline-block px-8 py-4 bg-white text-black font-medium hover:bg-gray-100 transition-colors"
            >
              Become a Partner Institution
            </a>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-24 px-6 border-t border-neutral-800">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
          
          <div className="space-y-6">
            {[
              {
                q: 'What data access levels are available?',
                a: 'We offer three levels: aggregate statistics (counts only), de-identified patient-level data (HIPAA Safe Harbor), and limited datasets with dates (requires additional DUA).',
              },
              {
                q: 'How long does IRB approval take?',
                a: 'Using our central sIRB, initial approval typically takes 2-3 weeks. Sites with pre-negotiated reliance agreements can be added in days.',
              },
              {
                q: 'Is there academic pricing?',
                a: 'Yes, we offer significant discounts for academic and non-profit institutions. Contact us for details.',
              },
              {
                q: 'What EMR systems do you support?',
                a: 'We have direct integrations with Epic (via Cosmos and FHIR) and Cerner. Other systems can connect via secure file transfer.',
              },
              {
                q: 'How is patient data protected?',
                a: 'All data is de-identified per HIPAA guidelines. We maintain SOC 2 Type II certification and undergo regular security audits.',
              },
            ].map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                viewport={{ once: true }}
                className="p-6 bg-neutral-900/30 border border-neutral-800 rounded-lg"
              >
                <h3 className="font-semibold mb-2">{faq.q}</h3>
                <p className="text-sm text-neutral-400">{faq.a}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-neutral-800">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to get started?</h2>
          <p className="text-neutral-400 mb-8">
            Schedule a demo to see how HealthDB can accelerate your research.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="https://calendly.com/healthdb/demo"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-emerald-500 text-black font-medium hover:bg-emerald-400 transition-colors"
            >
              Schedule Demo
            </a>
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

export default Pricing;
