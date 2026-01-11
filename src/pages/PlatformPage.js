import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  DatabaseIcon,
  ShieldCheckIcon,
  UserGroupIcon,
  ClipboardDocumentCheckIcon,
  DocumentTextIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  LockClosedIcon,
  ServerIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';

const PlatformPage = () => {
  const features = [
    {
      icon: DatabaseIcon,
      title: 'MRN-Based EMR Extraction',
      description: 'Define cohort criteria or upload MRN lists. System queries Epic, Cerner, AllScripts, and MEDITECH EMRs, extracts specified variables, and validates consent compliance.',
      capabilities: [
        'Query by diagnosis (ICD-10), procedure (CPT), medication, lab values (LOINC)',
        'MRN format validation and existence verification across institutions',
        'Automatic consent verification before extraction',
        'Variable selection: Demographics, diagnoses, labs, meds, vitals, notes, imaging',
        'Date range specification (relative to diagnosis or absolute)',
        'Parallel extraction with batch processing (100 patients per batch)',
        'FHIR R4 resource mapping and data standardization',
        'Real-time progress tracking and error handling with retry logic'
      ]
    },
    {
      icon: ClipboardDocumentCheckIcon,
      title: 'Multi-Institutional IRB Coordination',
      description: 'Streamlined IRB approval with support for both single IRB (sIRB) and independent IRB models, cutting approval time from 6-12 months to 30 days.',
      capabilities: [
        'Protocol submission wizard with step-by-step guidance',
        'Single IRB model: Lead IRB reviews, participating sites sign reliance agreements',
        'Independent IRB model: Simultaneous submission with harmonization support',
        'Automated reliance agreement workflow with electronic signatures',
        'Real-time status dashboard tracking approval at each site',
        'Continuing review automation with annual renewal reminders',
        'Adverse event reporting with automatic routing (SAE within 24 hours)',
        'Protocol deviation tracking and root cause analysis',
        'Multi-site amendment coordination with version control'
      ]
    },
    {
      icon: DocumentTextIcon,
      title: 'Data Sharing Agreement (DSA) Management',
      description: 'Automated generation, negotiation, and compliance monitoring of Data Use Agreements with institutional revenue sharing built-in.',
      capabilities: [
        'Auto-generated DUA templates based on IRB protocol and data scope',
        'Negotiation workflow: Recipient legal review → Provider review → Iteration',
        'Electronic signature collection via DocuSign integration',
        'Multi-party DUA support for multi-institutional studies',
        'Customizable terms: Publication embargoes, IP ownership, revenue sharing',
        'Compliance monitoring: Access logging, rate limit enforcement, anomaly detection',
        'Violation response: Warnings, suspension, termination, legal action',
        'Renewal management with 90/60/30-day reminders'
      ]
    },
    {
      icon: ShieldCheckIcon,
      title: 'Consent Management & Blockchain',
      description: 'Granular patient consent with biometric signing, comprehension quizzes, and blockchain anchoring for immutable audit trails.',
      capabilities: [
        'Consent types: General research, specific study, commercial use, genetic data, broad sharing, future contact',
        'Signature methods: Electronic, biometric (Face ID/fingerprint), witnessed, video consent',
        'Comprehension quiz (≥80% required) with adaptive learning',
        'Blockchain anchoring: SHA-256 hash of signed consent → Ethereum/Hyperledger',
        'Partial withdrawal: Granular control (withdraw commercial use, keep academic)',
        'Complete withdrawal: Revoke all access + optional data deletion',
        'Re-consent workflow for protocol amendments with side-by-side comparison',
        'Access transparency: Patients see all data access events in real-time'
      ]
    },
    {
      icon: LockClosedIcon,
      title: 'HIPAA-Compliant De-identification',
      description: 'Automated removal of 18 HIPAA identifiers with advanced NLP for clinical notes, ensuring Safe Harbor compliance.',
      capabilities: [
        'Direct identifier removal: Names, addresses, SSN, phone, email, photos',
        'MRN tokenization: Replace MRN with random token (consistent across queries)',
        'Date shifting: Shift all dates by random offset (consistent per patient)',
        'Quasi-identifier generalization: Age → ranges, zip → 3 digits',
        'Free text scrubbing: NER (Named Entity Recognition) detects PHI in clinical notes',
        'HIPAA Safe Harbor compliance: All 18 identifiers removed',
        'Expert Determination option: Statistical disclosure risk assessment',
        'Zero-Knowledge Proofs (ZKP): Verify data integrity without revealing content'
      ]
    },
    {
      icon: CurrencyDollarIcon,
      title: 'Patient & Institution Revenue Sharing',
      description: 'Ethical data monetization with 30% to patients, 10% to institutions, 60% to platform. Transparent earnings and multiple payout options.',
      capabilities: [
        'Patient share: 30% of net revenue distributed pro-rata by data completeness',
        'Institution share: 10% of net revenue distributed by patient contribution count',
        'Quarterly distributions with $10 minimum threshold',
        'Payment options: Cash (direct deposit), HealthDB Points (gift cards), charity donation',
        'Data completeness bonus: Higher quality data earns up to 20% more',
        'Tax reporting: 1099-MISC issued if annual total >$600 (US)',
        'Revenue transparency dashboard: Patients see estimated earnings',
        'Pricing calculator: Researchers estimate costs by tier (academic, startup, enterprise, pharma)'
      ]
    },
    {
      icon: ServerIcon,
      title: 'Data Marketplace & Licensing',
      description: 'Browse packaged datasets, license data with tiered pricing, track usage, and manage access permissions with automated enforcement.',
      capabilities: [
        'Data product types: Complete datasets, cohort extracts, aggregate reports, API access, custom extracts',
        'Pricing tiers: Academic (70-80% discount), Startup (40-50%), Enterprise (10-20%), Pharma (list price), Government (30%)',
        'Pricing models: Per-patient, subscription, one-time, per-query, custom negotiation',
        'License features by tier: Query limits, API calls, downloads, active users',
        'Usage tracking: Query count, API calls, download volume, session duration',
        'Automated enforcement: Soft limits (warnings), hard limits (block access), overage fees',
        'License renewal: 10% discount on same tier, 15% for 2-year, 20% for 3-year',
        'Auto-renewal with 60-day notice and opt-out window'
      ]
    },
    {
      icon: ChartBarIcon,
      title: 'Cohort Builder & Query Engine',
      description: 'Interactive cohort selection with real-time size estimation, multi-dimensional filtering, and cohort validation.',
      capabilities: [
        'Filter by cancer type: Hematologic (leukemia, lymphoma, myeloma) or solid tumors',
        'Demographics: Age at diagnosis (ranges), sex, race, ethnicity',
        'Disease stage: I-IV, relapsed, refractory, newly diagnosed',
        'Treatment types: Chemotherapy, immunotherapy, CAR-T, radiation, surgery, transplant',
        'Minimum follow-up requirements (e.g., ≥12 months)',
        'Lab value filters (e.g., hemoglobin <10, platelets <50k)',
        'Date range selection with relative or absolute dates',
        'Real-time cohort size estimation and characteristic visualization',
        'Cohort validation: Minimum n≥10 for re-identification protection',
        'Saved cohorts for reuse and sharing with collaborators'
      ]
    },
    {
      icon: UserGroupIcon,
      title: 'Multi-Site Collaboration Tools',
      description: 'Secure messaging, project management, and team coordination for distributed research teams with role-based access control.',
      capabilities: [
        'End-to-end encrypted messaging with AES-256 encryption',
        'Project workspaces: Share cohorts, queries, and results with team',
        'Role-based access control: PI, Co-Investigator, Research Coordinator, Data Analyst',
        'Team member management: Invite, remove, adjust permissions',
        'Activity feed: See team member actions and project updates',
        'Document sharing: Upload and share IRB documents, protocols, publications',
        'Task management: Assign tasks, set deadlines, track completion',
        'Video conferencing integration: Zoom/Teams links for study meetings'
      ]
    },
    {
      icon: BeakerIcon,
      title: 'Data Quality & Validation',
      description: 'Automated quality checks ensuring completeness, accuracy, consistency, plausibility, and timeliness of extracted data.',
      capabilities: [
        'Completeness: ≥80% of important fields populated, 100% of critical fields',
        'Format validation: ICD-10 codes match regex, dates in ISO-8601',
        'Value range checks: Lab values within biological limits (e.g., Hgb 0-25 g/dL)',
        'Consistency checks: Diagnosis date ≤ treatment date ≤ outcome date',
        'Cross-field validation: Age at diagnosis = DOB + diagnosis date',
        'Timeliness: Data updated within 7 days (prospective) or 30 days (retrospective)',
        'Terminology mapping: ICD-9/10 → ICD-10-CM, local codes → LOINC, meds → RxNorm',
        'Quality score: Overall data quality metric (0-100) per patient',
        'Error reports: Detailed reports on failed validations for manual review',
        'Auto-correction: Simple errors auto-corrected (e.g., date format fixes)'
      ]
    }
  ];

  return (
    <div className="bg-black text-white min-h-screen">
      {/* Hero Section */}
      <section className="relative py-32 px-6 overflow-hidden">
        <div className="absolute inset-0 gradient-bg" />
        <div className="absolute inset-0 grid-pattern" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#00d4aa]/5 rounded-full blur-[100px]" />

        <div className="relative z-10 max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="heading-display text-5xl md:text-6xl lg:text-7xl text-white mb-6">
              Platform
              <br />
              <span className="text-white/60">Capabilities</span>
            </h1>
            <p className="text-lg md:text-xl text-white/50 max-w-2xl mx-auto mb-12 font-light">
              Comprehensive infrastructure for longitudinal health data research with
              IRB management, EMR integration, consent management, and ethical monetization.
            </p>
            <Link to="/register" className="btn-primary">
              Get Started
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="space-y-24">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card-glass p-10"
              >
                <div className="flex items-start gap-6">
                  <div className="flex-shrink-0">
                    <div className="w-14 h-14 rounded-xl bg-[#00d4aa]/10 flex items-center justify-center border border-[#00d4aa]/20">
                      <feature.icon className="w-7 h-7 text-[#00d4aa]" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-medium text-white mb-3">
                      {feature.title}
                    </h3>
                    <p className="text-white/60 text-base mb-6 leading-relaxed">
                      {feature.description}
                    </p>
                    <div className="space-y-2">
                      {feature.capabilities.map((capability, idx) => (
                        <div key={idx} className="flex items-start gap-3">
                          <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-[#00d4aa]/50 mt-2" />
                          <span className="text-white/40 text-sm leading-relaxed">
                            {capability}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Technical Specifications */}
      <section className="py-20 px-6 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <h2 className="heading-display text-4xl md:text-5xl text-white/90 mb-4">
              Technical
              <br />
              <span className="text-white/40">Specifications</span>
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { label: 'EMR Systems', value: 'Epic, Cerner, AllScripts, MEDITECH' },
              { label: 'Standards', value: 'FHIR R4, LOINC, RxNorm, SNOMED' },
              { label: 'Compliance', value: 'HIPAA, SOC 2, HITRUST' },
              { label: 'Security', value: 'AES-256, TLS 1.3, WebAuthn' },
              { label: 'Database', value: 'PostgreSQL with TDE' },
              { label: 'API', value: 'FastAPI (Python 3.11)' },
              { label: 'Frontend', value: 'React 18, Tailwind CSS' },
              { label: 'Blockchain', value: 'Ethereum / Hyperledger' },
            ].map((spec, index) => (
              <motion.div
                key={spec.label}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                viewport={{ once: true }}
                className="card-glass p-6"
              >
                <p className="text-xs uppercase tracking-[0.2em] text-white/30 mb-2">
                  {spec.label}
                </p>
                <p className="text-white/80 text-sm font-medium">
                  {spec.value}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Performance Metrics */}
      <section className="py-20 px-6 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <h2 className="heading-display text-4xl md:text-5xl text-white/90 mb-4">
              Performance
              <br />
              <span className="text-white/40">Benchmarks</span>
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { metric: 'IRB Approval Time', value: '30 days', comparison: 'vs 6-12 months traditional' },
              { metric: 'Data Extraction Speed', value: '100 patients/min', comparison: 'with parallel processing' },
              { metric: 'De-identification Rate', value: '50 records/sec', comparison: 'HIPAA Safe Harbor' },
              { metric: 'Query Response Time', value: '<2 seconds', comparison: 'for cohort queries' },
              { metric: 'Uptime SLA', value: '99.9%', comparison: '<44 min downtime/month' },
              { metric: 'Data Completeness', value: '≥80%', comparison: 'for important fields' },
            ].map((perf, index) => (
              <motion.div
                key={perf.metric}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card-glass p-8"
              >
                <p className="text-xs uppercase tracking-[0.2em] text-white/30 mb-3">
                  {perf.metric}
                </p>
                <p className="text-3xl font-light text-[#00d4aa] mb-2">
                  {perf.value}
                </p>
                <p className="text-xs text-white/40">
                  {perf.comparison}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-6 border-t border-white/10">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="heading-display text-4xl md:text-5xl lg:text-6xl text-white/90 mb-6">
              Ready to get started?
            </h2>
            <p className="text-white/40 text-lg mb-12 max-w-xl mx-auto">
              Join healthcare institutions and researchers building the future of
              longitudinal health data research.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register" className="btn-primary">
                Create Account
              </Link>
              <Link to="/researchers" className="btn-secondary">
                For Researchers
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default PlatformPage;
