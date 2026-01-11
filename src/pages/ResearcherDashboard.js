import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const API_URL = process.env.NODE_ENV === 'production' ? '' : (process.env.REACT_APP_API_URL || 'http://localhost:8000');

const ResearcherDashboard = () => {
  const [activeTab, setActiveTab] = useState('cohort');
  const [cohortCriteria, setCohortCriteria] = useState({
    cancerTypes: [],
    icdCodes: [],
    ageMin: '',
    ageMax: '',
    diseaseStages: [],
    treatmentTypes: [],
    minFollowup: '',
    dateRange: { start: '', end: '' },
  });
  const [selectedVariables, setSelectedVariables] = useState([]);
  const [cohortResult, setCohortResult] = useState(null);
  const [isBuilding, setIsBuilding] = useState(false);
  const [savedCohorts, setSavedCohorts] = useState([]);
  const [studies, setStudies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showVariableSelector, setShowVariableSelector] = useState(false);
  const navigate = useNavigate();

  // Cancer types with ICD-10 codes
  const cancerTypeOptions = [
    { name: 'Multiple Myeloma', icd: 'C90.0' },
    { name: 'DLBCL', icd: 'C83.3' },
    { name: 'AML', icd: 'C92.0' },
    { name: 'ALL', icd: 'C91.0' },
    { name: 'CLL', icd: 'C91.1' },
    { name: 'Hodgkin Lymphoma', icd: 'C81' },
    { name: 'Follicular Lymphoma', icd: 'C82' },
    { name: 'Mantle Cell Lymphoma', icd: 'C83.1' },
    { name: 'NSCLC', icd: 'C34' },
    { name: 'Breast Cancer', icd: 'C50' },
  ];

  const stageOptions = ['Stage I', 'Stage II', 'Stage III', 'Stage IV', 'Relapsed', 'Refractory', 'R-ISS I', 'R-ISS II', 'R-ISS III'];
  const treatmentOptions = [
    'Chemotherapy', 'Immunotherapy', 'CAR-T', 'Stem Cell Transplant', 
    'Radiation', 'Targeted Therapy', 'Bispecific Antibody', 'Proteasome Inhibitor',
    'IMiD', 'Anti-CD38', 'BCMA-Targeted'
  ];

  const variableCategories = {
    demographics: ['Age at diagnosis', 'Sex', 'Race/ethnicity', 'Insurance type'],
    labs: ['Hemoglobin', 'Creatinine', 'LDH', 'Beta-2 microglobulin', 'Albumin', 'Free light chains'],
    staging: ['ISS stage', 'R-ISS stage', 'Bone lesions', 'Extramedullary disease'],
    cytogenetics: ['t(4;14)', 't(14;16)', 't(11;14)', 'del(17p)', '1q gain', 'Hyperdiploidy'],
    treatments: ['Regimen name', 'Start/stop dates', 'Dose', 'Cycles completed', 'Reason for discontinuation'],
    outcomes: ['Best response', 'PFS', 'OS', 'MRD status', 'Time to next treatment'],
    toxicities: ['CRS grade', 'ICANS grade', 'Cytopenias', 'Infections', 'Neuropathy'],
  };

  const tabs = [
    { id: 'cohort', label: 'Cohort Builder' },
    { id: 'studies', label: 'My Studies' },
    { id: 'regulatory', label: 'Regulatory Status' },
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

    const fetchData = async () => {
      try {
        const [cohortsRes, studiesRes] = await Promise.all([
          fetch(`${API_URL}/api/cohort/saved`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${API_URL}/api/researcher/studies`, { headers: { Authorization: `Bearer ${token}` } }),
        ]);
        
        if (cohortsRes.ok) setSavedCohorts(await cohortsRes.json());
        if (studiesRes.ok) setStudies(await studiesRes.json());
      } catch (err) {
        console.error('Failed to fetch data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
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
          icd_codes: cohortCriteria.icdCodes.length > 0 ? cohortCriteria.icdCodes : null,
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
          institutions: data.institutions || ['OHSU Knight', 'Fred Hutch'],
          data_completeness: data.data_completeness || 0.87,
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
          criteria: cohortCriteria,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSavedCohorts(prev => [data, ...prev]);
        alert('Cohort saved successfully!');
      }
    } catch (error) {
      console.error('Failed to save cohort:', error);
    }
  };

  const toggleCancerType = (cancer) => {
    setCohortCriteria(prev => {
      const hasType = prev.cancerTypes.includes(cancer.name);
      return {
        ...prev,
        cancerTypes: hasType 
          ? prev.cancerTypes.filter(t => t !== cancer.name)
          : [...prev.cancerTypes, cancer.name],
        icdCodes: hasType
          ? prev.icdCodes.filter(c => c !== cancer.icd)
          : [...prev.icdCodes, cancer.icd],
      };
    });
  };

  const toggleCriteriaItem = (category, item) => {
    setCohortCriteria(prev => ({
      ...prev,
      [category]: prev[category].includes(item)
        ? prev[category].filter(i => i !== item)
        : [...prev[category], item],
    }));
  };

  const toggleVariable = (variable) => {
    setSelectedVariables(prev => 
      prev.includes(variable) 
        ? prev.filter(v => v !== variable)
        : [...prev, variable]
    );
  };

  // Mock studies with regulatory status
  const mockStudies = [
    {
      id: 1,
      name: 'Bispecific Ab Outcomes in R/R MM',
      status: 'in_progress',
      patient_count: 847,
      regulatory: {
        central_irb: { status: 'approved', date: '2025-01-05' },
        dua: { status: 'signed', date: '2025-01-06' },
        sites: [
          { name: 'OHSU', status: 'approved', date: '2025-01-08' },
          { name: 'Fred Hutch', status: 'pending', days: 3 },
          { name: 'Emory', status: 'not_started' },
        ],
      },
    },
  ];

  return (
    <div className="min-h-screen bg-black pt-20">
      {/* Header */}
      <section className="py-12 px-6 border-b border-white/5">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex flex-col md:flex-row md:items-end justify-between gap-6"
          >
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">Researcher Portal</p>
              <h1 className="heading-display text-4xl md:text-5xl text-white/90">Research Dashboard</h1>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <p className="text-white/40 text-xs mb-1">Active Studies</p>
                <p className="text-white font-mono text-lg">{studies.length || mockStudies.length}</p>
              </div>
              <div className="h-8 w-px bg-white/10"></div>
              <div className="text-right">
                <p className="text-white/40 text-xs mb-1">Saved Cohorts</p>
                <p className="text-white font-mono text-lg">{savedCohorts.length}</p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Tabs */}
      <section className="border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex gap-1 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-4 text-xs uppercase tracking-wider transition-colors whitespace-nowrap ${
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
          <AnimatePresence mode="wait">
            {/* COHORT BUILDER TAB */}
            {activeTab === 'cohort' && (
              <motion.div key="cohort" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="grid lg:grid-cols-3 gap-8">
                  {/* Criteria Panel */}
                  <div className="lg:col-span-2 space-y-8">
                    <div>
                      <h2 className="text-lg font-medium text-white mb-2">Build Your Cohort</h2>
                      <p className="text-white/40 text-sm">
                        Define inclusion/exclusion criteria. Results show actual de-identified patient counts.
                      </p>
                    </div>

                    {/* Inclusion Criteria */}
                    <div className="card-glass p-6">
                      <h3 className="text-sm uppercase tracking-wider text-white/40 mb-6">Inclusion Criteria</h3>
                      
                      {/* Cancer Types with ICD-10 */}
                      <div className="mb-6">
                        <label className="block text-xs text-white/50 mb-3">Diagnosis (ICD-10)</label>
                        <div className="flex flex-wrap gap-2">
                          {cancerTypeOptions.map((cancer) => (
                            <button
                              key={cancer.icd}
                              onClick={() => toggleCancerType(cancer)}
                              className={`px-3 py-1.5 text-xs transition-all flex items-center gap-2 ${
                                cohortCriteria.cancerTypes.includes(cancer.name)
                                  ? 'bg-white text-black'
                                  : 'bg-transparent text-white/50 border border-white/20 hover:border-white/40'
                              }`}
                            >
                              <span>{cancer.name}</span>
                              <span className="opacity-50">({cancer.icd})</span>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Age Range */}
                      <div className="mb-6">
                        <label className="block text-xs text-white/50 mb-3">Age Range</label>
                        <div className="flex items-center gap-4">
                          <input
                            type="number"
                            placeholder="Min"
                            value={cohortCriteria.ageMin}
                            onChange={(e) => setCohortCriteria(prev => ({ ...prev, ageMin: e.target.value }))}
                            className="w-20 px-3 py-2 bg-white/5 border border-white/10 text-white text-sm placeholder-white/30 focus:border-white/30 focus:outline-none"
                          />
                          <span className="text-white/30 text-sm">to</span>
                          <input
                            type="number"
                            placeholder="Max"
                            value={cohortCriteria.ageMax}
                            onChange={(e) => setCohortCriteria(prev => ({ ...prev, ageMax: e.target.value }))}
                            className="w-20 px-3 py-2 bg-white/5 border border-white/10 text-white text-sm placeholder-white/30 focus:border-white/30 focus:outline-none"
                          />
                        </div>
                      </div>

                      {/* Treatments */}
                      <div className="mb-6">
                        <label className="block text-xs text-white/50 mb-3">Treatment Exposure</label>
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

                      {/* Stages */}
                      <div className="mb-6">
                        <label className="block text-xs text-white/50 mb-3">Disease Stage</label>
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

                      {/* Date Range */}
                      <div className="mb-6">
                        <label className="block text-xs text-white/50 mb-3">Diagnosis Date Range</label>
                        <div className="flex items-center gap-4">
                          <input
                            type="date"
                            value={cohortCriteria.dateRange.start}
                            onChange={(e) => setCohortCriteria(prev => ({ 
                              ...prev, 
                              dateRange: { ...prev.dateRange, start: e.target.value } 
                            }))}
                            className="px-3 py-2 bg-white/5 border border-white/10 text-white text-sm focus:border-white/30 focus:outline-none"
                          />
                          <span className="text-white/30 text-sm">to</span>
                          <input
                            type="date"
                            value={cohortCriteria.dateRange.end}
                            onChange={(e) => setCohortCriteria(prev => ({ 
                              ...prev, 
                              dateRange: { ...prev.dateRange, end: e.target.value } 
                            }))}
                            className="px-3 py-2 bg-white/5 border border-white/10 text-white text-sm focus:border-white/30 focus:outline-none"
                          />
                        </div>
                      </div>

                      {/* Min Follow-up */}
                      <div>
                        <label className="block text-xs text-white/50 mb-3">Minimum Follow-up</label>
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            placeholder="e.g., 12"
                            value={cohortCriteria.minFollowup}
                            onChange={(e) => setCohortCriteria(prev => ({ ...prev, minFollowup: e.target.value }))}
                            className="w-20 px-3 py-2 bg-white/5 border border-white/10 text-white text-sm placeholder-white/30 focus:border-white/30 focus:outline-none"
                          />
                          <span className="text-white/30 text-sm">months</span>
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-4">
                      <button
                        onClick={handleBuildCohort}
                        disabled={isBuilding}
                        className="px-8 py-4 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors disabled:opacity-50"
                      >
                        {isBuilding ? 'Running Query...' : 'Run Feasibility'}
                      </button>
                      {cohortResult && cohortResult.patient_count > 0 && (
                        <button
                          onClick={() => setShowVariableSelector(true)}
                          className="px-8 py-4 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white/5 transition-colors"
                        >
                          Select Variables →
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Results Panel */}
                  <div className="lg:col-span-1">
                    <div className="card-glass p-6 sticky top-24">
                      <h3 className="text-lg font-medium text-white mb-6">Feasibility Results</h3>
                      
                      {cohortResult ? (
                        <div className="space-y-6">
                          <div>
                            <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Eligible Patients</p>
                            <p className="text-4xl font-light text-white font-mono">
                              {cohortResult.patient_count.toLocaleString()}
                            </p>
                            <p className="text-white/30 text-sm mt-1">
                              across {cohortResult.institutions.length} institutions
                            </p>
                          </div>

                          <div>
                            <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Data Completeness</p>
                            <div className="flex items-center gap-3">
                              <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-[#00d4aa]" 
                                  style={{ width: `${cohortResult.data_completeness * 100}%` }}
                                />
                              </div>
                              <span className="text-[#00d4aa] font-mono text-sm">
                                {Math.round(cohortResult.data_completeness * 100)}%
                              </span>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-3">
                            {cohortResult.institutions.map((inst) => (
                              <div key={inst} className="card-glass p-3 text-center">
                                <p className="text-white/60 text-xs">{inst}</p>
                              </div>
                            ))}
                          </div>

                          <div className="pt-4 border-t border-white/10 space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-white/40">Diagnoses</span>
                              <span className="text-white font-mono">{cohortResult.diagnosis_count}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-white/40">Treatments</span>
                              <span className="text-white font-mono">{cohortResult.treatment_count}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-white/40">Molecular</span>
                              <span className="text-white font-mono">{cohortResult.molecular_count}</span>
                            </div>
                          </div>

                          {cohortResult.patient_count > 0 && (
                            <div className="pt-4 space-y-3">
                              <button 
                                onClick={handleSaveCohort}
                                className="w-full py-3 bg-[#00d4aa] text-black text-xs uppercase tracking-wider font-medium hover:bg-[#00d4aa]/90 transition-colors"
                              >
                                Save Cohort
                              </button>
                              <button 
                                className="w-full py-3 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white/5 transition-colors"
                              >
                                Submit for IRB
                              </button>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-center py-8">
                          <p className="text-white/30 text-sm">
                            Define criteria and run feasibility to see patient counts
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* STUDIES TAB */}
            {activeTab === 'studies' && (
              <motion.div key="studies" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="flex items-center justify-between mb-8">
                  <div>
                    <h2 className="text-lg font-medium text-white mb-2">My Studies</h2>
                    <p className="text-white/40 text-sm">Track your research studies and saved cohorts</p>
                  </div>
                  <button className="px-6 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors">
                    + New Study
                  </button>
                </div>
                
                {loading ? (
                  <div className="text-center py-12">
                    <div className="w-8 h-8 border border-white/20 border-t-white/60 rounded-full animate-spin mx-auto mb-4"></div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Active Studies */}
                    {mockStudies.map((study) => (
                      <div key={study.id} className="card-glass p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="text-white font-medium">{study.name}</h3>
                              <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-400 uppercase">
                                {study.status.replace('_', ' ')}
                              </span>
                            </div>
                            <p className="text-white/40 text-sm">{study.patient_count} patients</p>
                          </div>
                          <button className="px-4 py-2 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white hover:text-black transition-all">
                            View Details
                          </button>
                        </div>
                        
                        {/* Regulatory Quick Status */}
                        <div className="pt-4 border-t border-white/10">
                          <p className="text-white/40 text-xs uppercase tracking-wider mb-3">Regulatory Status</p>
                          <div className="flex flex-wrap gap-4">
                            <div className="flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-[#00d4aa]"></span>
                              <span className="text-white/60 text-sm">Central IRB</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-[#00d4aa]"></span>
                              <span className="text-white/60 text-sm">DUA</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                              <span className="text-white/60 text-sm">Site Approvals (1/3)</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}

                    {/* Saved Cohorts */}
                    <h3 className="text-white/40 text-xs uppercase tracking-wider pt-8 pb-4">Saved Cohorts</h3>
                    {savedCohorts.length > 0 ? (
                      savedCohorts.map((cohort) => (
                        <div key={cohort.id} className="card-glass card-hover p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="text-white font-medium">{cohort.name}</h4>
                              <p className="text-white/40 text-sm">{cohort.description}</p>
                            </div>
                            <div className="flex items-center gap-4">
                              <span className="text-white font-mono">{cohort.patient_count} pts</span>
                              <button className="px-3 py-1 border border-white/20 text-white/60 text-xs hover:bg-white hover:text-black transition-all">
                                Convert to Study
                              </button>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="card-glass p-8 text-center">
                        <p className="text-white/40">No saved cohorts yet</p>
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            )}

            {/* REGULATORY TAB */}
            {activeTab === 'regulatory' && (
              <motion.div key="regulatory" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="mb-8">
                  <h2 className="text-lg font-medium text-white mb-2">Regulatory Dashboard</h2>
                  <p className="text-white/40 text-sm">Track IRB approvals, DUAs, and site authorizations</p>
                </div>

                {/* Study: Bispecific Ab Outcomes */}
                <div className="card-glass p-6 mb-6">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-white font-medium text-lg">Bispecific Ab Outcomes in R/R MM</h3>
                      <p className="text-white/40 text-sm">847 patients • 3 sites</p>
                    </div>
                    <div className="flex gap-3">
                      <button className="px-4 py-2 border border-white/20 text-white/60 text-xs uppercase hover:bg-white/5 transition-colors">
                        Download IRB Protocol
                      </button>
                      <button className="px-4 py-2 border border-white/20 text-white/60 text-xs uppercase hover:bg-white/5 transition-colors">
                        Download DUA
                      </button>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {/* Central IRB */}
                    <div className="flex items-center justify-between py-3 border-b border-white/5">
                      <div className="flex items-center gap-4">
                        <span className="w-8 h-8 rounded-full bg-[#00d4aa]/20 text-[#00d4aa] flex items-center justify-center">✓</span>
                        <div>
                          <p className="text-white font-medium">Central IRB (HealthDB sIRB)</p>
                          <p className="text-white/40 text-sm">Protocol #HDB-2025-001</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="px-3 py-1 bg-[#00d4aa]/20 text-[#00d4aa] text-xs uppercase">Approved</span>
                        <p className="text-white/30 text-xs mt-1">Jan 5, 2025</p>
                      </div>
                    </div>

                    {/* DUA */}
                    <div className="flex items-center justify-between py-3 border-b border-white/5">
                      <div className="flex items-center gap-4">
                        <span className="w-8 h-8 rounded-full bg-[#00d4aa]/20 text-[#00d4aa] flex items-center justify-center">✓</span>
                        <div>
                          <p className="text-white font-medium">Data Use Agreement</p>
                          <p className="text-white/40 text-sm">Auto-generated template</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="px-3 py-1 bg-[#00d4aa]/20 text-[#00d4aa] text-xs uppercase">Signed</span>
                        <p className="text-white/30 text-xs mt-1">Jan 6, 2025</p>
                      </div>
                    </div>

                    {/* Site: OHSU */}
                    <div className="flex items-center justify-between py-3 border-b border-white/5">
                      <div className="flex items-center gap-4">
                        <span className="w-8 h-8 rounded-full bg-[#00d4aa]/20 text-[#00d4aa] flex items-center justify-center">✓</span>
                        <div>
                          <p className="text-white font-medium">OHSU Knight Cancer Institute</p>
                          <p className="text-white/40 text-sm">Reliance Agreement</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="px-3 py-1 bg-[#00d4aa]/20 text-[#00d4aa] text-xs uppercase">Approved</span>
                        <p className="text-white/30 text-xs mt-1">Jan 8, 2025</p>
                      </div>
                    </div>

                    {/* Site: Fred Hutch */}
                    <div className="flex items-center justify-between py-3 border-b border-white/5">
                      <div className="flex items-center gap-4">
                        <span className="w-8 h-8 rounded-full bg-amber-500/20 text-amber-500 flex items-center justify-center animate-pulse">◐</span>
                        <div>
                          <p className="text-white font-medium">Fred Hutchinson Cancer Center</p>
                          <p className="text-white/40 text-sm">Reliance Agreement</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="px-3 py-1 bg-amber-500/20 text-amber-500 text-xs uppercase">Pending</span>
                        <p className="text-white/30 text-xs mt-1">~3 days remaining</p>
                      </div>
                    </div>

                    {/* Site: Emory */}
                    <div className="flex items-center justify-between py-3">
                      <div className="flex items-center gap-4">
                        <span className="w-8 h-8 rounded-full bg-white/10 text-white/40 flex items-center justify-center">○</span>
                        <div>
                          <p className="text-white font-medium">Emory Winship Cancer Institute</p>
                          <p className="text-white/40 text-sm">Reliance Agreement</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="px-3 py-1 bg-white/10 text-white/40 text-xs uppercase">Not Started</span>
                        <button className="block text-[#00d4aa] text-xs mt-1 hover:underline">Initiate →</button>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 pt-6 border-t border-white/10 flex justify-between items-center">
                    <p className="text-white/40 text-sm">Estimated time to data access: <span className="text-white">~1 week</span></p>
                    <button className="px-4 py-2 bg-[#00d4aa] text-black text-xs uppercase tracking-wider font-medium hover:bg-[#00d4aa]/90 transition-colors">
                      Send Reminder to Pending Sites
                    </button>
                  </div>
                </div>

                {/* Resources */}
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="card-glass p-4 card-hover cursor-pointer">
                    <p className="text-white font-medium mb-1">📋 IRB Protocol Templates</p>
                    <p className="text-white/40 text-sm">Pre-approved templates for common study types</p>
                  </div>
                  <div className="card-glass p-4 card-hover cursor-pointer">
                    <p className="text-white font-medium mb-1">📝 DUA Library</p>
                    <p className="text-white/40 text-sm">Institution-specific data use agreements</p>
                  </div>
                  <div className="card-glass p-4 card-hover cursor-pointer">
                    <p className="text-white font-medium mb-1">🔗 Reliance Agreements</p>
                    <p className="text-white/40 text-sm">Pre-negotiated with 8 institutions</p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      {/* Variable Selector Modal */}
      <AnimatePresence>
        {showVariableSelector && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowVariableSelector(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-black border border-white/10 max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-white/10 flex items-center justify-between">
                <div>
                  <h2 className="text-xl text-white">Select Variables</h2>
                  <p className="text-white/40 text-sm mt-1">{selectedVariables.length} variables selected</p>
                </div>
                <button onClick={() => setShowVariableSelector(false)} className="p-2 hover:bg-white/10">
                  <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {Object.entries(variableCategories).map(([category, variables]) => (
                    <div key={category}>
                      <h3 className="text-sm uppercase tracking-wider text-white/40 mb-3">
                        {category.replace(/_/g, ' ')}
                      </h3>
                      <div className="space-y-2">
                        {variables.map((variable) => (
                          <label 
                            key={variable} 
                            className="flex items-center gap-3 cursor-pointer group"
                          >
                            <input
                              type="checkbox"
                              checked={selectedVariables.includes(variable)}
                              onChange={() => toggleVariable(variable)}
                              className="w-4 h-4 rounded border-white/20 bg-white/5 text-[#00d4aa] focus:ring-[#00d4aa] focus:ring-offset-0"
                            />
                            <span className="text-white/60 text-sm group-hover:text-white transition-colors">
                              {variable}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="p-6 border-t border-white/10 flex justify-between">
                <button
                  onClick={() => setSelectedVariables(Object.values(variableCategories).flat())}
                  className="text-white/40 text-sm hover:text-white transition-colors"
                >
                  Select All
                </button>
                <div className="flex gap-4">
                  <button
                    onClick={() => setShowVariableSelector(false)}
                    className="px-6 py-3 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white/5 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => setShowVariableSelector(false)}
                    className="px-6 py-3 bg-[#00d4aa] text-black text-xs uppercase tracking-wider font-medium hover:bg-[#00d4aa]/90 transition-colors"
                  >
                    Confirm Selection
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ResearcherDashboard;
