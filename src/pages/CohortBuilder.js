import { useState } from 'react';
import { Search, Plus, X, Database, FileText, Building2, Users, ChevronRight, Check, AlertCircle } from 'lucide-react';

export default function HealthDBCohortBuilder() {
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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6" style={{ fontFamily: "'IBM Plex Sans', -apple-system, sans-serif" }}>
      {/* Header */}
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-cyan-500 rounded-lg flex items-center justify-center">
            <Database className="w-6 h-6 text-slate-950" />
          </div>
          <div>
            <h1 className="text-xl font-semibold tracking-tight">HealthDB.ai</h1>
            <p className="text-slate-500 text-sm">Longitudinal Cancer Research Database</p>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center gap-2 mb-8 text-sm">
          {['Define Cohort', 'Select Variables', 'Regulatory', 'Extract'].map((label, i) => (
            <div key={i} className="flex items-center">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                step === i + 1 ? 'bg-emerald-500/20 text-emerald-400' :
                step > i + 1 ? 'bg-slate-800 text-slate-400' : 'bg-slate-900 text-slate-600'
              }`}>
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                  step > i + 1 ? 'bg-emerald-500 text-slate-950' : 'bg-slate-700'
                }`}>
                  {step > i + 1 ? <Check className="w-3 h-3" /> : i + 1}
                </span>
                {label}
              </div>
              {i < 3 && <ChevronRight className="w-4 h-4 text-slate-700 mx-1" />}
            </div>
          ))}
        </div>

        {/* Step 1: Cohort Builder */}
        {step === 1 && (
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2 space-y-4">
              {/* Inclusions */}
              <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-medium text-emerald-400">Inclusion Criteria</h2>
                  <button className="text-xs bg-slate-800 hover:bg-slate-700 px-2 py-1 rounded flex items-center gap-1">
                    <Plus className="w-3 h-3" /> Add Rule
                  </button>
                </div>
                <div className="space-y-2">
                  {inclusions.map((rule, i) => (
                    <div key={i} className="flex items-center gap-2 bg-slate-800/50 rounded-lg p-3">
                      <select className="bg-slate-700 rounded px-2 py-1 text-sm border-0 focus:ring-1 focus:ring-emerald-500">
                        <option>{rule.field}</option>
                      </select>
                      <select className="bg-slate-700 rounded px-2 py-1 text-sm border-0">
                        <option>{rule.operator}</option>
                      </select>
                      <input
                        className="flex-1 bg-slate-700 rounded px-3 py-1 text-sm border-0 focus:ring-1 focus:ring-emerald-500"
                        value={rule.value}
                        readOnly
                      />
                      <button className="text-slate-500 hover:text-red-400">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Exclusions */}
              <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-medium text-amber-400">Exclusion Criteria</h2>
                  <button className="text-xs bg-slate-800 hover:bg-slate-700 px-2 py-1 rounded flex items-center gap-1">
                    <Plus className="w-3 h-3" /> Add Rule
                  </button>
                </div>
                <div className="space-y-2">
                  {exclusions.map((rule, i) => (
                    <div key={i} className="flex items-center gap-2 bg-slate-800/50 rounded-lg p-3">
                      <input
                        type="checkbox"
                        checked={rule.enabled}
                        onChange={() => {
                          const updated = [...exclusions];
                          updated[i].enabled = !updated[i].enabled;
                          setExclusions(updated);
                        }}
                        className="rounded bg-slate-700 border-slate-600 text-emerald-500 focus:ring-emerald-500"
                      />
                      <span className={`text-sm ${rule.enabled ? '' : 'text-slate-500 line-through'}`}>
                        {rule.field} {rule.operator} {rule.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Feasibility Panel */}
            <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
              <h2 className="font-medium mb-4">Feasibility Check</h2>

              {!feasibilityRun ? (
                <button
                  onClick={() => setFeasibilityRun(true)}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium py-2 rounded-lg mb-4 transition-colors"
                >
                  Run Query
                </button>
              ) : (
                <>
                  <div className="text-center mb-4">
                    <div className="text-4xl font-bold text-emerald-400">1,593</div>
                    <div className="text-slate-500 text-sm">eligible patients</div>
                  </div>

                  <div className="space-y-3">
                    {institutions.map((inst, i) => (
                      <div key={i} className="bg-slate-800/50 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{inst.name}</span>
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            inst.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' :
                            inst.status === 'pending' ? 'bg-amber-500/20 text-amber-400' :
                            'bg-slate-700 text-slate-400'
                          }`}>
                            {inst.status}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">N = {inst.n}</span>
                          <span className="text-slate-500">{inst.completeness}% complete</span>
                        </div>
                        <div className="mt-2 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full"
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
                className={`w-full mt-4 py-2 rounded-lg font-medium transition-colors ${
                  feasibilityRun
                    ? 'bg-slate-800 hover:bg-slate-700 text-slate-100'
                    : 'bg-slate-800/50 text-slate-600 cursor-not-allowed'
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
              <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <h2 className="font-medium mb-4">Select Variables to Extract</h2>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(variables).map(([category, vars]) => (
                    <div key={category} className="bg-slate-800/50 rounded-lg p-4">
                      <h3 className="text-sm font-medium text-slate-300 mb-3 capitalize">{category}</h3>
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
                              className="rounded bg-slate-700 border-slate-600 text-emerald-500 focus:ring-emerald-500"
                            />
                            <span className="text-slate-400">{v.replace(/_/g, ' ')}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
              <h2 className="font-medium mb-4">Selection Summary</h2>
              <div className="space-y-3 mb-4">
                {Object.entries(selectedVars).map(([cat, vars]) => vars.length > 0 && (
                  <div key={cat} className="text-sm">
                    <span className="text-slate-500 capitalize">{cat}:</span>
                    <span className="text-emerald-400 ml-2">{vars.length} selected</span>
                  </div>
                ))}
              </div>

              <div className="bg-slate-800 rounded-lg p-3 mb-4">
                <div className="flex items-center gap-2 text-sm">
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                  <span className="text-slate-400">Estimated completeness: 87%</span>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 py-2 rounded-lg text-sm"
                >
                  ← Back
                </button>
                <button
                  onClick={() => setStep(3)}
                  className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium py-2 rounded-lg text-sm"
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
              <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <h2 className="font-medium mb-4">Regulatory Pipeline</h2>
                <div className="space-y-3">
                  {regulatorySteps.map((item, i) => (
                    <div key={i} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          item.status === 'approved' || item.status === 'signed' ? 'bg-emerald-500/20' :
                          item.status === 'pending' ? 'bg-amber-500/20' : 'bg-slate-700'
                        }`}>
                          {item.status === 'approved' || item.status === 'signed' ? (
                            <Check className="w-4 h-4 text-emerald-400" />
                          ) : item.status === 'pending' ? (
                            <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
                          ) : (
                            <div className="w-2 h-2 bg-slate-500 rounded-full" />
                          )}
                        </div>
                        <div>
                          <div className="font-medium">{item.name}</div>
                          <div className="text-xs text-slate-500">
                            {item.status === 'approved' || item.status === 'signed'
                              ? `Completed ${item.date}`
                              : item.status === 'pending'
                                ? 'Under review (est. 3 days)'
                                : 'Not started'}
                          </div>
                        </div>
                      </div>
                      <button className="text-xs bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded">
                        {item.status === 'not_started' ? 'Generate' : 'View'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
                <h2 className="font-medium mb-3">Quick Actions</h2>
                <div className="space-y-2">
                  <button className="w-full bg-slate-800 hover:bg-slate-700 py-2 rounded-lg text-sm flex items-center justify-center gap-2">
                    <FileText className="w-4 h-4" /> Download IRB Protocol
                  </button>
                  <button className="w-full bg-slate-800 hover:bg-slate-700 py-2 rounded-lg text-sm flex items-center justify-center gap-2">
                    <FileText className="w-4 h-4" /> Download DUA Template
                  </button>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 py-2 rounded-lg text-sm"
                >
                  ← Back
                </button>
                <button
                  onClick={() => setStep(4)}
                  className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium py-2 rounded-lg text-sm"
                >
                  Extract Data →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Extract */}
        {step === 4 && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-slate-900 rounded-xl p-8 border border-slate-800 text-center">
              <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Database className="w-8 h-8 text-emerald-400" />
              </div>
              <h2 className="text-xl font-semibold mb-2">Data Extraction Queued</h2>
              <p className="text-slate-400 mb-6">
                Your cohort of 1,593 patients with 15 variables is being prepared.
                Estimated completion: January 13, 2025
              </p>

              <div className="bg-slate-800 rounded-lg p-4 text-left mb-6">
                <div className="text-sm space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Job ID:</span>
                    <span className="font-mono text-emerald-400">extract_mm_bispab_001</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Format:</span>
                    <span>CSV (REDCap-ready)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">De-identification:</span>
                    <span>Limited Dataset</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 justify-center">
                <button className="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg text-sm">
                  View All Jobs
                </button>
                <button
                  onClick={() => setStep(1)}
                  className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium px-4 py-2 rounded-lg text-sm"
                >
                  Start New Query
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
