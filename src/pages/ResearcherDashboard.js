import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

const ResearcherDashboard = () => {
  const [selectedCancerTypes, setSelectedCancerTypes] = useState([]);
  const [selectedStages, setSelectedStages] = useState([]);
  const [selectedTreatments, setSelectedTreatments] = useState([]);
  const [showResults, setShowResults] = useState(false);

  const cancerTypes = [
    'Diffuse Large B-Cell Lymphoma',
    'Acute Myeloid Leukemia',
    'Multiple Myeloma',
    'Chronic Lymphocytic Leukemia',
    'Follicular Lymphoma',
    'Mantle Cell Lymphoma',
    'Non-Small Cell Lung Cancer',
    'Breast Cancer',
  ];

  const stages = ['I', 'II', 'III', 'IV'];
  
  const treatments = [
    'Chemotherapy',
    'Immunotherapy',
    'Targeted Therapy',
    'CAR-T',
    'Stem Cell Transplant',
    'Radiation',
  ];

  const toggleSelection = (item, selected, setSelected) => {
    if (selected.includes(item)) {
      setSelected(selected.filter((i) => i !== item));
    } else {
      setSelected([...selected, item]);
    }
  };

  const handleBuildCohort = () => {
    setShowResults(true);
  };

  // Mock cohort results
  const cohortResults = {
    patientCount: 1247,
    dataPoints: 42680,
    completeness: 91.5,
    demographics: {
      meanAge: 58.4,
      malePercent: 52,
    },
    outcomes: {
      overallResponse: 72.5,
      completeResponse: 48.2,
      medianPFS: 18.5,
      medianOS: 42.0,
    },
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-blue-600 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold mb-2">Researcher Dashboard</h1>
          <p className="text-indigo-100">Build cohorts and access longitudinal cancer data</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Cohort Builder */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-semibold text-slate-900 mb-6">Build Your Cohort</h2>
              
              {/* Cancer Types */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-3">
                  Cancer Types
                </label>
                <div className="flex flex-wrap gap-2">
                  {cancerTypes.map((type) => (
                    <button
                      key={type}
                      onClick={() => toggleSelection(type, selectedCancerTypes, setSelectedCancerTypes)}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                        selectedCancerTypes.includes(type)
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </div>

              {/* Stages */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-3">
                  Disease Stage
                </label>
                <div className="flex gap-2">
                  {stages.map((stage) => (
                    <button
                      key={stage}
                      onClick={() => toggleSelection(stage, selectedStages, setSelectedStages)}
                      className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
                        selectedStages.includes(stage)
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      Stage {stage}
                    </button>
                  ))}
                </div>
              </div>

              {/* Treatments */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-3">
                  Treatment Types
                </label>
                <div className="flex flex-wrap gap-2">
                  {treatments.map((treatment) => (
                    <button
                      key={treatment}
                      onClick={() => toggleSelection(treatment, selectedTreatments, setSelectedTreatments)}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                        selectedTreatments.includes(treatment)
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {treatment}
                    </button>
                  ))}
                </div>
              </div>

              {/* Additional Filters */}
              <div className="grid md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Age Range
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    <span className="text-slate-400">—</span>
                    <input
                      type="number"
                      placeholder="Max"
                      className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Minimum Follow-up (months)
                  </label>
                  <input
                    type="number"
                    placeholder="12"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Molecular Markers */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Molecular Markers (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g., MYC, BCL2, TP53, FLT3-ITD"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <button
                onClick={handleBuildCohort}
                className="w-full py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg font-semibold hover:from-indigo-600 hover:to-purple-700 transition-all"
              >
                Build Cohort
              </button>
            </div>

            {/* Results */}
            {showResults && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-xl shadow-sm p-6"
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-slate-900">Cohort Results</h2>
                  <div className="flex gap-2">
                    <button className="px-4 py-2 text-indigo-600 border border-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-50">
                      Save Cohort
                    </button>
                    <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700">
                      Export Data
                    </button>
                  </div>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                  <div className="bg-indigo-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-indigo-600">{cohortResults.patientCount.toLocaleString()}</div>
                    <div className="text-sm text-slate-600">Patients</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-purple-600">{cohortResults.dataPoints.toLocaleString()}</div>
                    <div className="text-sm text-slate-600">Data Points</div>
                  </div>
                  <div className="bg-emerald-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-emerald-600">{cohortResults.completeness}%</div>
                    <div className="text-sm text-slate-600">Completeness</div>
                  </div>
                  <div className="bg-amber-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-amber-600">{cohortResults.demographics.meanAge}</div>
                    <div className="text-sm text-slate-600">Mean Age</div>
                  </div>
                </div>

                {/* Outcomes Preview */}
                <div className="border border-slate-200 rounded-lg p-4">
                  <h3 className="font-semibold text-slate-900 mb-4">Outcome Summary (Preview)</h3>
                  <div className="grid md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-slate-500">Overall Response Rate</div>
                      <div className="text-lg font-semibold text-slate-900">{cohortResults.outcomes.overallResponse}%</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500">Complete Response</div>
                      <div className="text-lg font-semibold text-slate-900">{cohortResults.outcomes.completeResponse}%</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500">Median PFS</div>
                      <div className="text-lg font-semibold text-slate-900">{cohortResults.outcomes.medianPFS} mo</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500">Median OS</div>
                      <div className="text-lg font-semibold text-slate-900">{cohortResults.outcomes.medianOS} mo</div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="font-semibold text-slate-900 mb-4">Available Data</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Total Patients</span>
                  <span className="font-semibold text-slate-900">45,000+</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Cancer Types</span>
                  <span className="font-semibold text-slate-900">28</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Data Points</span>
                  <span className="font-semibold text-slate-900">2.5M+</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Avg Follow-up</span>
                  <span className="font-semibold text-slate-900">3.2 years</span>
                </div>
              </div>
            </div>

            {/* Saved Cohorts */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="font-semibold text-slate-900 mb-4">Recent Cohorts</h3>
              <div className="space-y-3">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="font-medium text-slate-900 text-sm">DLBCL CAR-T Responders</div>
                  <div className="text-xs text-slate-500">892 patients • Jan 2, 2026</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="font-medium text-slate-900 text-sm">AML FLT3+ Outcomes</div>
                  <div className="text-xs text-slate-500">1,245 patients • Dec 28, 2025</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="font-medium text-slate-900 text-sm">Myeloma Transplant Study</div>
                  <div className="text-xs text-slate-500">567 patients • Dec 15, 2025</div>
                </div>
              </div>
            </div>

            {/* Data Marketplace CTA */}
            <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
              <h3 className="font-semibold mb-2">Need Pre-Built Datasets?</h3>
              <p className="text-sm text-indigo-100 mb-4">
                Browse our marketplace for curated, analysis-ready datasets.
              </p>
              <Link
                to="/marketplace"
                className="block text-center py-2 bg-white text-indigo-600 rounded-lg font-medium hover:bg-indigo-50 transition-all"
              >
                View Marketplace
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResearcherDashboard;

