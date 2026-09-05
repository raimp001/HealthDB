import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

import { API_URL } from '../lib/api';

const CohortBuilder = () => {
  const [step, setStep] = useState(1);
  const [studyName, setStudyName] = useState('');
  const [inclusions, setInclusions] = useState([]);
  const [exclusions, setExclusions] = useState([]);
  const [selectedVars, setSelectedVars] = useState({});
  const [feasibilityRun, setFeasibilityRun] = useState(false);
  const [cohortResult, setCohortResult] = useState(null);
  const [institutions, setInstitutions] = useState([]);
  const [queryError, setQueryError] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [showAddRule, setShowAddRule] = useState(null); // 'inclusion' or 'exclusion'
  const [newRule, setNewRule] = useState({ field: '', operator: 'IS', value: '' });
  const [outputFormat, setOutputFormat] = useState('csv');
  const [deidentLevel, setDeidentLevel] = useState('limited_dataset');
  const [extracting, setExtracting] = useState(false);

  // Field definitions with operators and values
  const fieldDefinitions = {
    diagnosis: {
      label: 'Diagnosis',
      operators: ['IS', 'IS NOT', 'INCLUDES'],
      values: [
        'Multiple Myeloma (C90.0)',
        'DLBCL (C83.3)',
        'AML (C92.0)',
        'CLL (C91.1)',
        'Hodgkin Lymphoma (C81.x)',
        'Follicular Lymphoma (C82.x)',
        'Mantle Cell Lymphoma (C83.1)'
      ]
    },
    stage: {
      label: 'Stage',
      operators: ['IS', 'IS NOT', 'IN'],
      values: ['I', 'II', 'III', 'IV', 'ISS I', 'ISS II', 'ISS III', 'R-ISS I', 'R-ISS II', 'R-ISS III']
    },
    treatment: {
      label: 'Treatment',
      operators: ['INCLUDES', 'EXCLUDES', 'IS'],
      values: [
        'Bispecific antibody',
        'CAR-T therapy',
        'Stem cell transplant',
        'Lenalidomide',
        'Bortezomib',
        'Daratumumab',
        'Chemotherapy',
        'Radiation',
        'Immunotherapy'
      ]
    },
    line_of_therapy: {
      label: 'Line of Therapy',
      operators: ['=', '>=', '<=', '>'],
      values: ['1', '2', '3', '4', '5+']
    },
    age: {
      label: 'Age at Diagnosis',
      operators: ['>=', '<=', '>', '<', 'BETWEEN'],
      values: ['18', '40', '50', '60', '65', '70', '75', '80']
    },
    sex: {
      label: 'Sex',
      operators: ['IS'],
      values: ['Male', 'Female']
    },
    ecog: {
      label: 'ECOG Status',
      operators: ['=', '<=', '>='],
      values: ['0', '1', '2', '3', '4']
    },
    prior_cart: {
      label: 'Prior CAR-T',
      operators: ['IS'],
      values: ['TRUE', 'FALSE']
    },
    prior_transplant: {
      label: 'Prior Transplant',
      operators: ['IS'],
      values: ['TRUE', 'FALSE', 'Autologous', 'Allogeneic']
    },
    cytogenetics: {
      label: 'Cytogenetics',
      operators: ['INCLUDES', 'EXCLUDES'],
      values: ['del(17p)', 't(4;14)', 't(14;16)', 'gain(1q)', 't(11;14)', 'High Risk', 'Standard Risk']
    },
    response: {
      label: 'Best Response',
      operators: ['IS', 'IN', 'AT LEAST'],
      values: ['sCR', 'CR', 'VGPR', 'PR', 'MR', 'SD', 'PD']
    },
    mrd: {
      label: 'MRD Status',
      operators: ['IS'],
      values: ['Negative', 'Positive', 'Unknown']
    },
    follow_up: {
      label: 'Minimum Follow-up',
      operators: ['>='],
      values: ['6 months', '12 months', '24 months', '36 months']
    }
  };

  // Query templates: one-click starting criteria. These fill the query form only;
  // they carry no data of their own.
  const diseasePresets = [
    {
      name: 'Multiple Myeloma Registry',
      inclusions: [{ field: 'diagnosis', operator: 'IS', value: 'Multiple Myeloma (C90.0)' }],
      exclusions: []
    },
    {
      name: 'CAR-T Outcomes',
      inclusions: [{ field: 'treatment', operator: 'INCLUDES', value: 'CAR-T therapy' }],
      exclusions: []
    },
    {
      name: 'Bispecific Antibody Study',
      inclusions: [
        { field: 'diagnosis', operator: 'IS', value: 'Multiple Myeloma (C90.0)' },
        { field: 'treatment', operator: 'INCLUDES', value: 'Bispecific antibody' }
      ],
      exclusions: [{ field: 'prior_cart', operator: 'IS', value: 'TRUE', enabled: true }]
    }
  ];

  // Variable inventory, measured from the records consented patients actually
  // contributed. Loaded from the API — nothing here is assumed or estimated.
  const [variableInventory, setVariableInventory] = useState(null);
  const [inventoryError, setInventoryError] = useState(null);

  // Real study + regulatory state, loaded from the API.
  const [studies, setStudies] = useState([]);
  const [activeStudyId, setActiveStudyId] = useState('');
  const [siteData, setSiteData] = useState(null);
  const [regBusy, setRegBusy] = useState(false);
  const [regError, setRegError] = useState(null);
  const [extractJob, setExtractJob] = useState(null);
  const [extractError, setExtractError] = useState(null);

  const steps = ['Define Cohort', 'Select Variables', 'Regulatory', 'Extract'];

  // Add rule
  const addRule = (type) => {
    if (!newRule.field || !newRule.value) return;
    
    const rule = {
      id: Date.now(),
      field: newRule.field,
      operator: newRule.operator,
      value: newRule.value,
      enabled: true
    };

    if (type === 'inclusion') {
      setInclusions([...inclusions, rule]);
    } else {
      setExclusions([...exclusions, rule]);
    }
    
    setNewRule({ field: '', operator: 'IS', value: '' });
    setShowAddRule(null);
  };

  // Remove rule
  const removeRule = (type, id) => {
    if (type === 'inclusion') {
      setInclusions(inclusions.filter(r => r.id !== id));
    } else {
      setExclusions(exclusions.filter(r => r.id !== id));
    }
  };

  // Apply preset
  const applyPreset = (preset) => {
    setInclusions(preset.inclusions.map((r, i) => ({ ...r, id: i + 1 })));
    setExclusions(preset.exclusions.map((r, i) => ({ ...r, id: i + 1 })));
    setStudyName(preset.name);
  };

  const authHeaders = () => {
    const token = sessionStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  // Load the directory of institutions a study can be filed with
  useEffect(() => {
    fetch(`${API_URL}/api/institutions`)
      .then(res => (res.ok ? res.json() : []))
      .then(setInstitutions)
      .catch(() => setInstitutions([]));
  }, []);

  // Load the measured variable inventory and the researcher's real studies
  useEffect(() => {
    if (!sessionStorage.getItem('token')) {
      setInventoryError('Sign in as a researcher to load the variable inventory.');
      return;
    }
    fetch(`${API_URL}/api/cohort/variables`, { headers: authHeaders() })
      .then(async res => {
        if (!res.ok) throw new Error((await res.json()).detail || 'Failed to load variables');
        return res.json();
      })
      .then(data => { setVariableInventory(data); setInventoryError(null); })
      .catch(err => setInventoryError(err.message));

    fetch(`${API_URL}/api/researcher/studies`, { headers: authHeaders() })
      .then(res => (res.ok ? res.json() : []))
      .then(list => {
        setStudies(list);
        if (list.length > 0) setActiveStudyId(prev => prev || list[0].id);
      })
      .catch(() => setStudies([]));
  }, []);

  const loadSiteData = useCallback(async (studyId) => {
    if (!studyId) { setSiteData(null); return; }
    try {
      const res = await fetch(`${API_URL}/api/researcher/studies/${studyId}/sites`, { headers: authHeaders() });
      setSiteData(res.ok ? await res.json() : null);
    } catch (err) {
      setSiteData(null);
    }
  }, []);

  // Refresh regulatory status on entering the step, so an approval granted while
  // the researcher waits shows up without a full reload.
  useEffect(() => {
    if (step === 3 || step === 4) loadSiteData(activeStudyId);
  }, [step, activeStudyId, loadSiteData]);

  // Run feasibility against the live cohort API
  const runFeasibility = async () => {
    setIsRunning(true);
    setQueryError(null);
    const cancerTypes = inclusions
      .filter(r => r.field === 'diagnosis')
      .map(r => String(r.value).replace(/\s*\([^)]*\)\s*$/, '').trim())
      .filter(Boolean);
    try {
      const response = await fetch(`${API_URL}/api/cohort/build`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ cancer_types: cancerTypes.length > 0 ? cancerTypes : null }),
      });
      const data = await response.json();
      if (response.ok) {
        setCohortResult(data);
        setFeasibilityRun(true);
      } else {
        setQueryError(
          response.status === 401
            ? 'Your session has expired. Please sign in again to run a feasibility query.'
            : data.detail || 'Failed to run feasibility query.'
        );
      }
    } catch (err) {
      setQueryError('Failed to reach the server. Please sign in and try again.');
    } finally {
      setIsRunning(false);
    }
  };

  // Create a real study from the cohort definition
  const createStudy = async () => {
    if (!studyName.trim()) { setRegError('Give the study a name first.'); return; }
    setRegBusy(true); setRegError(null);
    try {
      const res = await fetch(`${API_URL}/api/researcher/studies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          name: studyName.trim(),
          description: `Inclusions: ${inclusions.map(r => `${r.field} ${r.operator} ${r.value}`).join('; ') || 'none'}. `
            + `Exclusions: ${exclusions.map(r => `${r.field} ${r.operator} ${r.value}`).join('; ') || 'none'}.`,
          principal_investigator: JSON.parse(sessionStorage.getItem('user') || '{}').name || 'Principal Investigator',
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to create study.');
      setStudies(prev => [...prev, data]);
      setActiveStudyId(data.id);
    } catch (err) {
      setRegError(err.message);
    } finally {
      setRegBusy(false);
    }
  };

  // Submit a real regulatory document against the selected study
  const submitRegulatory = async (documentType) => {
    if (!activeStudyId) { setRegError('Select or create a study first.'); return; }
    setRegBusy(true); setRegError(null);
    try {
      const res = await fetch(`${API_URL}/api/regulatory/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ study_id: activeStudyId, document_type: documentType }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Submission failed.');
      await loadSiteData(activeStudyId);
    } catch (err) {
      setRegError(err.message);
    } finally {
      setRegBusy(false);
    }
  };

  // Queue a real extraction job
  const startExtraction = async () => {
    if (!activeStudyId) { setExtractError('Select or create a study first.'); return; }
    setExtracting(true); setExtractError(null); setExtractJob(null);
    try {
      const res = await fetch(`${API_URL}/api/extraction/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          study_id: activeStudyId,
          variables: selectedVariableIds,
          output_format: outputFormat,
          deidentification_level: deidentLevel,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Extraction failed.');
      setExtractJob(data);
    } catch (err) {
      setExtractError(err.message);
    } finally {
      setExtracting(false);
    }
  };

  const selectedVariableIds = Object.values(selectedVars).flat();
  const totalVars = selectedVariableIds.length;

  const regDocuments = siteData?.central || [];
  const approvedDocs = regDocuments.filter(d => ['approved', 'signed'].includes(d.status));
  const hasIrb = regDocuments.some(d => d.document_type === 'irb_protocol' && d.status === 'approved');
  const hasDua = regDocuments.some(d => d.document_type === 'dua' && ['approved', 'signed'].includes(d.status));
  const siteCount = siteData?.sites?.length || 0;

  // Completeness measured across the variables the user actually picked
  const avgCompleteness = () => {
    const cats = variableInventory?.categories || [];
    const picked = [];
    cats.forEach(c => (c.variables || []).forEach(v => {
      if (selectedVars[c.category]?.includes(v.id)) picked.push(v.completeness);
    }));
    if (picked.length === 0) return null;
    return Math.round(picked.reduce((a, b) => a + b, 0) / picked.length);
  };

  return (
    <div className="min-h-screen bg-black text-white pt-20 pb-12 px-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link to="/research" className="text-white/40 text-sm hover:text-white/60 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold">Cohort Builder</h1>
              <p className="text-white/40 text-sm">Define criteria, select variables, complete regulatory</p>
            </div>
            {studyName && (
              <div className="text-right">
                <div className="text-xs text-white/40">Study Name</div>
                <div className="text-emerald-400">{studyName}</div>
              </div>
            )}
          </div>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center gap-2 mb-8 text-sm">
          {steps.map((label, i) => (
            <div key={i} className="flex items-center">
              <button
                onClick={() => i + 1 <= step && setStep(i + 1)}
                className={`flex items-center gap-2 px-3 py-1.5 transition-colors ${
                  step === i + 1 ? 'bg-emerald-500/20 text-emerald-400' : 
                  step > i + 1 ? 'bg-white/10 text-white/60 hover:bg-white/20' : 'bg-white/5 text-white/30'
                }`}
              >
                <span className={`w-5 h-5 flex items-center justify-center text-xs ${
                  step > i + 1 ? 'bg-emerald-500 text-black' : 'bg-white/10'
                }`}>
                  {step > i + 1 ? '✓' : i + 1}
                </span>
                {label}
              </button>
              {i < 3 && <span className="text-white/20 mx-2">→</span>}
            </div>
          ))}
        </div>

        {/* Step 1: Cohort Builder */}
        {step === 1 && (
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2 space-y-4">
              {/* Study Name */}
              <div className="bg-white/5 border border-white/10 p-4">
                <label className="block text-sm text-white/60 mb-2">Study Name</label>
                <input
                  type="text"
                  value={studyName}
                  onChange={(e) => setStudyName(e.target.value)}
                  placeholder="e.g., MM Bispecific Real-World Outcomes"
                  className="w-full bg-white/5 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Presets */}
              <div className="bg-white/5 border border-white/10 p-4">
                <div className="text-sm text-white/60 mb-3">Quick Start Templates</div>
                <div className="flex flex-wrap gap-2">
                  {diseasePresets.map((preset, i) => (
                    <button
                      key={i}
                      onClick={() => applyPreset(preset)}
                      className="px-3 py-1.5 text-xs border border-white/20 hover:border-emerald-500/50 hover:bg-emerald-500/10 transition-colors"
                    >
                      {preset.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Inclusions */}
              <div className="bg-white/5 border border-white/10 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-medium text-emerald-400">Inclusion Criteria</h2>
                  <button 
                    onClick={() => setShowAddRule('inclusion')}
                    className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1.5 transition-colors"
                  >
                    + Add Rule
                  </button>
                </div>
                <div className="space-y-2">
                  <AnimatePresence>
                    {inclusions.map((rule) => (
                      <motion.div
                        key={rule.id}
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="flex items-center gap-2 bg-white/5 p-3"
                      >
                        <span className="text-xs text-white/40 w-24 truncate">
                          {fieldDefinitions[rule.field]?.label || rule.field}
                        </span>
                        <span className="text-xs text-emerald-400 px-2 py-0.5 bg-emerald-500/10">
                          {rule.operator}
                        </span>
                        <span className="flex-1 text-sm">{rule.value}</span>
                        <button 
                          onClick={() => removeRule('inclusion', rule.id)}
                          className="text-white/30 hover:text-red-400 p-1 text-lg"
                        >
                          ×
                        </button>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  {inclusions.length === 0 && (
                    <div className="text-center text-white/30 py-4 text-sm">
                      No inclusion criteria. Add at least one rule.
                    </div>
                  )}
                </div>
              </div>

              {/* Exclusions */}
              <div className="bg-white/5 border border-white/10 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-medium text-amber-400">Exclusion Criteria</h2>
                  <button 
                    onClick={() => setShowAddRule('exclusion')}
                    className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1.5 transition-colors"
                  >
                    + Add Rule
                  </button>
                </div>
                <div className="space-y-2">
                  <AnimatePresence>
                    {exclusions.map((rule) => (
                      <motion.div
                        key={rule.id}
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="flex items-center gap-3 bg-white/5 p-3"
                      >
                        <input 
                          type="checkbox" 
                          checked={rule.enabled}
                          onChange={() => {
                            setExclusions(exclusions.map(r => 
                              r.id === rule.id ? { ...r, enabled: !r.enabled } : r
                            ));
                          }}
                          className="rounded bg-white/10 border-white/20 text-emerald-500 focus:ring-emerald-500"
                        />
                        <span className={`flex-1 text-sm ${rule.enabled ? '' : 'text-white/30 line-through'}`}>
                          {fieldDefinitions[rule.field]?.label || rule.field} {rule.operator} {rule.value}
                        </span>
                        <button 
                          onClick={() => removeRule('exclusion', rule.id)}
                          className="text-white/30 hover:text-red-400 p-1 text-lg"
                        >
                          ×
                        </button>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  {exclusions.length === 0 && (
                    <div className="text-center text-white/30 py-4 text-sm">
                      No exclusion criteria (optional)
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Feasibility Panel */}
            <div className="space-y-4">
              <div className="bg-white/5 border border-white/10 p-5">
                <h2 className="font-medium mb-4">Feasibility</h2>
                
                {queryError && (
                  <p className="text-red-400 text-xs mb-3">{queryError}</p>
                )}
                {!feasibilityRun ? (
                  <button 
                    onClick={runFeasibility}
                    disabled={isRunning}
                    className={`w-full font-medium py-2 mb-4 transition-colors ${
                      isRunning 
                        ? 'bg-emerald-500/50 text-black/50' 
                        : 'bg-emerald-500 hover:bg-emerald-400 text-black'
                    }`}
                  >
                    {isRunning ? 'Running Query...' : inclusions.length === 0 ? 'Count all consented patients' : 'Run Query'}
                  </button>
                ) : (
                  <>
                    <div className="text-center mb-4">
                      <div className="text-4xl font-bold text-emerald-400">
                        {(cohortResult?.patient_count ?? 0).toLocaleString()}
                      </div>
                      <div className="text-white/40 text-sm">eligible patients</div>
                    </div>

                    <div className="space-y-2 mb-4">
                      {[
                        ['Diagnoses', cohortResult?.diagnosis_count],
                        ['Treatments', cohortResult?.treatment_count],
                        ['Molecular', cohortResult?.molecular_count],
                        ['Data points', cohortResult?.data_points],
                      ].map(([label, value]) => (
                        <div key={label} className="flex items-center justify-between text-sm">
                          <span className="text-white/40">{label}</span>
                          <span className="text-white font-mono">{(value ?? 0).toLocaleString()}</span>
                        </div>
                      ))}
                    </div>

                    {institutions.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-xs uppercase tracking-wider text-white/40">Sites you can file a study with</div>
                        {institutions.map(inst => (
                          <div key={inst.id} className="bg-white/5 p-3 text-sm">
                            <div className="font-medium">{inst.name}</div>
                            <div className="text-white/30 text-xs">
                              {[inst.city, inst.state].filter(Boolean).join(', ')}
                              {inst.emr_system ? ` \u00b7 ${inst.emr_system}` : ''}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
                
                <button 
                  onClick={() => setStep(2)}
                  disabled={!feasibilityRun}
                  className={`w-full mt-4 py-2 font-medium transition-colors ${
                    feasibilityRun 
                      ? 'bg-white/10 hover:bg-white/20 text-white' 
                      : 'bg-white/5 text-white/30 cursor-not-allowed'
                  }`}
                >
                  Select Variables →
                </button>
              </div>

              {/* Criteria Summary */}
              <div className="bg-white/5 border border-white/10 p-5">
                <h3 className="text-sm font-medium mb-3">Criteria Summary</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-white/40">Inclusions</span>
                    <span className="text-emerald-400">{inclusions.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Exclusions</span>
                    <span className="text-amber-400">{exclusions.filter(e => e.enabled).length}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Variable Selection */}
        {step === 2 && (
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2">
              <div className="bg-white/5 border border-white/10 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-medium">Select Variables</h2>
                  <div className="text-xs text-white/40">
                    {totalVars} selected
                  </div>
                </div>
                {inventoryError && (
                  <p className="text-amber-400 text-sm">{inventoryError}</p>
                )}
                {!inventoryError && !variableInventory && (
                  <p className="text-white/40 text-sm">Loading variable inventory…</p>
                )}
                {variableInventory && variableInventory.categories.length === 0 && (
                  <div className="text-sm text-white/40 space-y-2">
                    <p>No variables are available yet.</p>
                    <p className="text-xs">
                      Variables appear here once enough consented patients have contributed records.
                      Fields held by fewer than {variableInventory.min_cell_size} patients are withheld
                      so a rare variable cannot itself identify someone.
                    </p>
                  </div>
                )}
                {variableInventory && variableInventory.categories.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {variableInventory.categories.map(({ category, variables: vars }) => (
                      <div key={category} className="bg-white/5 p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="text-sm font-medium text-white/60 capitalize">
                            {category.replace(/_/g, ' ')}
                          </h3>
                          <button
                            onClick={() => {
                              const allSelected = vars.every(v => selectedVars[category]?.includes(v.id));
                              setSelectedVars({
                                ...selectedVars,
                                [category]: allSelected ? [] : vars.map(v => v.id),
                              });
                            }}
                            className="text-xs text-emerald-400 hover:underline"
                          >
                            {vars.every(v => selectedVars[category]?.includes(v.id)) ? 'Clear' : 'Select All'}
                          </button>
                        </div>
                        <div className="space-y-2">
                          {vars.map(v => (
                            <label key={v.id} className="flex items-center gap-2 text-sm cursor-pointer hover:text-emerald-400 group">
                              <input
                                type="checkbox"
                                checked={selectedVars[category]?.includes(v.id) || false}
                                onChange={() => {
                                  const current = selectedVars[category] || [];
                                  setSelectedVars({
                                    ...selectedVars,
                                    [category]: current.includes(v.id)
                                      ? current.filter(x => x !== v.id)
                                      : [...current, v.id],
                                  });
                                }}
                                className="rounded bg-white/10 border-white/20 text-emerald-500 focus:ring-emerald-500"
                              />
                              <span className="text-white/50 flex-1">{v.label}</span>
                              <span
                                title={`${v.patients_with_data} of ${variableInventory.total_patients} contributing patients have this field`}
                                className={`text-xs ${
                                  v.completeness >= 90 ? 'text-emerald-400' :
                                  v.completeness >= 70 ? 'text-amber-400' : 'text-red-400'
                                }`}
                              >
                                {v.completeness}%
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {variableInventory && (
                  <p className="text-white/30 text-xs mt-4">
                    Completeness is measured against {variableInventory.total_patients} contributing
                    {variableInventory.total_patients === 1 ? ' patient' : ' patients'}
                    {variableInventory.suppressed_variables > 0 &&
                      ` · ${variableInventory.suppressed_variables} rare field(s) withheld below the ${variableInventory.min_cell_size}-patient floor`}
                    .
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-white/5 border border-white/10 p-5">
                <h2 className="font-medium mb-4">Summary</h2>
                <div className="space-y-3 mb-4">
                  {Object.entries(selectedVars).map(([cat, vars]) => vars.length > 0 && (
                    <div key={cat} className="text-sm flex justify-between">
                      <span className="text-white/40 capitalize">{cat}</span>
                      <span className="text-emerald-400">{vars.length}</span>
                    </div>
                  ))}
                  <div className="border-t border-white/10 pt-3 flex justify-between font-medium">
                    <span>Total Variables</span>
                    <span className="text-emerald-400">{totalVars}</span>
                  </div>
                  {totalVars === 0 && (
                    <p className="text-white/30 text-xs">
                      Nothing selected — the extract will include every field available for the cohort.
                    </p>
                  )}
                </div>
                
                {avgCompleteness() !== null && (
                  <div className="bg-white/5 p-3 mb-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-white/40">Measured completeness</span>
                      <span className={
                        avgCompleteness() >= 85 ? 'text-emerald-400' :
                        avgCompleteness() >= 70 ? 'text-amber-400' :
                        'text-red-400'
                      }>{avgCompleteness()}%</span>
                    </div>
                  </div>
                )}

                <div className="flex gap-2">
                  <button 
                    onClick={() => setStep(1)}
                    className="flex-1 bg-white/10 hover:bg-white/20 py-2 text-sm transition-colors"
                  >
                    ← Back
                  </button>
                  <button 
                    onClick={() => setStep(3)}
                    className="flex-1 font-medium py-2 text-sm transition-colors bg-emerald-500 hover:bg-emerald-400 text-black"
                  >
                    Continue →
                  </button>
                </div>
              </div>

              {/* Cohort Summary */}
              <div className="bg-white/5 border border-white/10 p-5">
                <h3 className="text-sm font-medium mb-3">Cohort</h3>
                <div className="text-2xl font-bold text-emerald-400 mb-1">{(cohortResult?.patient_count ?? 0).toLocaleString()}</div>
                <div className="text-xs text-white/40">consented and matching</div>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Regulatory */}
        {step === 3 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <div className="bg-white/5 border border-white/10 p-5">
                <h2 className="font-medium mb-4">Study</h2>
                {studies.length > 0 && (
                  <div className="mb-4">
                    <label className="block text-xs uppercase tracking-wider text-white/40 mb-2">
                      Attach this cohort to a study
                    </label>
                    <select
                      value={activeStudyId}
                      onChange={(e) => setActiveStudyId(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
                    >
                      {studies.map(st => (
                        <option key={st.id} value={st.id} className="bg-black">{st.name}</option>
                      ))}
                    </select>
                  </div>
                )}
                <div className="flex flex-wrap items-center gap-3">
                  <input
                    type="text"
                    value={studyName}
                    onChange={(e) => setStudyName(e.target.value)}
                    placeholder="New study name"
                    className="flex-1 min-w-[200px] bg-white/5 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
                  />
                  <button
                    onClick={createStudy}
                    disabled={regBusy || !studyName.trim()}
                    className="bg-white/10 hover:bg-white/20 px-4 py-2 text-sm transition-colors disabled:opacity-40"
                  >
                    {regBusy ? 'Working…' : 'Create study'}
                  </button>
                </div>
                {studies.length === 0 && (
                  <p className="text-white/40 text-xs mt-3">
                    You have no studies yet. Create one to submit regulatory documents against it.
                  </p>
                )}
              </div>

              <div className="bg-white/5 border border-white/10 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-medium">Regulatory Pipeline</h2>
                  <div className="text-xs text-white/40">
                    {approvedDocs.length}/{regDocuments.length} approved
                  </div>
                </div>

                {regError && <p className="text-red-400 text-sm mb-3">{regError}</p>}

                {!activeStudyId ? (
                  <p className="text-white/40 text-sm">Select or create a study to see its regulatory status.</p>
                ) : regDocuments.length === 0 ? (
                  <p className="text-white/40 text-sm">
                    No documents submitted yet. Submit an IRB protocol and a data use agreement below —
                    both must be approved by a reviewer before any extraction can run.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {regDocuments.map((doc) => {
                      const done = ['approved', 'signed'].includes(doc.status);
                      const pending = doc.status === 'submitted' || doc.status === 'under_review';
                      return (
                        <div key={doc.id} className="flex items-center justify-between bg-white/5 p-4 gap-3 flex-wrap">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 flex items-center justify-center ${
                              done ? 'bg-emerald-500/20' : pending ? 'bg-amber-500/20' : 'bg-white/10'
                            }`}>
                              {done ? <span className="text-emerald-400">✓</span>
                                : pending ? <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
                                : <div className="w-2 h-2 bg-white/30 rounded-full" />}
                            </div>
                            <div>
                              <div className="font-medium text-sm capitalize">
                                {String(doc.document_type || '').replace(/_/g, ' ')}
                              </div>
                              <div className="text-xs text-white/40">
                                {doc.protocol_number ? `${doc.protocol_number} · ` : ''}
                                {doc.status}
                                {doc.approved_at ? ` · approved ${new Date(doc.approved_at).toLocaleDateString()}` : ''}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                <div className="flex flex-wrap gap-2 mt-4">
                  <button
                    onClick={() => submitRegulatory('irb_protocol')}
                    disabled={regBusy || !activeStudyId}
                    className="bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 px-4 py-2 text-sm transition-colors disabled:opacity-40"
                  >
                    Submit IRB protocol
                  </button>
                  <button
                    onClick={() => submitRegulatory('dua')}
                    disabled={regBusy || !activeStudyId}
                    className="bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 px-4 py-2 text-sm transition-colors disabled:opacity-40"
                  >
                    Submit data use agreement
                  </button>
                  <button
                    onClick={() => submitRegulatory('reliance_agreement')}
                    disabled={regBusy || !activeStudyId}
                    className="bg-white/10 hover:bg-white/20 px-4 py-2 text-sm transition-colors disabled:opacity-40"
                  >
                    Submit reliance agreement
                  </button>
                </div>
                <p className="text-white/30 text-xs mt-3">
                  Submissions are reviewed by an institutional reviewer. You cannot approve your own
                  submission, and extraction stays blocked until the IRB protocol and DUA are both approved.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-white/5 border border-white/10 p-5">
                <h3 className="text-sm font-medium mb-3">Study Summary</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-white/40">Patients</span>
                    <span>{(cohortResult?.patient_count ?? 0).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Variables</span>
                    <span>{totalVars}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Sites</span>
                    <span>{siteCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">IRB approved</span>
                    <span className={hasIrb ? 'text-emerald-400' : 'text-white/40'}>{hasIrb ? 'Yes' : 'No'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">DUA approved</span>
                    <span className={hasDua ? 'text-emerald-400' : 'text-white/40'}>{hasDua ? 'Yes' : 'No'}</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 bg-white/10 hover:bg-white/20 py-2 text-sm transition-colors"
                >
                  ← Back
                </button>
                <button
                  onClick={() => setStep(4)}
                  disabled={!activeStudyId}
                  className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-black font-medium py-2 text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Extract →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Extract */}
        {step === 4 && (
          <div className="max-w-2xl mx-auto">
            {!extractJob ? (
              <div className="bg-white/5 border border-white/10 p-8">
                <h2 className="text-xl font-semibold mb-6">Configure Extraction</h2>

                <div className="space-y-6 mb-8">
                  <div>
                    <label className="block text-sm text-white/60 mb-2">Output Format</label>
                    <div className="flex flex-wrap gap-3">
                      {[
                        { id: 'csv', label: 'CSV', desc: 'REDCap-ready' },
                        { id: 'parquet', label: 'Parquet', desc: 'For Python/R' },
                        { id: 'fhir', label: 'FHIR', desc: 'Interoperability' }
                      ].map(opt => (
                        <button
                          key={opt.id}
                          onClick={() => setOutputFormat(opt.id)}
                          className={`flex-1 min-w-[120px] p-3 border transition-colors ${
                            outputFormat === opt.id
                              ? 'border-emerald-500 bg-emerald-500/10'
                              : 'border-white/10 hover:border-white/20'
                          }`}
                        >
                          <div className="font-medium text-sm">{opt.label}</div>
                          <div className="text-xs text-white/40">{opt.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-white/60 mb-2">De-identification Level</label>
                    <div className="space-y-2">
                      {[
                        { id: 'limited_dataset', label: 'Limited Dataset', desc: 'Year-level dates, no geography below state' },
                        { id: 'safe_harbor', label: 'Safe Harbor', desc: 'All 18 HIPAA identifiers removed' },
                        { id: 'expert', label: 'Expert Determination', desc: 'Requires a documented statistical determination' }
                      ].map(opt => (
                        <button
                          key={opt.id}
                          onClick={() => setDeidentLevel(opt.id)}
                          className={`w-full p-3 border text-left transition-colors ${
                            deidentLevel === opt.id
                              ? 'border-emerald-500 bg-emerald-500/10'
                              : 'border-white/10 hover:border-white/20'
                          }`}
                        >
                          <div className="font-medium text-sm">{opt.label}</div>
                          <div className="text-xs text-white/40">{opt.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="bg-white/5 p-4 mb-6">
                  <h3 className="text-sm font-medium mb-3">Extraction Summary</h3>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-emerald-400">
                        {(cohortResult?.patient_count ?? 0).toLocaleString()}
                      </div>
                      <div className="text-xs text-white/40">Patients</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{totalVars}</div>
                      <div className="text-xs text-white/40">Variables</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{siteCount}</div>
                      <div className="text-xs text-white/40">Sites</div>
                    </div>
                  </div>
                </div>

                {(!hasIrb || !hasDua) && (
                  <p className="text-amber-400 text-sm mb-4">
                    Extraction is blocked until this study has an approved IRB protocol and an approved
                    data use agreement.
                  </p>
                )}
                {extractError && <p className="text-red-400 text-sm mb-4">{extractError}</p>}

                <div className="flex gap-3">
                  <button
                    onClick={() => setStep(3)}
                    className="flex-1 bg-white/10 hover:bg-white/20 py-3 font-medium transition-colors"
                  >
                    ← Back
                  </button>
                  <button
                    onClick={startExtraction}
                    disabled={extracting || !activeStudyId}
                    className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-black font-medium py-3 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {extracting ? 'Running…' : 'Start Extraction'}
                  </button>
                </div>
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-white/5 border border-white/10 p-8 text-center"
              >
                <div className="w-16 h-16 bg-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl text-emerald-400">✓</span>
                </div>
                <h2 className="text-xl font-semibold mb-2">
                  {extractJob.status === 'completed' ? 'Extraction Complete' : 'Extraction Queued'}
                </h2>
                <p className="text-white/40 mb-6">
                  {(extractJob.patient_count ?? 0).toLocaleString()} patients · {totalVars} variables
                </p>

                <div className="bg-white/5 p-4 text-left mb-6">
                  <div className="text-sm space-y-2">
                    <div className="flex justify-between gap-4">
                      <span className="text-white/40">Job ID</span>
                      <span className="font-mono text-emerald-400 break-all">{extractJob.job_id}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-white/40">Status</span>
                      <span>{extractJob.status}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-white/40">Study</span>
                      <span>{studies.find(st => st.id === activeStudyId)?.name || studyName}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-white/40">Format</span>
                      <span>{outputFormat.toUpperCase()}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-white/40">De-identification</span>
                      <span>{deidentLevel.replace(/_/g, ' ')}</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3 justify-center">
                  {extractJob.status === 'completed' && (
                    <button
                      onClick={async () => {
                        const res = await fetch(`${API_URL}/api/extraction/jobs/${extractJob.job_id}/download`, {
                          headers: authHeaders(),
                        });
                        if (!res.ok) { setExtractError('Download failed.'); return; }
                        const blob = await res.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `${extractJob.job_id}.csv`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                      className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium px-4 py-2 text-sm transition-colors"
                    >
                      Download dataset
                    </button>
                  )}
                  <Link to="/research" className="bg-white/10 hover:bg-white/20 px-4 py-2 text-sm transition-colors">
                    View All Jobs
                  </Link>
                  <button
                    onClick={() => {
                      setStep(1);
                      setFeasibilityRun(false);
                      setExtractJob(null);
                      setExtractError(null);
                      setStudyName('');
                    }}
                    className="bg-white/10 hover:bg-white/20 px-4 py-2 text-sm transition-colors"
                  >
                    New Query
                  </button>
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>

      {/* Add Rule Modal */}
      <AnimatePresence>
        {showAddRule && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
            onClick={() => setShowAddRule(null)}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="bg-neutral-900 border border-white/10 p-6 w-full max-w-md"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-lg font-medium mb-4">
                Add {showAddRule === 'inclusion' ? 'Inclusion' : 'Exclusion'} Rule
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-white/60 mb-1">Field</label>
                  <select
                    value={newRule.field}
                    onChange={(e) => {
                      const field = e.target.value;
                      const operators = fieldDefinitions[field]?.operators || ['IS'];
                      setNewRule({ ...newRule, field, operator: operators[0], value: '' });
                    }}
                    className="w-full bg-white/5 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
                  >
                    <option value="">Select field...</option>
                    {Object.entries(fieldDefinitions).map(([key, def]) => (
                      <option key={key} value={key}>{def.label}</option>
                    ))}
                  </select>
                </div>

                {newRule.field && (
                  <>
                    <div>
                      <label className="block text-sm text-white/60 mb-1">Operator</label>
                      <select
                        value={newRule.operator}
                        onChange={(e) => setNewRule({ ...newRule, operator: e.target.value })}
                        className="w-full bg-white/5 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
                      >
                        {fieldDefinitions[newRule.field]?.operators.map(op => (
                          <option key={op} value={op}>{op}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm text-white/60 mb-1">Value</label>
                      <select
                        value={newRule.value}
                        onChange={(e) => setNewRule({ ...newRule, value: e.target.value })}
                        className="w-full bg-white/5 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
                      >
                        <option value="">Select value...</option>
                        {fieldDefinitions[newRule.field]?.values.map(val => (
                          <option key={val} value={val}>{val}</option>
                        ))}
                      </select>
                    </div>
                  </>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowAddRule(null)}
                  className="flex-1 bg-white/10 hover:bg-white/20 py-2 text-sm transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => addRule(showAddRule)}
                  disabled={!newRule.field || !newRule.value}
                  className={`flex-1 py-2 text-sm font-medium transition-colors ${
                    newRule.field && newRule.value
                      ? 'bg-emerald-500 hover:bg-emerald-400 text-black'
                      : 'bg-white/10 text-white/30 cursor-not-allowed'
                  }`}
                >
                  Add Rule
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default CohortBuilder;

