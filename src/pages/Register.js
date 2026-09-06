import React from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';

const AUDIENCE = {
  patient: {
    label: 'Patient and caregiver advisors',
    body: 'HealthDB is not accepting medical records. We are inviting patients and caregivers to help evaluate consent language, privacy controls, and access-log concepts using synthetic examples.',
    interest: 'patient',
  },
  institution: {
    label: 'Institutional design partners',
    body: 'We are looking for research, privacy, informatics, and governance teams to review the prototype and define the controls required before any institutional integration.',
    interest: 'institution',
  },
  researcher: {
    label: 'Research pilot partners',
    body: 'Researchers can request a guided evaluation of cohort and study workflows using synthetic data. Production datasets and self-service exports are not available.',
    interest: 'researcher',
  },
};

const Register = () => {
  const [searchParams] = useSearchParams();
  const requestedType = searchParams.get('type');
  const audience = AUDIENCE[requestedType] || AUDIENCE.researcher;

  return (
    <div className="min-h-screen bg-black flex items-center justify-center py-24 px-6 text-white">
      <div className="absolute inset-0 gradient-bg opacity-50" />
      <div className="absolute inset-0 grid-pattern" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-2xl"
      >
        <div className="mb-10">
          <p className="text-xs uppercase tracking-[0.2em] text-amber-300 mb-4">Invite-only pilot</p>
          <h1 className="heading-display text-4xl md:text-5xl mb-5">Request access, don’t upload data</h1>
          <p className="text-white/60 text-lg leading-relaxed">{audience.body}</p>
        </div>

        <div className="border border-white/10 bg-black/50 p-6 md:p-8 mb-6">
          <p className="text-sm font-medium mb-5">{audience.label}</p>
          <div className="grid sm:grid-cols-3 gap-4 mb-8">
            {[
              ['Environment', 'Synthetic data only'],
              ['Access', 'Guided and invite-only'],
              ['Use', 'Workflow evaluation'],
            ].map(([label, value]) => (
              <div key={label} className="border-l border-white/15 pl-4">
                <p className="text-xs uppercase tracking-wider text-white/30 mb-1">{label}</p>
                <p className="text-sm text-white/70">{value}</p>
              </div>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              to={`/contact?interest=${audience.interest}`}
              className="px-6 py-3 bg-white text-black text-center text-sm font-medium hover:bg-gray-100 transition-colors"
            >
              Request pilot access
            </Link>
            <Link
              to="/login"
              className="px-6 py-3 border border-white/20 text-center text-sm hover:bg-white/5 transition-colors"
            >
              Sign in with an invitation
            </Link>
          </div>
        </div>

        <p className="text-xs text-white/35 leading-relaxed">
          Do not submit patient identifiers, protected health information, or clinical records.
          HealthDB has no production data partnerships or third-party compliance certifications.
        </p>
      </motion.div>
    </div>
  );
};

export default Register;
