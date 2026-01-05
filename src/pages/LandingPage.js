import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const LandingPage = () => {
  const [platformStats, setPlatformStats] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/api/stats/platform`)
      .then(res => res.json())
      .then(data => setPlatformStats(data))
      .catch(err => console.error('Failed to fetch stats:', err));
  }, []);

  const stats = platformStats ? [
    { value: platformStats.total_patients.toLocaleString() + '+', label: 'Patient Records' },
    { value: platformStats.total_data_points.toLocaleString() + '+', label: 'Data Points' },
    { value: platformStats.partner_institutions.toString(), label: 'Partner Institutions' },
    { value: platformStats.active_studies.toString(), label: 'Active Studies' },
  ] : [
    { value: '—', label: 'Patient Records' },
    { value: '—', label: 'Data Points' },
    { value: '—', label: 'Partner Institutions' },
    { value: '—', label: 'Active Studies' },
  ];

  const features = [
    {
      icon: '🔬',
      title: 'Longitudinal Data',
      description: 'Track patient outcomes over time with comprehensive treatment and response data across multiple lines of therapy.',
    },
    {
      icon: '🏥',
      title: 'Multi-EMR Integration',
      description: 'Seamlessly connect to Epic, Cerner, MEDITECH and other EMR systems via FHIR or direct database access.',
    },
    {
      icon: '🧬',
      title: 'Molecular Profiling',
      description: 'Rich molecular and cytogenetic data including mutations, FISH, NGS results, and treatment-response correlations.',
    },
    {
      icon: '🤖',
      title: 'AI-Powered Insights',
      description: 'Machine learning models for treatment recommendations, outcome predictions, and clinical trial matching.',
    },
    {
      icon: '🔒',
      title: 'Privacy-First Design',
      description: 'De-identified data with patient consent. HIPAA compliant, SOC 2 certified, with full audit trails.',
    },
    {
      icon: '💰',
      title: 'Fair Compensation',
      description: 'Patients receive rewards for data sharing. Institutions get revenue share. Everyone benefits.',
    },
  ];

  const cancerTypes = [
    'Diffuse Large B-Cell Lymphoma',
    'Acute Myeloid Leukemia',
    'Multiple Myeloma',
    'Chronic Lymphocytic Leukemia',
    'Non-Small Cell Lung Cancer',
    'Breast Cancer',
    'Colorectal Cancer',
    'Melanoma',
  ];

  return (
    <div className="overflow-hidden">
      {/* Hero Section */}
      <section className="hero-gradient relative min-h-[90vh] flex items-center">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 right-0 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 left-0 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <span className="inline-flex items-center px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-300 text-sm font-medium mb-6">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse" />
                Now with CAR-T & Transplant Data
              </span>
              
              <h1 className="text-4xl md:text-6xl font-bold text-white leading-tight mb-6">
                The Future of
                <span className="block gradient-text">Cancer Research</span>
                Data
              </h1>
              
              <p className="text-xl text-slate-300 mb-8 max-w-lg">
                Access the largest longitudinal oncology database. Real-world outcomes, 
                molecular data, and treatment histories from 45,000+ patients.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/register?type=researcher"
                  className="px-8 py-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-semibold text-lg hover:from-indigo-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl flex items-center justify-center"
                >
                  <span className="mr-2">🔬</span>
                  Join as Researcher
                </Link>
                <Link
                  to="/register?type=patient"
                  className="px-8 py-4 bg-white/10 backdrop-blur text-white border border-white/20 rounded-xl font-semibold text-lg hover:bg-white/20 transition-all flex items-center justify-center"
                >
                  <span className="mr-2">💜</span>
                  Join as Patient
                </Link>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="hidden lg:block"
            >
              {/* Stats cards floating */}
              <div className="relative">
                <div className="glass rounded-2xl p-6 absolute top-0 right-0 animate-float">
                  <div className="text-3xl font-bold text-white">94%</div>
                  <div className="text-sm text-slate-300">Data Completeness</div>
                </div>
                <div className="glass rounded-2xl p-6 absolute bottom-20 left-0 animate-float" style={{ animationDelay: '1s' }}>
                  <div className="text-3xl font-bold text-white">45K+</div>
                  <div className="text-sm text-slate-300">Patients</div>
                </div>
                <div className="glass rounded-2xl p-6 absolute top-1/2 right-10 animate-float" style={{ animationDelay: '0.5s' }}>
                  <div className="text-3xl font-bold text-white">28</div>
                  <div className="text-sm text-slate-300">Cancer Types</div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-white py-12 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <div className="text-3xl md:text-4xl font-bold gradient-text mb-1">
                  {stat.value}
                </div>
                <div className="text-slate-600 text-sm">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              Everything You Need for
              <span className="gradient-text"> Impactful Research</span>
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              From data collection to AI-powered insights, we provide the complete platform 
              for retrospective studies and personalized medicine.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all card-hover border border-slate-100"
              >
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-slate-600">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Cancer Types */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              Comprehensive Cancer Coverage
            </h2>
            <p className="text-lg text-slate-600">
              Deep data across hematologic malignancies and solid tumors
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-3">
            {cancerTypes.map((type) => (
              <span
                key={type}
                className="px-4 py-2 bg-slate-100 rounded-full text-slate-700 text-sm font-medium hover:bg-indigo-50 hover:text-indigo-600 transition-colors cursor-pointer"
              >
                {type}
              </span>
            ))}
            <span className="px-4 py-2 bg-indigo-100 rounded-full text-indigo-600 text-sm font-medium">
              +20 more
            </span>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 hero-gradient">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to Accelerate Your Research?
          </h2>
          <p className="text-xl text-slate-300 mb-8">
            Join leading institutions already using HealthDB for breakthrough discoveries.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/marketplace"
              className="px-8 py-4 bg-white text-indigo-600 rounded-xl font-semibold text-lg hover:bg-slate-100 transition-all shadow-lg"
            >
              Browse Datasets
            </Link>
            <a
              href="mailto:demo@healthdb.ai"
              className="px-8 py-4 bg-transparent text-white border-2 border-white/30 rounded-xl font-semibold text-lg hover:bg-white/10 transition-all"
            >
              Request Demo
            </a>
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="py-16 bg-white border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8">
            <p className="text-slate-500 text-sm font-medium uppercase tracking-wider">
              Trusted by Leading Institutions
            </p>
          </div>
          <div className="flex flex-wrap justify-center items-center gap-12 opacity-50">
            {['Stanford Medicine', 'Mayo Clinic', 'MD Anderson', 'Memorial Sloan Kettering', 'Dana-Farber'].map((name) => (
              <div key={name} className="text-slate-400 font-semibold text-lg">
                {name}
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;

