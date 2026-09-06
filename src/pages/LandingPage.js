import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const statusGroups = [
  {
    status: 'Prototype works today',
    tone: 'emerald',
    items: [
      'Role-scoped patient, researcher, and institution workspaces',
      'FHIR R4 bundle parsing and identifier checks for supported synthetic fields',
      'Consent records, revocation states, and patient-visible access events',
      'Cohort feasibility with suppression of small aggregate results',
    ],
  },
  {
    status: 'Ready for pilot validation',
    tone: 'blue',
    items: [
      'Cohort criteria and variable-selection usability',
      'Study, regulatory, and data-request workflow design',
      'De-identification test coverage and data-quality benchmarks',
      'Institutional governance and audit requirements',
    ],
  },
  {
    status: 'Not available',
    tone: 'amber',
    items: [
      'Real patient-data intake or production EHR connections',
      'Institutional data-use or business-associate agreements',
      'A central IRB, partner-site network, or production datasets',
      'Clinical use, certifications, or self-service data export',
    ],
  },
];

const toneClasses = {
  emerald: 'border-emerald-400/20 text-emerald-300',
  blue: 'border-blue-400/20 text-blue-300',
  amber: 'border-amber-400/20 text-amber-300',
};

const LandingPage = () => (
  <div className="bg-black text-white">
    <section className="relative min-h-[calc(100vh-2rem)] flex items-center overflow-hidden px-6 py-24">
      <div className="absolute inset-0 gradient-bg" />
      <div className="absolute inset-0 grid-pattern" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[760px] h-[760px] bg-emerald-400/5 rounded-full blur-[120px]" />

      <div className="relative z-10 max-w-6xl mx-auto w-full grid lg:grid-cols-[1.35fr_0.65fr] gap-14 items-end">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <p className="text-xs uppercase tracking-[0.24em] text-emerald-300 mb-6">
            Oncology research infrastructure · closed pilot
          </p>
          <h1 className="text-5xl md:text-7xl font-medium tracking-tight mb-7 max-w-4xl">
            Design safer research data workflows before real data enters them.
          </h1>
          <p className="text-lg md:text-xl text-white/55 max-w-2xl mb-9 leading-relaxed">
            HealthDB is a working technical prototype for consent, de-identification, cohort
            feasibility, and research governance. Pilot evaluations use synthetic data only.
          </p>
          <div className="flex flex-col sm:flex-row flex-wrap gap-3">
            <Link to="/demo" className="px-7 py-3.5 bg-white text-black text-center font-medium hover:bg-gray-100 transition-colors">
              Try the research demo
            </Link>
            <Link to="/care-guide" className="px-7 py-3.5 border border-white/20 text-center hover:bg-white/5 transition-colors">
              Explore the care guide
            </Link>
          </div>
        </motion.div>

        <motion.aside
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.12 }}
          className="border border-white/10 bg-black/35 p-6"
          aria-label="Pilot boundaries"
        >
          <p className="text-xs uppercase tracking-[0.2em] text-white/35 mb-5">Pilot boundary</p>
          <dl className="space-y-5">
            {[
              ['Data', 'Synthetic examples only'],
              ['Access', 'Public demo · invited workspaces'],
              ['Purpose', 'Workflow and control testing'],
              ['Production readiness', 'Not yet'],
            ].map(([term, detail]) => (
              <div key={term} className="border-l border-white/15 pl-4">
                <dt className="text-xs text-white/35 mb-1">{term}</dt>
                <dd className="text-sm text-white/75">{detail}</dd>
              </div>
            ))}
          </dl>
          <Link to="/login" className="inline-block text-sm text-white/50 hover:text-white mt-7 transition-colors">
            Already invited? Sign in →
          </Link>
        </motion.aside>
      </div>
    </section>

    <section id="status" className="py-24 px-6 border-t border-white/5 scroll-mt-32">
      <div className="max-w-6xl mx-auto">
        <div className="max-w-2xl mb-12">
          <p className="text-xs uppercase tracking-[0.2em] text-white/35 mb-4">Product status</p>
          <h2 className="text-3xl md:text-4xl font-medium mb-4">What exists, what needs validation, and what does not exist</h2>
          <p className="text-white/45">A code-complete screen is not the same as a validated healthcare workflow. HealthDB labels that boundary explicitly.</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-5">
          {statusGroups.map((group) => (
            <article key={group.status} className={`p-6 border ${toneClasses[group.tone]}`}>
              <h3 className="text-sm font-medium mb-6">{group.status}</h3>
              <ul className="space-y-4 text-sm text-white/55">
                {group.items.map((item) => (
                  <li key={item} className="flex gap-3">
                    <span aria-hidden="true" className="text-white/25">—</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>

    <section className="py-24 px-6 border-t border-white/5">
      <div className="max-w-6xl mx-auto grid lg:grid-cols-[0.7fr_1.3fr] gap-14">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-blue-300 mb-4">Evaluation path</p>
          <h2 className="text-3xl font-medium mb-5">Test the whole research journey without handling PHI</h2>
          <p className="text-white/45 leading-relaxed">
            The pilot is designed to expose workflow gaps early—before integrations, agreements,
            and real records make changes expensive.
          </p>
        </div>
        <ol className="grid sm:grid-cols-2 gap-px bg-white/10 border border-white/10">
          {[
            ['01', 'Frame the question', 'Translate a study idea into explicit cohort and variable criteria.'],
            ['02', 'Run synthetic feasibility', 'Exercise aggregate queries and small-cell suppression behavior.'],
            ['03', 'Review governance', 'Walk through consent, access, regulatory, and audit states.'],
            ['04', 'Document gaps', 'Turn evaluator feedback into measurable product and safety requirements.'],
          ].map(([step, title, description]) => (
            <li key={step} className="bg-black p-6 min-h-44">
              <span className="text-xs font-mono text-white/25">{step}</span>
              <h3 className="font-medium mt-7 mb-3">{title}</h3>
              <p className="text-sm text-white/45 leading-relaxed">{description}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>

    <section className="py-24 px-6 border-t border-white/5">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-medium mb-10">Choose your perspective</h2>
        <div className="grid md:grid-cols-3 gap-5">
          {[
            ['/researchers', 'Researchers', 'Evaluate cohort logic, study setup, variable selection, and export controls.'],
            ['/patients', 'Patients and caregivers', 'Help shape understandable consent, control, and transparency experiences.'],
            ['/institutions', 'Institutions', 'Review governance, privacy, security, and integration requirements.'],
          ].map(([to, title, description]) => (
            <Link key={to} to={to} className="group p-6 border border-white/10 hover:border-white/25 transition-colors">
              <h3 className="font-medium mb-3 group-hover:text-emerald-300 transition-colors">{title}</h3>
              <p className="text-sm text-white/45 mb-7 leading-relaxed">{description}</p>
              <span className="text-sm text-white/50">Explore →</span>
            </Link>
          ))}
        </div>
      </div>
    </section>

    <section className="py-24 px-6 border-t border-white/5">
      <div className="max-w-3xl mx-auto text-center">
        <p className="text-xs uppercase tracking-[0.2em] text-amber-300 mb-5">Build with us</p>
        <h2 className="text-3xl md:text-4xl font-medium mb-5">Help define the bar for a credible pilot</h2>
        <p className="text-white/45 mb-8">We are seeking focused feedback from oncology researchers, patient advisors, privacy teams, and clinical informaticists.</p>
        <Link to="/contact" className="inline-block px-8 py-3.5 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
          Request a pilot conversation
        </Link>
      </div>
    </section>
  </div>
);

export default LandingPage;
