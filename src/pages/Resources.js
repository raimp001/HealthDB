import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

const Resources = () => {
  const [activeCategory, setActiveCategory] = useState('all');
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [selectedWhitepaper, setSelectedWhitepaper] = useState(null);

  const articles = [
    {
      id: 1,
      category: 'Research',
      title: 'The Future of Real-World Evidence in Oncology',
      excerpt: 'How patient-contributed data is transforming cancer research and accelerating treatment discoveries.',
      date: 'January 2026',
      readTime: '8 min read',
      content: `Real-world evidence (RWE) is revolutionizing how we understand cancer treatments and patient outcomes. Unlike traditional clinical trials that study carefully selected patient populations, RWE captures the full spectrum of patient experiences in everyday clinical practice.

**Why RWE Matters for Oncology**

Clinical trials typically exclude patients with comorbidities, older age, or previous treatments. This means trial results may not reflect outcomes for the majority of cancer patients. RWE fills this gap by:

- Capturing outcomes across diverse patient populations
- Tracking long-term treatment effects beyond trial endpoints
- Identifying rare adverse events that trials miss
- Comparing treatments that were never studied head-to-head

**The Patient-Contributed Data Revolution**

HealthDB enables patients to voluntarily contribute their de-identified health data to research. This approach offers several advantages:

1. **Scale**: Access to thousands of patient records across multiple institutions
2. **Longitudinal tracking**: Follow patients for years, not just months
3. **Real-world treatments**: See how therapies perform outside controlled settings
4. **Rapid insights**: Generate evidence in weeks instead of years

**Case Study: CAR-T Therapy Outcomes**

Using patient-contributed data, researchers identified that CAR-T response rates in the real world closely matched clinical trial data, but also discovered previously unreported late toxicities that only emerged with longer follow-up.

**Looking Ahead**

As more patients choose to contribute their data, we'll see RWE become the foundation for treatment decisions, regulatory approvals, and personalized medicine approaches.`
    },
    {
      id: 2,
      category: 'Ethics',
      title: 'Building Trust Through Transparent Data Governance',
      excerpt: 'Why consent-first data sharing is essential for the future of healthcare research.',
      date: 'January 2026',
      readTime: '6 min read',
      content: `Trust is the foundation of ethical health data research. Without it, patients won't share their data, and without data, research stalls. HealthDB has built a governance model centered on transparency and patient control.

**The Problem with Traditional Approaches**

Historically, patient data was collected and used with minimal transparency:

- Broad consent forms buried data sharing in legal language
- Patients had no visibility into how their data was used
- No mechanism to revoke consent or understand benefit

This approach has eroded trust, with many patients now hesitant to participate in research.

**Our Consent-First Model**

HealthDB operates on four principles:

1. **Informed Consent**: Clear, plain-language explanations of data use
2. **Granular Control**: Patients choose exactly what data to share and with whom
3. **Transparency**: Real-time visibility into who accessed their data
4. **Revocability**: One-click consent withdrawal at any time

**Tiered Consent Structure**

We offer four consent levels:

- **Tier 1**: Basic research (de-identified, aggregated only)
- **Tier 2**: Academic studies (individual-level, de-identified)
- **Tier 3**: Industry research (includes pharma and biotech)
- **Tier 4**: Full access (clinical trials, personalized medicine)

Each tier is separately controllable, giving patients fine-grained choice.

**The Access Log**

Every time a researcher queries data that includes a patient's records, the patient sees:

- Who accessed the data
- What study it was for
- Which data elements were included
- The date and time

This transparency builds trust and accountability.

**Results**

Patients who understand how their data is used are 3x more likely to participate in research. Transparent governance isn't just ethical—it's effective.`
    },
    {
      id: 3,
      category: 'Technology',
      title: 'De-identification: Protecting Privacy While Enabling Research',
      excerpt: 'Technical approaches to ensuring patient privacy in longitudinal health data.',
      date: 'December 2025',
      readTime: '10 min read',
      content: `De-identification is the technical foundation of privacy-preserving research. Done right, it enables valuable insights while making re-identification effectively impossible.

**HIPAA Standards**

HIPAA defines two de-identification methods:

1. **Safe Harbor**: Remove 18 specific identifiers
2. **Expert Determination**: Statistical verification that re-identification risk is very small

HealthDB implements both, choosing the appropriate method based on data sensitivity and use case.

**The 18 Safe Harbor Identifiers**

- Names
- Geographic data (smaller than state)
- Dates (except year) for dates related to an individual
- Phone numbers
- Fax numbers
- Email addresses
- Social Security numbers
- Medical record numbers
- Health plan numbers
- Account numbers
- Certificate/license numbers
- Vehicle identifiers
- Device identifiers
- URLs
- IP addresses
- Biometric identifiers
- Full-face photos
- Any unique identifying number

**Beyond Safe Harbor**

For longitudinal cancer data, additional protections are necessary:

**Date Shifting**
Instead of removing dates entirely, we shift all dates for a patient by a random offset (±180 days), preserving temporal relationships while preventing identification.

**Generalization**
Rare values are generalized. A rare cancer type affecting <10 patients might be categorized as "Other hematologic malignancy."

**K-Anonymity**
Every record is indistinguishable from at least k-1 other records on quasi-identifiers. We maintain k≥5 across all datasets.

**Differential Privacy**
For aggregate queries, we add calibrated noise to prevent inference attacks.

**Validation**

Our de-identification pipeline is validated through:

- Automated testing against known re-identification attacks
- Third-party security audits
- Regular penetration testing
- Statistical analysis of re-identification risk

**The Result**

Researchers get the longitudinal data they need. Patients get mathematical guarantees of privacy. That's the balance we've achieved.`
    },
    {
      id: 4,
      category: 'Regulatory',
      title: 'Navigating IRB Approval for Data-Driven Studies',
      excerpt: 'Best practices for researchers seeking institutional review board approval.',
      date: 'November 2025',
      readTime: '9 min read',
      content: `IRB approval is often the longest part of research timelines. Understanding the process and using HealthDB's pre-negotiated agreements can reduce approval from 6 months to 3 weeks.

**Understanding IRB Requirements**

IRBs evaluate:

1. **Scientific merit**: Is the study well-designed?
2. **Risk-benefit ratio**: Do potential benefits justify risks?
3. **Informed consent**: Are participants properly informed?
4. **Privacy protections**: Is data adequately protected?
5. **Vulnerable populations**: Are appropriate safeguards in place?

**Why Traditional IRB Takes So Long**

Multi-site studies face compounded delays:

- Each site requires separate IRB review
- DUAs must be negotiated individually
- Legal review happens sequentially
- Amendments restart the clock

**HealthDB's Single IRB (sIRB) Model**

We've established a central IRB that serves as the IRB of record for all participating institutions. Benefits include:

- **One submission**: Submit once, cover all sites
- **Pre-negotiated reliance agreements**: 50+ institutions already signed
- **Standardized DUAs**: Legal-reviewed templates ready to sign
- **Fast turnaround**: Average 21 days to approval

**Preparing Your Submission**

Our protocol generator auto-populates:

- Study aims and background
- Data elements requested
- Privacy protections (based on our platform)
- Consent language (referencing patient consents)
- Risk mitigation (standard for de-identified data)

You provide:

- Scientific rationale
- Cohort criteria
- Analysis plan
- Investigator qualifications

**Common Pitfalls**

1. **Vague data requests**: Be specific about what variables you need
2. **Missing justification**: Explain why each data element is necessary
3. **Incomplete team**: Ensure all investigators are listed
4. **Consent mismatch**: Requested data must align with patient consent levels

**Post-Approval**

Once approved, you can:

- Run feasibility queries immediately
- Begin data extraction within 48 hours
- Add sites with reliance agreements in 24 hours

The regulatory burden shouldn't stop important research. We've built the infrastructure to make compliance efficient.`
    },
    {
      id: 5,
      category: 'Patients',
      title: 'Your Data, Your Choice: A Guide for Cancer Patients',
      excerpt: 'Understanding how your health data can contribute to research while maintaining control.',
      date: 'November 2025',
      readTime: '5 min read',
      content: `As a cancer patient, your health records contain valuable information that could help future patients. HealthDB makes it easy to contribute your data to research—on your terms.

**Why Contribute Your Data?**

Every treatment decision, every side effect, every outcome in your medical record is a data point that could:

- Help researchers find better treatments
- Identify which patients respond to which therapies
- Uncover rare side effects before others experience them
- Accelerate approval of new drugs

Many patients want to help. HealthDB makes it possible while protecting your privacy.

**How It Works**

1. **Connect**: Link your medical records from Epic MyChart, Cerner, or other systems
2. **Consent**: Choose what data to share and for what purposes
3. **Contribute**: Your de-identified data becomes available for approved research
4. **Track**: See exactly who uses your data and why

**Your Data is De-Identified**

Before any researcher sees your data, we remove all identifying information:

- Your name, address, and contact info
- Exact dates (replaced with relative timings)
- Medical record numbers
- Any other identifying details

Researchers see "Patient #12847 with Stage III Multiple Myeloma" not "John Smith."

**You Stay in Control**

- **Revoke anytime**: One click withdraws your consent
- **Change levels**: Adjust what you share as your preferences change
- **See the log**: Every data access is recorded and visible to you
- **Ask questions**: Our support team is here to help

**Rewards**

Contributing data earns you points redeemable for:

- Gift cards
- Charitable donations in your name
- Premium health tracking features

This isn't payment for data—it's recognition of your contribution to science.

**Getting Started**

1. Create an account at healthdb.ai
2. Verify your identity
3. Connect your medical records
4. Review and sign consent
5. Start contributing

Your data could help save lives. Your choice makes it possible.`
    },
    {
      id: 6,
      category: 'Industry',
      title: 'Multi-Center Collaboration: Breaking Down Data Silos',
      excerpt: 'How federated data networks enable large-scale oncology studies across institutions.',
      date: 'December 2025',
      readTime: '7 min read',
      content: `Cancer research requires scale. Rare cancers, specific mutations, and novel treatments all demand large patient populations that no single institution can provide. HealthDB enables multi-center collaboration without the traditional barriers.

**The Silo Problem**

Each cancer center has:

- Its own EMR system
- Unique data formats
- Separate governance
- Individual legal requirements

Getting data from multiple centers traditionally meant months of negotiations, custom data mappings, and substantial legal fees.

**The HealthDB Network**

We've built pre-existing relationships with 50+ institutions:

- **Technical integration**: EMR connectors in place
- **Legal framework**: Master DUAs already signed
- **IRB reliance**: Agreements ready to activate
- **Data standards**: OMOP CDM normalization

**How Multi-Center Studies Work**

1. **Define cohort**: Specify your inclusion/exclusion criteria
2. **Run feasibility**: See patient counts by site instantly
3. **Submit to sIRB**: One application covers all sites
4. **Activate sites**: Reliance agreements activate in 24 hours
5. **Extract data**: Normalized data from all sites in one dataset

**Case Study: CAR-T Registry**

A researcher studying CAR-T outcomes needed 500+ patients. No single center had enough. Through HealthDB:

- 8 sites identified with qualifying patients
- sIRB approved in 18 days
- All sites activated in 48 hours
- 547 patients in the final cohort
- Time from concept to data: 4 weeks

Traditional approach would have taken 6-12 months.

**Data Harmonization**

Different EMRs record data differently. We normalize to OMOP CDM:

- ICD-10 codes mapped to standard concepts
- Medication names to RxNorm
- Lab values to LOINC
- Consistent temporal relationships

Researchers get clean, analysis-ready data regardless of source.

**The Future: Federated Analytics**

For sensitive analyses, we're piloting federated approaches where:

- Queries go to the data, not data to the query
- Only aggregate results leave institutions
- PHI never moves

This enables even broader collaboration while strengthening privacy.`
    }
  ];

  const whitepapers = [
    {
      id: 1,
      title: 'Ethical Framework for Health Data Sharing',
      description: 'Our comprehensive guide to consent-based data governance in oncology research.',
      pages: '24 pages',
      sections: [
        { title: 'Executive Summary', content: 'Health data sharing requires a new ethical framework that puts patients at the center. This whitepaper outlines HealthDB\'s approach to consent-based governance.' },
        { title: '1. Introduction', content: 'The healthcare industry generates massive amounts of data daily, but extracting value while respecting patient rights remains challenging. Traditional approaches have prioritized institutional needs over patient autonomy.' },
        { title: '2. The Consent Framework', content: 'We propose a tiered consent model with four levels: basic research (aggregated only), academic studies (de-identified individual), industry research (including pharma), and full access (clinical trials). Each tier requires explicit opt-in.' },
        { title: '3. Transparency Requirements', content: 'Patients must have real-time visibility into data access. Our access log shows every query touching patient data, including researcher identity, study purpose, and data elements accessed.' },
        { title: '4. Revocation Rights', content: 'Consent can be withdrawn at any time with immediate effect for future queries. Historical data use is documented and explained to patients.' },
        { title: '5. Implementation Guidelines', content: 'Technical implementation requires: granular access controls, comprehensive audit logging, patient-facing dashboards, and regular consent verification.' },
        { title: '6. Governance Structure', content: 'A Patient Advisory Board reviews platform policies. An Ethics Committee evaluates edge cases. Regular third-party audits ensure compliance.' },
        { title: '7. Conclusion', content: 'Ethical data sharing is not just possible—it\'s essential for sustainable research. Patients who trust the system participate at 3x higher rates.' }
      ]
    },
    {
      id: 2,
      title: 'Technical Architecture for HIPAA-Compliant Data Platforms',
      description: 'How we built a secure, scalable infrastructure for sensitive health data.',
      pages: '18 pages',
      sections: [
        { title: 'Executive Summary', content: 'Building a HIPAA-compliant data platform requires security at every layer. This document details our architecture decisions and implementation.' },
        { title: '1. Threat Model', content: 'We consider: external attackers, insider threats, third-party risks, and regulatory exposure. Each requires specific mitigations.' },
        { title: '2. Data Architecture', content: 'PHI is stored in encrypted form using AES-256. Keys are managed in AWS KMS with hardware security modules. Data at rest and in transit is always encrypted.' },
        { title: '3. Access Control', content: 'Role-based access control (RBAC) with principle of least privilege. Researchers can only access data matching their approved protocols. All access is logged.' },
        { title: '4. De-identification Pipeline', content: 'Automated Safe Harbor compliance with date shifting, generalization, and k-anonymity verification. Statistical risk analysis before any data release.' },
        { title: '5. Audit & Logging', content: 'Comprehensive audit trail of all data access. Immutable logs stored separately. Real-time anomaly detection for unusual access patterns.' },
        { title: '6. Incident Response', content: 'Documented procedures for potential breaches. Automatic detection, containment, and notification workflows. Regular tabletop exercises.' },
        { title: '7. Compliance Validation', content: 'Annual SOC 2 Type II audits. Quarterly penetration testing. Continuous compliance monitoring with automated controls.' }
      ]
    },
    {
      id: 3,
      title: 'Real-World Evidence: From Data to Clinical Insights',
      description: 'Methodology for generating actionable insights from patient-contributed data.',
      pages: '32 pages',
      sections: [
        { title: 'Executive Summary', content: 'Real-world evidence complements clinical trials by capturing outcomes across diverse populations. This whitepaper provides methodology for valid RWE generation.' },
        { title: '1. RWE vs Clinical Trials', content: 'Trials offer internal validity through randomization. RWE offers external validity through broad populations. Both are necessary for complete evidence.' },
        { title: '2. Data Quality Framework', content: 'Garbage in, garbage out. We implement data quality checks at ingestion: completeness scoring, consistency verification, and plausibility testing.' },
        { title: '3. Bias Identification', content: 'Selection bias, information bias, and confounding all affect RWE. We document potential biases and provide statistical adjustments where possible.' },
        { title: '4. Causal Inference Methods', content: 'Propensity score matching, inverse probability weighting, and instrumental variables can approximate causal inference from observational data when properly applied.' },
        { title: '5. Outcome Definitions', content: 'Consistent outcome definitions are critical. We provide standardized definitions for PFS, OS, response rates, and toxicity grades mapped to source data elements.' },
        { title: '6. Sensitivity Analyses', content: 'Results should be robust to analytical choices. We recommend multiple approaches with consistency assessment.' },
        { title: '7. Reporting Standards', content: 'Follow STROBE guidelines for observational studies. Document all analytical decisions. Provide reproducibility packages.' },
        { title: '8. Regulatory Applications', content: 'FDA and EMA increasingly accept RWE for label expansions and post-marketing commitments. We outline requirements for regulatory-grade evidence.' }
      ]
    }
  ];

  const guides = [
    {
      title: 'Researcher Quick Start',
      description: 'Get from hypothesis to data in 30 minutes',
      steps: [
        'Create account and verify credentials',
        'Define your cohort criteria',
        'Run feasibility query',
        'Submit IRB application (auto-generated)',
        'Upon approval, queue data extraction',
        'Download analysis-ready dataset'
      ],
      audience: 'Researchers'
    },
    {
      title: 'Patient Onboarding',
      description: 'Start contributing your data today',
      steps: [
        'Sign up at healthdb.ai/register',
        'Verify your identity securely',
        'Connect your medical records (Epic, Cerner, etc.)',
        'Review and select consent levels',
        'Sign digital consent form',
        'Track your contributions and impact'
      ],
      audience: 'Patients'
    },
    {
      title: 'Institution Integration',
      description: 'Join the HealthDB network',
      steps: [
        'Sign master BAA and DUA',
        'Configure EMR integration (FHIR R4)',
        'Complete data quality validation',
        'Execute IRB reliance agreement',
        'Go live with patient enrollment',
        'Monitor ongoing data quality'
      ],
      audience: 'Institutions'
    }
  ];

  const categories = ['all', 'Research', 'Ethics', 'Technology', 'Regulatory', 'Patients', 'Industry'];

  const filteredArticles = activeCategory === 'all' 
    ? articles 
    : articles.filter(a => a.category === activeCategory);

  const categoryColors = {
    'Research': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    'Ethics': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    'Technology': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    'Industry': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    'Patients': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    'Regulatory': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <section className="relative pt-32 pb-16 px-6">
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 to-transparent" />
        <div className="max-w-5xl mx-auto relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-emerald-400 text-sm uppercase tracking-wider mb-4">Resources</p>
            <h1 className="text-4xl md:text-5xl font-bold mb-6">
              Insights & Documentation
            </h1>
            <p className="text-lg text-white/40 max-w-2xl">
              In-depth articles, whitepapers, and guides on ethical data sharing, 
              real-world evidence, and research methodology.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Quick Start Guides */}
      <section className="py-16 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">Quick Start Guides</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {guides.map((guide, index) => (
              <div key={index} className="p-6 border border-white/10 hover:border-white/20 transition-colors">
                <div className="text-xs text-emerald-400 mb-2">{guide.audience}</div>
                <h3 className="font-medium text-lg mb-2">{guide.title}</h3>
                <p className="text-sm text-white/40 mb-4">{guide.description}</p>
                <ol className="space-y-2">
                  {guide.steps.map((step, i) => (
                    <li key={i} className="text-xs text-white/60 flex gap-2">
                      <span className="text-emerald-400">{i + 1}.</span>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Articles */}
      <section className="py-16 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
            <h2 className="text-2xl font-bold">Articles</h2>
            <div className="flex flex-wrap gap-2">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-3 py-1 text-xs uppercase tracking-wider transition-colors ${
                    activeCategory === cat
                      ? 'bg-white text-black'
                      : 'border border-white/20 text-white/60 hover:border-white/40'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {filteredArticles.map((article) => (
              <motion.article
                key={article.id}
                layout
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="p-6 border border-white/10 hover:border-white/20 transition-colors cursor-pointer"
                onClick={() => setSelectedArticle(article)}
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className={`px-2 py-0.5 text-xs border ${categoryColors[article.category]}`}>
                    {article.category}
                  </span>
                  <span className="text-xs text-white/40">{article.readTime}</span>
                </div>
                <h3 className="font-medium text-lg mb-2">{article.title}</h3>
                <p className="text-sm text-white/40 mb-4">{article.excerpt}</p>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-white/30">{article.date}</span>
                  <span className="text-sm text-emerald-400">Read article →</span>
                </div>
              </motion.article>
            ))}
          </div>
        </div>
      </section>

      {/* Whitepapers */}
      <section className="py-16 px-6 border-t border-white/5 bg-white/[0.02]">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-2">Whitepapers & Guides</h2>
          <p className="text-white/40 mb-8">In-depth resources for researchers and institutions</p>
          
          <div className="grid md:grid-cols-3 gap-6">
            {whitepapers.map((paper) => (
              <div
                key={paper.id}
                className="p-6 border border-white/10 hover:border-emerald-500/30 transition-colors cursor-pointer"
                onClick={() => setSelectedWhitepaper(paper)}
              >
                <div className="w-10 h-10 bg-emerald-500/10 flex items-center justify-center mb-4">
                  <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="font-medium mb-2">{paper.title}</h3>
                <p className="text-sm text-white/40 mb-4">{paper.description}</p>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-white/30">{paper.pages}</span>
                  <span className="text-sm text-emerald-400">Read →</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Stay Updated</h2>
          <p className="text-white/40 mb-8">
            Monthly insights on ethical data sharing and oncology research.
          </p>
          <form className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
            <input
              type="email"
              placeholder="Enter your email"
              className="flex-1 px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-white/30 transition-colors"
            />
            <button
              type="submit"
              className="px-6 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors"
            >
              Subscribe
            </button>
          </form>
        </div>
      </section>

      {/* Article Modal */}
      {selectedArticle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={() => setSelectedArticle(null)}>
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-neutral-900 border border-white/10 max-w-3xl max-h-[80vh] overflow-y-auto w-full"
            onClick={e => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-neutral-900 border-b border-white/10 p-6 flex justify-between items-start">
              <div>
                <span className={`px-2 py-0.5 text-xs border ${categoryColors[selectedArticle.category]} mb-2 inline-block`}>
                  {selectedArticle.category}
                </span>
                <h2 className="text-xl font-bold">{selectedArticle.title}</h2>
                <p className="text-sm text-white/40 mt-1">{selectedArticle.date} · {selectedArticle.readTime}</p>
              </div>
              <button onClick={() => setSelectedArticle(null)} className="text-white/40 hover:text-white">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6">
              <div className="prose prose-invert max-w-none">
                {selectedArticle.content.split('\n\n').map((paragraph, i) => {
                  if (paragraph.startsWith('**') && paragraph.endsWith('**')) {
                    return <h3 key={i} className="text-lg font-bold mt-6 mb-3">{paragraph.replace(/\*\*/g, '')}</h3>;
                  }
                  if (paragraph.startsWith('- ')) {
                    return (
                      <ul key={i} className="list-disc list-inside space-y-1 text-white/60">
                        {paragraph.split('\n').map((item, j) => (
                          <li key={j}>{item.replace('- ', '')}</li>
                        ))}
                      </ul>
                    );
                  }
                  if (paragraph.match(/^\d\./)) {
                    return (
                      <ol key={i} className="list-decimal list-inside space-y-1 text-white/60">
                        {paragraph.split('\n').map((item, j) => (
                          <li key={j}>{item.replace(/^\d+\.\s*/, '')}</li>
                        ))}
                      </ol>
                    );
                  }
                  return <p key={i} className="text-white/60 mb-4">{paragraph}</p>;
                })}
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Whitepaper Modal */}
      {selectedWhitepaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={() => setSelectedWhitepaper(null)}>
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-neutral-900 border border-white/10 max-w-3xl max-h-[80vh] overflow-y-auto w-full"
            onClick={e => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-neutral-900 border-b border-white/10 p-6 flex justify-between items-start">
              <div>
                <p className="text-xs text-emerald-400 mb-2">WHITEPAPER</p>
                <h2 className="text-xl font-bold">{selectedWhitepaper.title}</h2>
                <p className="text-sm text-white/40 mt-1">{selectedWhitepaper.pages}</p>
              </div>
              <button onClick={() => setSelectedWhitepaper(null)} className="text-white/40 hover:text-white">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6">
              {selectedWhitepaper.sections.map((section, i) => (
                <div key={i} className="mb-6">
                  <h3 className="font-bold text-lg mb-2">{section.title}</h3>
                  <p className="text-white/60 text-sm leading-relaxed">{section.content}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default Resources;
