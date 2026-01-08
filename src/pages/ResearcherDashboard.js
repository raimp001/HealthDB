import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

// Use relative URL in production (same origin), fallback to localhost in dev
const API_URL = process.env.NODE_ENV === 'production' ? '' : (process.env.REACT_APP_API_URL || 'http://localhost:8000');

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
  const [savedCohorts, setSavedCohorts] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const cancerTypeOptions = [
    'DLBCL', 'AML', 'ALL', 'CLL', 'Multiple Myeloma', 'Hodgkin Lymphoma',
    'Follicular Lymphoma', 'Mantle Cell Lymphoma', 'NSCLC', 'Breast Cancer',
  ];

  const stageOptions = ['Stage I', 'Stage II', 'Stage III', 'Stage IV', 'Relapsed', 'Refractory'];
  const treatmentOptions = ['Chemotherapy', 'Immunotherapy', 'CAR-T', 'Stem Cell Transplant', 'Radiation', 'Targeted Therapy'];

  const tabs = [
    { id: 'cohort', label: 'Cohort Builder' },
    { id: 'studies', label: 'Saved Cohorts' },
  ];

  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    if (!token) {
      navigate('/login');
      return;
    }

    if (user.user_type === 'patient') {
      navigate('/patient');
      return;
    }

    // Fetch saved cohorts
    const fetchCohorts = async () => {
      try {
        const response = await fetch(`${API_URL}/api/cohort/saved`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (response.ok) {
          const data = await response.json();
          setSavedCohorts(data);
        }
      } catch (err) {
        console.error('Failed to fetch cohorts:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCohorts();
  }, [navigate]);

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
          cancer_types: cohortCriteria.cancerTypes.length > 0 ? cohortCriteria.cancerTypes : null,
          stages: cohortCriteria.diseaseStages.length > 0 ? cohortCriteria.diseaseStages : null,
          age_min: cohortCriteria.ageMin ? parseInt(cohortCriteria.ageMin) : null,
          age_max: cohortCriteria.ageMax ? parseInt(cohortCriteria.ageMax) : null,
          treatment_types: cohortCriteria.treatmentTypes.length > 0 ? cohortCriteria.treatmentTypes : null,
          min_follow_up_months: cohortCriteria.minFollowup ? parseInt(cohortCriteria.minFollowup) : null,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCohortResult({
          patient_count: data.patient_count,
          data_points: data.data_points,
          diagnosis_count: data.diagnosis_count,
          treatment_count: data.treatment_count,
          molecular_count: data.molecular_count,
          criteria: cohortCriteria,
        });
      } else {
        const errorData = await response.json();
        alert(`Failed to build cohort: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to build cohort:', error);
      alert('Failed to build cohort. Please try again.');
    } finally {
      setIsBuilding(false);
    }
  };

  const handleSaveCohort = async () => {
    if (!cohortResult) return;

    const name = prompt('Enter a name for this cohort:');
    if (!name) return;

    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`${API_URL}/api/cohort/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          description: `Cancer types: ${cohortCriteria.cancerTypes.join(', ') || 'Any'}`,
          criteria: {
            cancer_types: cohortCriteria.cancerTypes.length > 0 ? cohortCriteria.cancerTypes : null,
            stages: cohortCriteria.diseaseStages.length > 0 ? cohortCriteria.diseaseStages : null,
            age_min: cohortCriteria.ageMin ? parseInt(cohortCriteria.ageMin) : null,
            age_max: cohortCriteria.ageMax ? parseInt(cohortCriteria.ageMax) : null,
            treatment_types: cohortCriteria.treatmentTypes.length > 0 ? cohortCriteria.treatmentTypes : null,
          },
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSavedCohorts(prev => [data, ...prev]);
        alert('Cohort saved successfully!');
      }
    } catch (error) {
      console.error('Failed to save cohort:', error);
      alert('Failed to save cohort. Please try again.');
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
                      Results reflect actual de-identified data in the platform.
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
                            {cohortResult.patient_count.toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Total Data Points</p>
                          <p className="text-2xl font-light text-white font-mono">
                            {cohortResult.data_points.toLocaleString()}
                          </p>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-center">
                          <div className="card-glass p-3">
                            <p className="text-white/40 text-xs mb-1">Diagnoses</p>
                            <p className="text-white font-mono">{cohortResult.diagnosis_count}</p>
                          </div>
                          <div className="card-glass p-3">
                            <p className="text-white/40 text-xs mb-1">Treatments</p>
                            <p className="text-white font-mono">{cohortResult.treatment_count}</p>
                          </div>
                          <div className="card-glass p-3">
                            <p className="text-white/40 text-xs mb-1">Molecular</p>
                            <p className="text-white font-mono">{cohortResult.molecular_count}</p>
                          </div>
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
                            {cohortResult.criteria.diseaseStages.length > 0 && (
                              <p className="text-white/60 text-sm">
                                Stages: {cohortResult.criteria.diseaseStages.join(', ')}
                              </p>
                            )}
                          </div>
                        </div>
                        {cohortResult.patient_count > 0 && (
                          <button 
                            onClick={handleSaveCohort}
                            className="w-full py-3 bg-[#00d4aa] text-black text-xs uppercase tracking-wider font-medium hover:bg-[#00d4aa]/90 transition-colors"
                          >
                            Save Cohort
                          </button>
                        )}
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
              <h2 className="text-lg font-medium text-white mb-6">Saved Cohorts</h2>
              
              {loading ? (
                <div className="text-center py-12">
                  <div className="w-8 h-8 border border-white/20 border-t-white/60 rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-white/40 text-sm">Loading...</p>
                </div>
              ) : savedCohorts.length > 0 ? (
                <div className="space-y-px">
                  {savedCohorts.map((cohort) => (
                    <div key={cohort.id} className="card-glass card-hover p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-white font-medium mb-1">{cohort.name}</h3>
                          <p className="text-white/40 text-sm">
                            {cohort.description || 'No description'}
                          </p>
                          <p className="text-white/30 text-xs mt-2">
                            Created {new Date(cohort.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <p className="text-white/30 text-xs">Patients</p>
                            <p className="text-white font-mono">{cohort.patient_count}</p>
                          </div>
                          <button className="px-4 py-2 border border-white/20 text-white/60 text-xs uppercase tracking-wider hover:bg-white hover:text-black transition-all">
                            View
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="card-glass p-12 text-center">
                  <p className="text-white/40 mb-4">No saved cohorts yet</p>
                  <p className="text-white/30 text-sm mb-6">
                    Build a cohort using the Cohort Builder and save it to access it here.
                  </p>
                  <button
                    onClick={() => setActiveTab('cohort')}
                    className="px-6 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors"
                  >
                    Build Cohort
                  </button>
                </div>
              )}
            </motion.div>
          )}
        </div>
      </section>
    </div>
  );
};

export default ResearcherDashboard;
