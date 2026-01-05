import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const LandingPage = () => {
  const capabilities = [
    {
      title: 'EMR Integration',
      description: 'Connect to Epic, Cerner, MEDITECH via FHIR or direct database access.',
    },
    {
      title: 'Longitudinal Tracking',
      description: 'Follow patient outcomes across multiple lines of therapy over time.',
    },
    {
      title: 'De-identification',
      description: 'HIPAA-compliant data anonymization with patient consent management.',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Hero Section - Clean & Minimal */}
      <section className="relative py-32">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-4xl md:text-5xl font-bold text-white leading-tight mb-6">
              Longitudinal Cancer Research Database
            </h1>
            
            <p className="text-lg text-slate-400 mb-10 max-w-2xl mx-auto">
              A platform for collecting, de-identifying, and sharing oncology data 
              to enable retrospective studies and personalized medicine.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/register?type=researcher"
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
              >
                Join as Researcher
              </Link>
              <Link
                to="/register?type=patient"
                className="px-6 py-3 bg-slate-800 text-white border border-slate-700 rounded-lg font-medium hover:bg-slate-700 transition-colors"
              >
                Join as Patient
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* What We're Building */}
      <section className="py-20 bg-slate-800/50">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-semibold text-white mb-8 text-center">
            What We're Building
          </h2>
          
          <div className="grid md:grid-cols-3 gap-6">
            {capabilities.map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-6 bg-slate-800 rounded-lg border border-slate-700"
              >
                <h3 className="text-lg font-medium text-white mb-2">
                  {item.title}
                </h3>
                <p className="text-slate-400 text-sm">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-semibold text-white mb-8 text-center">
            How It Works
          </h2>
          
          <div className="space-y-6">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center text-white font-medium flex-shrink-0">
                1
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">Institutions Connect EMRs</h3>
                <p className="text-slate-400 text-sm">
                  Healthcare institutions connect their EMR systems to securely share de-identified patient data.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center text-white font-medium flex-shrink-0">
                2
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">Patients Consent & Earn</h3>
                <p className="text-slate-400 text-sm">
                  Patients opt-in to share their data, maintain full control, and receive rewards when their data contributes to research.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center text-white font-medium flex-shrink-0">
                3
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">Researchers Build Cohorts</h3>
                <p className="text-slate-400 text-sm">
                  Researchers query the database to build cohorts for retrospective studies without accessing identifiable information.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 border-t border-slate-800">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-semibold text-white mb-4">
            Interested in Partnering?
          </h2>
          <p className="text-slate-400 mb-8">
            We're looking for healthcare institutions and researchers to help build this platform.
          </p>
          <a
            href="mailto:contact@healthdb.ai"
            className="inline-block px-6 py-3 bg-white text-slate-900 rounded-lg font-medium hover:bg-slate-100 transition-colors"
          >
            Get in Touch
          </a>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
