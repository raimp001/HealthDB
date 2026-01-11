import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

const CohortBuilder = () => {
  const [step, setStep] = useState(1);
  const [studyName, setStudyName] = useState('');
  const [inclusions, setInclusions] = useState([
    { id: 1, field: 'diagnosis', operator: 'IS', value: 'Multiple Myeloma (C90.0)' },
    { id: 2, field: 'treatment', operator: 'INCLUDES', value: 'Bispecific antibody' }
  ]);
  const [exclusions, setExclusions] = useState([
    { id: 1, field: 'prior_cart', operator: 'IS', value: 'TRUE', enabled: true }
  ]);
  const [selectedVars, setSelectedVars] = useState({
    demographics: ['age_at_dx', 'sex'],
    labs: ['hemoglobin', 'ldh', 'b2m'],
    staging: ['iss', 'riss'],
    outcomes: ['pfs', 'os']
  });
  const [feasibilityRun, setFeasibilityRun] = useState(false);
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

  // Disease presets
  const diseasePresets = [
    {
      name: 'Multiple Myeloma Registry',
      inclusions: [
        { field: 'diagnosis', operator: 'IS', value: 'Multiple Myeloma (C90.0)' }
      ],
      exclusions: [],
      variables: {
        demographics: ['age_at_dx', 'sex', 'race'],
        labs: ['hemoglobin', 'creatinine', 'ldh', 'b2m', 'albumin'],
        staging: ['iss', 'riss'],
        cytogenetics: ['del17p', 't_4_14', 't_14_16', 'gain_1q'],
        outcomes: ['pfs', 'os', 'best_response']
      }
    },
    {
      name: 'CAR-T Outcomes',
      inclusions: [
        { field: 'treatment', operator: 'INCLUDES', value: 'CAR-T therapy' }
      ],
      exclusions: [],
      variables: {
        demographics: ['age_at_dx', 'sex'],
        labs: ['ldh', 'crp', 'ferritin'],
        outcomes: ['pfs', 'os', 'crs_grade', 'icans_grade', 'best_response']
      }
    },
    {
      name: 'Bispecific Antibody Study',
      inclusions: [
        { field: 'diagnosis', operator: 'IS', value: 'Multiple Myeloma (C90.0)' },
        { field: 'treatment', operator: 'INCLUDES', value: 'Bispecific antibody' }
      ],
      exclusions: [
        { field: 'prior_cart', operator: 'IS', value: 'TRUE', enabled: true }
      ],
      variables: {
        demographics: ['age_at_dx', 'sex'],
        labs: ['hemoglobin', 'ldh', 'b2m'],
        staging: ['iss', 'riss'],
        outcomes: ['pfs', 'os', 'crs_grade', 'icans_grade']
      }
    }
  ];

  const institutions = [
    { name: 'OHSU Knight', n: 847, completeness: 92, status: 'active' },
    { name: 'Fred Hutchinson', n: 512, completeness: 87, status: 'pending' },
    { name: 'Emory Winship', n: 234, completeness: 78, status: 'setup' }
  ];

  const variables = {
    demographics: [
      { id: 'age_at_dx', label: 'Age at Diagnosis', completeness: 99 },
      { id: 'sex', label: 'Sex', completeness: 99 },
      { id: 'race', label: 'Race/Ethnicity', completeness: 85 },
      { id: 'zip_3digit', label: 'ZIP (3-digit)', completeness: 92 }
    ],
    labs: [
      { id: 'hemoglobin', label: 'Hemoglobin', completeness: 94 },
      { id: 'creatinine', label: 'Creatinine', completeness: 93 },
      { id: 'ldh', label: 'LDH', completeness: 78 },
      { id: 'b2m', label: 'Beta-2 Microglobulin', completeness: 72 },
      { id: 'albumin', label: 'Albumin', completeness: 89 },
      { id: 'flc_kappa', label: 'FLC Kappa', completeness: 65 },
      { id: 'flc_lambda', label: 'FLC Lambda', completeness: 65 }
    ],
    staging: [
      { id: 'iss', label: 'ISS Stage', completeness: 82 },
      { id: 'riss', label: 'R-ISS Stage', completeness: 68 },
      { id: 'bone_lesions', label: 'Bone Lesions', completeness: 71 },
      { id: 'extramedullary', label: 'Extramedullary Disease', completeness: 59 }
    ],
    treatments: [
      { id: 'regimen', label: 'Regimen Name', completeness: 95 },
      { id: 'start_date', label: 'Start Date', completeness: 97 },
      { id: 'stop_date', label: 'Stop Date', completeness: 88 },
      { id: 'cycles', label: 'Cycles Completed', completeness: 75 },
      { id: 'best_response', label: 'Best Response', completeness: 82 }
    ],
    outcomes: [
      { id: 'pfs', label: 'Progression-Free Survival', completeness: 76 },
      { id: 'os', label: 'Overall Survival', completeness: 89 },
      { id: 'crs_grade', label: 'CRS Grade', completeness: 91 },
      { id: 'icans_grade', label: 'ICANS Grade', completeness: 88 },
      { id: 'infections', label: 'Infections', completeness: 67 }
    ],
    cytogenetics: [
      { id: 'del17p', label: 'del(17p)', completeness: 74 },
      { id: 't_4_14', label: 't(4;14)', completeness: 72 },
      { id: 't_14_16', label: 't(14;16)', completeness: 68 },
      { id: 'gain_1q', label: 'gain(1q)', completeness: 65 },
      { id: 't_11_14', label: 't(11;14)', completeness: 62 }
    ]
  };

  const [regulatorySteps, setRegulatorySteps] = useState([
    { id: 1, name: 'Central IRB', status: 'approved', date: '2025-01-05', doc: true },
    { id: 2, name: 'Data Use Agreement', status: 'signed', date: '2025-01-06', doc: true },
    { id: 3, name: 'OHSU Reliance', status: 'pending', date: null, doc: false },
    { id: 4, name: 'Fred Hutch Reliance', status: 'not_started', date: null, doc: false }
  ]);

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
    setSelectedVars(preset.variables);
    setStudyName(preset.name);
  };

  // Run feasibility
  const runFeasibility = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
      setFeasibilityRun(true);
    }, 1500);
  };

  // Calculate total selected variables
  const totalVars = Object.values(selectedVars).reduce((sum, arr) => sum + arr.length, 0);

  // Calculate average completeness
  const avgCompleteness = () => {
    let total = 0;
    let count = 0;
    Object.entries(selectedVars).forEach(([cat, vars]) => {
      vars.forEach(v => {
        const varDef = variables[cat]?.find(x => x.id === v);
        if (varDef) {
          total += varDef.completeness;
          count++;
        }
      });
    });
    return count > 0 ? Math.round(total / count) : 0;
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
                
                {!feasibilityRun ? (
                  <button 
                    onClick={runFeasibility}
                    disabled={isRunning || inclusions.length === 0}
                    className={`w-full font-medium py-2 mb-4 transition-colors ${
                      inclusions.length === 0 
                        ? 'bg-white/10 text-white/30 cursor-not-allowed'
                        : isRunning 
                          ? 'bg-emerald-500/50 text-black/50' 
                          : 'bg-emerald-500 hover:bg-emerald-400 text-black'
                    }`}
                  >
                    {isRunning ? 'Running Query...' : 'Run Query'}
                  </button>
                ) : (
                  <>
                    <div className="text-center mb-4">
                      <div className="text-4xl font-bold text-emerald-400">1,593</div>
                      <div className="text-white/40 text-sm">eligible patients</div>
                    </div>
                    
                    <div className="space-y-3">
                      {institutions.map((inst, i) => (
                        <div key={i} className="bg-white/5 p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium">{inst.name}</span>
                            <span className={`text-xs px-1.5 py-0.5 ${
                              inst.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' :
                              inst.status === 'pending' ? 'bg-amber-500/20 text-amber-400' :
                              'bg-white/10 text-white/40'
                            }`}>
                              {inst.status}
                            </span>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-white/40">N = {inst.n}</span>
                            <span className="text-white/30">{inst.completeness}%</span>
                          </div>
                          <div className="mt-2 h-1 bg-white/10 overflow-hidden">
                            <div 
                              className="h-full bg-emerald-500"
                              style={{ width: `${inst.completeness}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
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
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(variables).map(([category, vars]) => (
                    <div key={category} className="bg-white/5 p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-medium text-white/60 capitalize">{category}</h3>
                        <button
                          onClick={() => {
                            const allSelected = vars.every(v => selectedVars[category]?.includes(v.id));
                            if (allSelected) {
                              setSelectedVars({ ...selectedVars, [category]: [] });
                            } else {
                              setSelectedVars({ ...selectedVars, [category]: vars.map(v => v.id) });
                            }
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
                              checked={selectedVars[category]?.includes(v.id)}
                              onChange={() => {
                                const updated = { ...selectedVars };
                                if (!updated[category]) updated[category] = [];
                                if (updated[category].includes(v.id)) {
                                  updated[category] = updated[category].filter(x => x !== v.id);
                                } else {
                                  updated[category].push(v.id);
                                }
                                setSelectedVars(updated);
                              }}
                              className="rounded bg-white/10 border-white/20 text-emerald-500 focus:ring-emerald-500"
                            />
                            <span className="text-white/50 flex-1">{v.label}</span>
                            <span className={`text-xs ${
                              v.completeness >= 90 ? 'text-emerald-400' :
                              v.completeness >= 70 ? 'text-amber-400' :
                              'text-red-400'
                            } opacity-0 group-hover:opacity-100 transition-opacity`}>
                              {v.completeness}%
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
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
                </div>
                
                <div className="bg-white/5 p-3 mb-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/40">Est. Completeness</span>
                    <span className={
                      avgCompleteness() >= 85 ? 'text-emerald-400' :
                      avgCompleteness() >= 70 ? 'text-amber-400' :
                      'text-red-400'
                    }>{avgCompleteness()}%</span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button 
                    onClick={() => setStep(1)}
                    className="flex-1 bg-white/10 hover:bg-white/20 py-2 text-sm transition-colors"
                  >
                    ← Back
                  </button>
                  <button 
                    onClick={() => setStep(3)}
                    disabled={totalVars === 0}
                    className={`flex-1 font-medium py-2 text-sm transition-colors ${
                      totalVars > 0 
                        ? 'bg-emerald-500 hover:bg-emerald-400 text-black' 
                        : 'bg-white/10 text-white/30 cursor-not-allowed'
                    }`}
                  >
                    Continue →
                  </button>
                </div>
              </div>

              {/* Cohort Summary */}
              <div className="bg-white/5 border border-white/10 p-5">
                <h3 className="text-sm font-medium mb-3">Cohort</h3>
                <div className="text-2xl font-bold text-emerald-400 mb-1">1,593</div>
                <div className="text-xs text-white/40">patients across 3 sites</div>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Regulatory */}
        {step === 3 && (
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2 space-y-4">
              <div className="bg-white/5 border border-white/10 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-medium">Regulatory Pipeline</h2>
                  <div className="text-xs text-white/40">
                    {regulatorySteps.filter(s => s.status === 'approved' || s.status === 'signed').length}/{regulatorySteps.length} complete
                  </div>
                </div>
                <div className="space-y-3">
                  {regulatorySteps.map((item) => (
                    <div key={item.id} className="flex items-center justify-between bg-white/5 p-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 flex items-center justify-center ${
                          item.status === 'approved' || item.status === 'signed' ? 'bg-emerald-500/20' :
                          item.status === 'pending' ? 'bg-amber-500/20' : 'bg-white/10'
                        }`}>
                          {item.status === 'approved' || item.status === 'signed' ? (
                            <span className="text-emerald-400">✓</span>
                          ) : item.status === 'pending' ? (
                            <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
                          ) : (
                            <div className="w-2 h-2 bg-white/30 rounded-full" />
                          )}
                        </div>
                        <div>
                          <div className="font-medium text-sm">{item.name}</div>
                          <div className="text-xs text-white/40">
                            {item.status === 'approved' || item.status === 'signed' 
                              ? `Completed ${item.date}` 
                              : item.status === 'pending' 
                                ? 'Under review (est. 3-5 days)'
                                : 'Not started'}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {item.doc && (
                          <button className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1.5 transition-colors">
                            View
                          </button>
                        )}
                        {item.status === 'not_started' && (
                          <button 
                            onClick={() => {
                              setRegulatorySteps(regulatorySteps.map(s => 
                                s.id === item.id ? { ...s, status: 'pending' } : s
                              ));
                            }}
                            className="text-xs bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 px-3 py-1.5 transition-colors"
                          >
                            Generate
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Timeline */}
              <div className="bg-white/5 border border-white/10 p-5">
                <h2 className="font-medium mb-4">Estimated Timeline</h2>
                <div className="flex items-center gap-4">
                  <div className="flex-1 h-2 bg-white/10 relative">
                    <div className="absolute left-0 w-1/4 h-full bg-emerald-500" />
                    <div className="absolute left-1/4 w-1/4 h-full bg-emerald-500/50" />
                  </div>
                  <span className="text-sm text-white/60">~2-3 weeks</span>
                </div>
                <div className="flex justify-between text-xs text-white/40 mt-2">
                  <span>IRB</span>
                  <span>DUA</span>
                  <span>Reliance</span>
                  <span>Data Ready</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-white/5 border border-white/10 p-5">
                <h2 className="font-medium mb-3">Quick Actions</h2>
                <div className="space-y-2">
                  <button className="w-full bg-white/10 hover:bg-white/20 py-2 text-sm transition-colors flex items-center justify-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    IRB Protocol
                  </button>
                  <button className="w-full bg-white/10 hover:bg-white/20 py-2 text-sm transition-colors flex items-center justify-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    DUA Template
                  </button>
                  <button className="w-full bg-white/10 hover:bg-white/20 py-2 text-sm transition-colors flex items-center justify-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Reliance Form
                  </button>
                </div>
              </div>

              <div className="bg-white/5 border border-white/10 p-5">
                <h3 className="text-sm font-medium mb-3">Study Summary</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-white/40">Patients</span>
                    <span>1,593</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Variables</span>
                    <span>{totalVars}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Sites</span>
                    <span>3</span>
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
                  className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-black font-medium py-2 text-sm transition-colors"
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
            {!extracting ? (
              <div className="bg-white/5 border border-white/10 p-8">
                <h2 className="text-xl font-semibold mb-6">Configure Extraction</h2>
                
                <div className="space-y-6 mb-8">
                  <div>
                    <label className="block text-sm text-white/60 mb-2">Output Format</label>
                    <div className="flex gap-3">
                      {[
                        { id: 'csv', label: 'CSV', desc: 'REDCap-ready' },
                        { id: 'parquet', label: 'Parquet', desc: 'For Python/R' },
                        { id: 'fhir', label: 'FHIR', desc: 'Interoperability' }
                      ].map(opt => (
                        <button
                          key={opt.id}
                          onClick={() => setOutputFormat(opt.id)}
                          className={`flex-1 p-3 border transition-colors ${
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
                        { id: 'limited_dataset', label: 'Limited Dataset', desc: 'Dates shifted, ZIP-3 only' },
                        { id: 'safe_harbor', label: 'Safe Harbor', desc: '18 identifiers removed' },
                        { id: 'expert', label: 'Expert Determination', desc: 'Statistical verification' }
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
                      <div className="text-2xl font-bold text-emerald-400">1,593</div>
                      <div className="text-xs text-white/40">Patients</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{totalVars}</div>
                      <div className="text-xs text-white/40">Variables</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">~2 days</div>
                      <div className="text-xs text-white/40">Est. Time</div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button 
                    onClick={() => setStep(3)}
                    className="flex-1 bg-white/10 hover:bg-white/20 py-3 font-medium transition-colors"
                  >
                    ← Back
                  </button>
                  <button 
                    onClick={() => setExtracting(true)}
                    className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-black font-medium py-3 transition-colors"
                  >
                    Start Extraction
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
                <h2 className="text-xl font-semibold mb-2">Extraction Queued</h2>
                <p className="text-white/40 mb-6">
                  1,593 patients · {totalVars} variables · Est. completion: 2 days
                </p>
                
                <div className="bg-white/5 p-4 text-left mb-6">
                  <div className="text-sm space-y-2">
                    <div className="flex justify-between">
                      <span className="text-white/40">Job ID</span>
                      <span className="font-mono text-emerald-400">extract_{Date.now().toString(36)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/40">Study</span>
                      <span>{studyName || 'Untitled Study'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/40">Format</span>
                      <span>{outputFormat.toUpperCase()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/40">De-identification</span>
                      <span>{deidentLevel.replace(/_/g, ' ')}</span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 justify-center">
                  <Link to="/research" className="bg-white/10 hover:bg-white/20 px-4 py-2 text-sm transition-colors">
                    View All Jobs
                  </Link>
                  <button 
                    onClick={() => { 
                      setStep(1); 
                      setFeasibilityRun(false); 
                      setExtracting(false);
                      setStudyName('');
                    }}
                    className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium px-4 py-2 text-sm transition-colors"
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
