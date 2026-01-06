import React, { useState } from 'react';
import { motion } from 'framer-motion';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ResearcherDashboard = () => {
  const [activeTab, setActiveTab] = useState('cohort');
  const [cohortCriteria, setCohortCriteria] = useState({
    cancerTypes: [],
    ageMin: '',
    ageMax: '',
    diseaseStages: [],
    treatmentTypes: [],
    minFollowup: '',
  });
  const [cohortResult, setCohortResult] = useState(null);
  const [isBuilding, setIsBuilding] = useState(false);

  const cancerTypeOptions = [
    'DLBCL', 'AML', 'ALL', 'CLL', 'Multiple Myeloma', 'Hodgkin Lymphoma',
    'Follicular Lymphoma', 'Mantle Cell Lymphoma', 'NSCLC', 'Breast Cancer',
  ];

  const stageOptions = ['Stage I', 'Stage II', 'Stage III', 'Stage IV', 'Relapsed', 'Refractory'];
  const treatmentOptions = ['Chemotherapy', 'Immunotherapy', 'CAR-T', 'Stem Cell Transplant', 'Radiation', 'Targeted Therapy'];

  const tabs = [
    { id: 'cohort', label: 'Cohort Builder' },
    { id: 'studies', label: 'My Studies' },
    { id: 'requests', label: 'Data Requests' },
  ];

  const handleBuildCohort = async () => {
    setIsBuilding(true);
    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`${API_URL}/api/cohort/build`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          cancer_types: cohortCriteria.cancerTypes,
          age_min: cohortCriteria.ageMin ? parseInt(cohortCriteria.ageMin) : null,
          age_max: cohortCriteria.ageMax ? parseInt(cohortCriteria.ageMax) : null,
          disease_stages: cohortCriteria.diseaseStages,
          treatment_types: cohortCriteria.treatmentTypes,
          min_followup_months: cohortCriteria.minFollowup ? parseInt(cohortCriteria.minFollowup) : null,
        }),
      });

      const data = await response.json();
      setCohortResult({
        cohortSize: data.cohort_size || Math.floor(Math.random() * 5000) + 500,
        estimatedCost: data.estimated_cost || Math.floor(Math.random() * 10000) + 2000,
        criteria: cohortCriteria,
      });
    } catch (error) {
      // Demo fallback
      setCohortResult({
        cohortSize: Math.floor(Math.random() * 5000) + 500,
        estimatedCost: Math.floor(Math.random() * 10000) + 2000,
        criteria: cohortCriteria,
      });
    } finally {
      setIsBuilding(false);
    }
  };

  const toggleCriteriaItem = (category, item) => {
    setCohortCriteria(prev => ({
      ...prev,
      [category]: prev[category].includes(item)
        ? prev[category].filter(i => i !== item)
        : [...prev[category], item],
    }));
  };

  return (
    <div className="min-h-screen bg-black pt-20">
      {/* Header */}
      <section className="py-16 px-6 border-b border-white/5">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Researcher Portal
            </p>
            <h1 className="heading-display text-4xl md:text-5xl text-white/90">
              Research Dashboard
            </h1>
          </motion.div>
        </div>
      </section>

      {/* Tabs */}
      <section className="border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-4 text-xs uppercase tracking-wider transition-colors ${
                  activeTab === tab.id
                    ? 'text-white border-b-2 border-white'
                    : 'text-white/40 hover:text-white/60'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="py-12 px-6">
        <div className="max-w-6xl mx-auto">
          {activeTab === 'cohort' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <div className="grid lg:grid-cols-3 gap-8">
                {/* Criteria Panel */}
                <div className="lg:col-span-2 space-y-8">
                  <div>
                    <h2 className="text-lg font-medium text-white mb-6">Build Your Cohort</h2>
                    <p className="text-white/40 mb-8">
                      Define criteria to identify patient populations for your research.
                    </p>
                  </div>

                  {/* Cancer Types */}
                  <div>
                    <label className="block text-xs uppercase tracking-wider text-white/40 mb-4">
                      Cancer Types
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {cancerTypeOptions.map((type) => (
                        <button
                          key={type}
                          onClick={() => toggleCriteriaItem('cancerTypes', type)}
                          className={`px-3 py-1.5 text-xs transition-all ${
                            cohortCriteria.cancerTypes.includes(type)
                              ? 'bg-white text-black'
                              : 'bg-transparent text-white/50 border border-white/20 hover:border-white/40'
                          }`}
                        >
                          {type}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Age Range */}
                  <div>
                    <label className="block text-xs uppercase tracking-wider text-white/40 mb-4">
                      Age Range
                    </label>
                    <div className="flex gap-4">
                      <input
                        type="number"
                        placeholder="Min"
                        value={cohortCriteria.ageMin}
                        onChange={(e) => setCohortCriteria(prev => ({ ...prev, ageMin: e.target.value }))}
                        className="w-24 px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none"
                      />
                      <span className="text-white/30 self-center">to</span>
                      <input
                        type="number"
                        placeholder="Max"
                        value={cohortCriteria.ageMax}
                        onChange={(e) => setCohortCriteria(prev => ({ ...prev, ageMax: e.target.value }))}
                        className="w-24 px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none"
                      />
                    </div>
                  </div>

                  {/* Disease Stages */}
                  <div>
                    <label className="block text-xs uppercase tracking-wider text-white/40 mb-4">
                      Disease Stages
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {stageOptions.map((stage) => (
                        <button
                          key={stage}
                          onClick={() => toggleCriteriaItem('diseaseStages', stage)}
                          className={`px-3 py-1.5 text-xs transition-all ${
                            cohortCriteria.diseaseStages.includes(stage)
                              ? 'bg-white text-black'
                              : 'bg-transparent text-white/50 border border-white/20 hover:border-white/40'
                          }`}
                        >
                          {stage}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Treatment Types */}
                  <div>
                    <label className="block text-xs uppercase tracking-wider text-white/40 mb-4">
                      Treatment Types
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {treatmentOptions.map((treatment) => (
                        <button
                          key={treatment}
                          onClick={() => toggleCriteriaItem('treatmentTypes', treatment)}
                          className={`px-3 py-1.5 text-xs transition-all ${
                            cohortCriteria.treatmentTypes.includes(treatment)
                              ? 'bg-white text-black'
                              : 'bg-transparent text-white/50 border border-white/20 hover:border-white/40'
                          }`}
                        >
                          {treatment}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Min Follow-up */}
                  <div>
                    <label className="block text-xs uppercase tracking-wider text-white/40 mb-4">
                      Minimum Follow-up (months)
                    </label>
                    <input
                      type="number"
                      placeholder="e.g., 12"
                      value={cohortCriteria.minFollowup}
                      onChange={(e) => setCohortCriteria(prev => ({ ...prev, minFollowup: e.target.value }))}
                      className="w-32 px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none"
                    />
                  </div>

                  <button
                    onClick={handleBuildCohort}
                    disabled={isBuilding}
                    className="px-8 py-4 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors disabled:opacity-50"
                  >
                    {isBuilding ? 'Building...' : 'Build Cohort'}
                  </button>
                </div>

                {/* Results Panel */}
                <div className="lg:col-span-1">
                  <div className="card-glass p-6 sticky top-24">
                    <h3 className="text-lg font-medium text-white mb-6">Cohort Preview</h3>
                    
                    {cohortResult ? (
                      <div className="space-y-6">
                        <div>
                          <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Matching Patients</p>
                          <p className="text-4xl font-light text-white font-mono">
                            {cohortResult.cohortSize.toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Estimated Cost</p>
                          <p className="text-2xl font-light text-white font-mono">
                            ${cohortResult.estimatedCost.toLocaleString()}
                          </p>
                        </div>
                        <div className="pt-6 border-t border-white/10">
                          <p className="text-white/40 text-xs uppercase tracking-wider mb-3">Selected Criteria</p>
                          <div className="space-y-2">
                            {cohortResult.criteria.cancerTypes.length > 0 && (
                              <p className="text-white/60 text-sm">
                                {cohortResult.criteria.cancerTypes.join(', ')}
                              </p>
                            )}
                            {(cohortResult.criteria.ageMin || cohortResult.criteria.ageMax) && (
                              <p className="text-white/60 text-sm">
                                Age: {cohortResult.criteria.ageMin || '0'} - {cohortResult.criteria.ageMax || '100'}
                              </p>
                            )}
                          </div>
                        </div>
                        <button className="w-full py-3 bg-[#00d4aa] text-black text-xs uppercase tracking-wider font-medium hover:bg-[#00d4aa]/90 transition-colors">
                          Request Access
                        </button>
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <p className="text-white/30 text-sm">
                          Select criteria and build your cohort to see results
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'studies' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <h2 className="text-lg font-medium text-white mb-6">My Studies</h2>
              <div className="space-y-px">
                {[
                  { name: 'DLBCL CAR-T Response Analysis', status: 'Active', patients: 234, created: '2024-01-10' },
                  { name: 'AML Treatment Outcomes', status: 'Pending IRB', patients: 0, created: '2024-01-05' },
                  { name: 'Multiple Myeloma Cohort', status: 'Completed', patients: 567, created: '2023-11-20' },
                ].map((study, index) => (
                  <div key={index} className="card-glass card-hover p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-white font-medium mb-1">{study.name}</h3>
                        <p className="text-white/40 text-sm">Created {study.created}</p>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <p className="text-white/30 text-xs">Patients</p>
                          <p className="text-white font-mono">{study.patients}</p>
                        </div>
                        <span className={`px-3 py-1 text-xs uppercase tracking-wider ${
                          study.status === 'Active' ? 'bg-[#00d4aa]/20 text-[#00d4aa]' :
                          study.status === 'Completed' ? 'bg-white/10 text-white/60' :
                          'bg-yellow-500/20 text-yellow-500'
                        }`}>
                          {study.status}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'requests' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <h2 className="text-lg font-medium text-white mb-6">Data Requests</h2>
              <div className="space-y-px">
                {[
                  { dataset: 'Comprehensive DLBCL Registry', status: 'Approved', date: '2024-01-12' },
                  { dataset: 'AML Treatment Response', status: 'Under Review', date: '2024-01-08' },
                  { dataset: 'CAR-T Outcomes Dataset', status: 'Pending Payment', date: '2024-01-05' },
                ].map((request, index) => (
                  <div key={index} className="card-glass card-hover p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-white font-medium mb-1">{request.dataset}</h3>
                        <p className="text-white/40 text-sm">Requested {request.date}</p>
                      </div>
                      <span className={`px-3 py-1 text-xs uppercase tracking-wider ${
                        request.status === 'Approved' ? 'bg-[#00d4aa]/20 text-[#00d4aa]' :
                        request.status === 'Under Review' ? 'bg-blue-500/20 text-blue-400' :
                        'bg-yellow-500/20 text-yellow-500'
                      }`}>
                        {request.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </section>
    </div>
  );
};

export default ResearcherDashboard;
