import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const CohortBuilder = () => {
  const [step, setStep] = useState(1);
  const [inclusions, setInclusions] = useState([
    { field: 'Diagnosis', operator: 'IS', value: 'Multiple Myeloma (C90.0)' },
    { field: 'Treatment', operator: 'INCLUDES', value: 'Bispecific antibody' }
  ]);
  const [exclusions, setExclusions] = useState([
    { field: 'Prior CAR-T', operator: 'IS', value: 'TRUE', enabled: true }
  ]);
  const [selectedVars, setSelectedVars] = useState({
    demographics: ['age_at_dx', 'sex'],
    labs: ['hemoglobin', 'ldh', 'b2m'],
    staging: ['iss', 'riss'],
    outcomes: ['pfs', 'os', 'crs_grade', 'icans_grade']
  });
  const [feasibilityRun, setFeasibilityRun] = useState(false);

  const institutions = [
    { name: 'OHSU Knight', n: 847, completeness: 92, status: 'active' },
    { name: 'Fred Hutchinson', n: 512, completeness: 87, status: 'pending' },
    { name: 'Emory Winship', n: 234, completeness: 78, status: 'setup' }
  ];

  const variables = {
    demographics: ['age_at_dx', 'sex', 'race', 'zip_3digit'],
    labs: ['hemoglobin', 'creatinine', 'ldh', 'b2m', 'flc_kappa', 'flc_lambda'],
    staging: ['iss', 'riss', 'bone_lesions', 'extramedullary'],
    treatments: ['regimen', 'start_date', 'stop_date', 'cycles', 'best_response'],
    outcomes: ['pfs', 'os', 'crs_grade', 'icans_grade', 'infections'],
    cytogenetics: ['del17p', 't_4_14', 't_14_16', 'gain_1q']
  };

  const regulatorySteps = [
    { name: 'Central IRB', status: 'approved', date: '2025-01-05' },
    { name: 'Data Use Agreement', status: 'signed', date: '2025-01-06' },
    { name: 'OHSU Reliance', status: 'pending', date: null },
    { name: 'Fred Hutch Reliance', status: 'not_started', date: null }
  ];

  const steps = ['Define Cohort', 'Select Variables', 'Regulatory', 'Extract'];

  return (
    <div className="min-h-screen bg-black text-white pt-20 pb-12 px-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link to="/research" className="text-white/40 text-sm hover:text-white/60 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-2xl font-semibold">Cohort Builder</h1>
          <p className="text-white/40 text-sm">Define criteria, select variables, complete regulatory</p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center gap-2 mb-8 text-sm">
          {steps.map((label, i) => (
            <div key={i} className="flex items-center">
              <button
                onClick={() => i + 1 <= step && setStep(i + 1)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full transition-colors ${
                  step === i + 1 ? 'bg-emerald-500/20 text-emerald-400' : 
                  step > i + 1 ? 'bg-white/10 text-white/60 hover:bg-white/20' : 'bg-white/5 text-white/30'
                }`}
              >
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
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
              {/* Inclusions */}
              <div className="bg-white/5 border border-white/10 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-medium text-emerald-400">Inclusion Criteria</h2>
                  <button className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1.5 transition-colors">
                    + Add Rule
                  </button>
                </div>
                <div className="space-y-2">
                  {inclusions.map((rule, i) => (
                    <div key={i} className="flex items-center gap-2 bg-white/5 p-3">
                      <select className="bg-white/10 border-0 px-2 py-1 text-sm focus:ring-1 focus:ring-emerald-500">
                        <option>{rule.field}</option>
                      </select>
                      <select className="bg-white/10 border-0 px-2 py-1 text-sm">
                        <option>{rule.operator}</option>
                      </select>
                      <input 
                        className="flex-1 bg-white/10 border-0 px-3 py-1 text-sm focus:ring-1 focus:ring-emerald-500"
                        value={rule.value}
                        readOnly
                      />
                      <button className="text-white/30 hover:text-red-400 p-1">×</button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Exclusions */}
              <div className="bg-white/5 border border-white/10 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-medium text-amber-400">Exclusion Criteria</h2>
                  <button className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1.5 transition-colors">
                    + Add Rule
                  </button>
                </div>
                <div className="space-y-2">
                  {exclusions.map((rule, i) => (
                    <div key={i} className="flex items-center gap-3 bg-white/5 p-3">
                      <input 
                        type="checkbox" 
                        checked={rule.enabled}
                        onChange={() => {
                          const updated = [...exclusions];
                          updated[i].enabled = !updated[i].enabled;
                          setExclusions(updated);
                        }}
                        className="rounded bg-white/10 border-white/20 text-emerald-500 focus:ring-emerald-500"
                      />
                      <span className={`text-sm ${rule.enabled ? '' : 'text-white/30 line-through'}`}>
                        {rule.field} {rule.operator} {rule.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Feasibility Panel */}
            <div className="bg-white/5 border border-white/10 p-5">
              <h2 className="font-medium mb-4">Feasibility</h2>
              
              {!feasibilityRun ? (
                <button 
                  onClick={() => setFeasibilityRun(true)}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 text-black font-medium py-2 mb-4 transition-colors"
                >
                  Run Query
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
          </div>
        )}

        {/* Step 2: Variable Selection */}
        {step === 2 && (
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2">
              <div className="bg-white/5 border border-white/10 p-5">
                <h2 className="font-medium mb-4">Select Variables</h2>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(variables).map(([category, vars]) => (
                    <div key={category} className="bg-white/5 p-4">
                      <h3 className="text-sm font-medium text-white/60 mb-3 capitalize">{category}</h3>
                      <div className="space-y-2">
                        {vars.map(v => (
                          <label key={v} className="flex items-center gap-2 text-sm cursor-pointer hover:text-emerald-400">
                            <input 
                              type="checkbox" 
                              checked={selectedVars[category]?.includes(v)}
                              onChange={() => {
                                const updated = { ...selectedVars };
                                if (!updated[category]) updated[category] = [];
                                if (updated[category].includes(v)) {
                                  updated[category] = updated[category].filter(x => x !== v);
                                } else {
                                  updated[category].push(v);
                                }
                                setSelectedVars(updated);
                              }}
                              className="rounded bg-white/10 border-white/20 text-emerald-500 focus:ring-emerald-500"
                            />
                            <span className="text-white/50">{v.replace(/_/g, ' ')}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 p-5">
              <h2 className="font-medium mb-4">Summary</h2>
              <div className="space-y-3 mb-4">
                {Object.entries(selectedVars).map(([cat, vars]) => vars.length > 0 && (
                  <div key={cat} className="text-sm">
                    <span className="text-white/40 capitalize">{cat}:</span>
                    <span className="text-emerald-400 ml-2">{vars.length}</span>
                  </div>
                ))}
              </div>
              
              <div className="bg-white/5 p-3 mb-4">
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-amber-400">!</span>
                  <span className="text-white/40">Est. completeness: 87%</span>
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
                  className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-black font-medium py-2 text-sm transition-colors"
                >
                  Continue →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Regulatory */}
        {step === 3 && (
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2">
              <div className="bg-white/5 border border-white/10 p-5">
                <h2 className="font-medium mb-4">Regulatory Pipeline</h2>
                <div className="space-y-3">
                  {regulatorySteps.map((item, i) => (
                    <div key={i} className="flex items-center justify-between bg-white/5 p-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
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
                          <div className="font-medium">{item.name}</div>
                          <div className="text-xs text-white/40">
                            {item.status === 'approved' || item.status === 'signed' 
                              ? `Completed ${item.date}` 
                              : item.status === 'pending' 
                                ? 'Under review'
                                : 'Not started'}
                          </div>
                        </div>
                      </div>
                      <button className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1.5 transition-colors">
                        {item.status === 'not_started' ? 'Generate' : 'View'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-white/5 border border-white/10 p-5">
                <h2 className="font-medium mb-3">Quick Actions</h2>
                <div className="space-y-2">
                  <button className="w-full bg-white/10 hover:bg-white/20 py-2 text-sm transition-colors">
                    Download IRB Protocol
                  </button>
                  <button className="w-full bg-white/10 hover:bg-white/20 py-2 text-sm transition-colors">
                    Download DUA Template
                  </button>
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
            <div className="bg-white/5 border border-white/10 p-8 text-center">
              <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl text-emerald-400">✓</span>
              </div>
              <h2 className="text-xl font-semibold mb-2">Extraction Queued</h2>
              <p className="text-white/40 mb-6">
                1,593 patients · 15 variables · Est. completion: Jan 13
              </p>
              
              <div className="bg-white/5 p-4 text-left mb-6">
                <div className="text-sm space-y-2">
                  <div className="flex justify-between">
                    <span className="text-white/40">Job ID</span>
                    <span className="font-mono text-emerald-400">extract_mm_bispab_001</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Format</span>
                    <span>CSV (REDCap-ready)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">De-identification</span>
                    <span>Limited Dataset</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 justify-center">
                <Link to="/research" className="bg-white/10 hover:bg-white/20 px-4 py-2 text-sm transition-colors">
                  View All Jobs
                </Link>
                <button 
                  onClick={() => { setStep(1); setFeasibilityRun(false); }}
                  className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium px-4 py-2 text-sm transition-colors"
                >
                  New Query
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CohortBuilder;
