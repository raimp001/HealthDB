import React, { useState } from 'react';
import { motion } from 'framer-motion';

const PatientPortal = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Mock patient data
  const patientData = {
    points: 450,
    cashValue: 4.50,
    consentsActive: 3,
    studiesContributing: 12,
    dataAccesses: 8,
  };

  const consents = [
    { id: 1, type: 'General Research', status: 'active', signedDate: '2025-01-15', expiresAt: '2026-01-15' },
    { id: 2, type: 'Commercial Research', status: 'active', signedDate: '2025-01-15', expiresAt: '2026-01-15' },
    { id: 3, type: 'Genetic Research', status: 'pending', signedDate: null, expiresAt: null },
  ];

  const rewards = [
    { date: '2026-01-03', activity: 'Data accessed by researcher', points: 50 },
    { date: '2026-01-02', activity: 'Completed health survey', points: 15 },
    { date: '2025-12-28', activity: 'Data contributed to study', points: 50 },
    { date: '2025-12-20', activity: 'Profile verification bonus', points: 100 },
    { date: '2025-12-15', activity: 'Initial consent bonus', points: 100 },
  ];

  const accessLog = [
    { date: '2026-01-03', institution: 'Stanford Cancer Center', dataType: 'Treatment outcomes', purpose: 'Treatment optimization study' },
    { date: '2025-12-28', institution: 'NIH Lymphoma Study', dataType: 'All de-identified', purpose: 'Longitudinal outcomes research' },
    { date: '2025-12-15', institution: 'Mayo Clinic Research', dataType: 'Lab results', purpose: 'Biomarker analysis' },
  ];

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'consents', label: 'My Consents', icon: '📝' },
    { id: 'rewards', label: 'Rewards', icon: '🎁' },
    { id: 'access', label: 'Access Log', icon: '🔍' },
    { id: 'data', label: 'My Data', icon: '💾' },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Patient Portal</h1>
              <p className="text-purple-100">Manage your data, earn rewards, and contribute to research</p>
            </div>
            <div className="hidden md:flex items-center space-x-4">
              <div className="text-center bg-white/10 backdrop-blur rounded-xl px-6 py-3">
                <div className="text-3xl font-bold">{patientData.points}</div>
                <div className="text-sm text-purple-100">Points Balance</div>
              </div>
              <div className="text-center bg-white/10 backdrop-blur rounded-xl px-6 py-3">
                <div className="text-3xl font-bold">${patientData.cashValue.toFixed(2)}</div>
                <div className="text-sm text-purple-100">Cash Value</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <div className="lg:w-64 flex-shrink-0">
            <nav className="bg-white rounded-xl shadow-sm p-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center px-4 py-3 rounded-lg text-left text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? 'bg-purple-50 text-purple-600'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <span className="text-xl mr-3">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content Area */}
          <div className="flex-grow">
            {activeTab === 'dashboard' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white rounded-xl p-6 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-slate-500 text-sm">Active Consents</p>
                        <p className="text-3xl font-bold text-slate-900">{patientData.consentsActive}</p>
                      </div>
                      <div className="text-4xl">📝</div>
                    </div>
                  </div>
                  <div className="bg-white rounded-xl p-6 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-slate-500 text-sm">Studies Contributing To</p>
                        <p className="text-3xl font-bold text-slate-900">{patientData.studiesContributing}</p>
                      </div>
                      <div className="text-4xl">🔬</div>
                    </div>
                  </div>
                  <div className="bg-white rounded-xl p-6 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-slate-500 text-sm">Data Accesses</p>
                        <p className="text-3xl font-bold text-slate-900">{patientData.dataAccesses}</p>
                      </div>
                      <div className="text-4xl">👁️</div>
                    </div>
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-white rounded-xl p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-slate-900 mb-4">Recent Activity</h3>
                  <div className="space-y-4">
                    {rewards.slice(0, 3).map((item, index) => (
                      <div key={index} className="flex items-center justify-between border-b border-slate-100 pb-4 last:border-0">
                        <div>
                          <p className="text-slate-900 font-medium">{item.activity}</p>
                          <p className="text-slate-500 text-sm">{item.date}</p>
                        </div>
                        <span className="text-green-600 font-semibold">+{item.points} pts</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button className="bg-gradient-to-r from-purple-500 to-indigo-500 text-white rounded-xl p-6 text-left hover:from-purple-600 hover:to-indigo-600 transition-all">
                    <span className="text-2xl">📋</span>
                    <h3 className="text-lg font-semibold mt-2">Complete Health Survey</h3>
                    <p className="text-purple-100 text-sm">Earn 50 points</p>
                  </button>
                  <button className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl p-6 text-left hover:from-emerald-600 hover:to-teal-600 transition-all">
                    <span className="text-2xl">🎁</span>
                    <h3 className="text-lg font-semibold mt-2">Redeem Rewards</h3>
                    <p className="text-emerald-100 text-sm">{patientData.points} points available</p>
                  </button>
                </div>
              </motion.div>
            )}

            {activeTab === 'consents' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-xl shadow-sm"
              >
                <div className="p-6 border-b border-slate-100">
                  <h2 className="text-xl font-semibold text-slate-900">Manage Your Consents</h2>
                  <p className="text-slate-500 mt-1">Control how your data is used in research</p>
                </div>
                <div className="divide-y divide-slate-100">
                  {consents.map((consent) => (
                    <div key={consent.id} className="p-6 flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-slate-900">{consent.type}</h3>
                        {consent.signedDate ? (
                          <p className="text-slate-500 text-sm">
                            Signed: {consent.signedDate} • Expires: {consent.expiresAt}
                          </p>
                        ) : (
                          <p className="text-slate-500 text-sm">Not yet signed</p>
                        )}
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          consent.status === 'active'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {consent.status === 'active' ? 'Active' : 'Pending'}
                        </span>
                        {consent.status === 'pending' ? (
                          <button className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700">
                            Sign Now
                          </button>
                        ) : (
                          <button className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-medium">
                            Manage
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'rewards' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Rewards Summary */}
                <div className="bg-gradient-to-r from-amber-400 to-orange-500 rounded-xl p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-2xl font-bold mb-2">Your Rewards</h2>
                      <p className="text-amber-100">Thank you for contributing to research!</p>
                    </div>
                    <div className="text-right">
                      <div className="text-4xl font-bold">{patientData.points}</div>
                      <div className="text-amber-100">Points (${patientData.cashValue.toFixed(2)})</div>
                    </div>
                  </div>
                  <button className="mt-4 px-6 py-2 bg-white text-orange-600 rounded-lg font-semibold hover:bg-orange-50 transition-all">
                    Redeem Points
                  </button>
                </div>

                {/* History */}
                <div className="bg-white rounded-xl shadow-sm">
                  <div className="p-6 border-b border-slate-100">
                    <h3 className="text-lg font-semibold text-slate-900">Points History</h3>
                  </div>
                  <div className="divide-y divide-slate-100">
                    {rewards.map((item, index) => (
                      <div key={index} className="p-6 flex items-center justify-between">
                        <div>
                          <p className="font-medium text-slate-900">{item.activity}</p>
                          <p className="text-slate-500 text-sm">{item.date}</p>
                        </div>
                        <span className="text-green-600 font-bold text-lg">+{item.points}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'access' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-xl shadow-sm"
              >
                <div className="p-6 border-b border-slate-100">
                  <h2 className="text-xl font-semibold text-slate-900">Data Access Log</h2>
                  <p className="text-slate-500 mt-1">See who has accessed your de-identified data</p>
                </div>
                <div className="divide-y divide-slate-100">
                  {accessLog.map((item, index) => (
                    <div key={index} className="p-6">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-slate-900">{item.institution}</h3>
                          <p className="text-slate-600 mt-1">{item.purpose}</p>
                          <p className="text-slate-500 text-sm mt-2">
                            Data accessed: <span className="font-medium">{item.dataType}</span>
                          </p>
                        </div>
                        <div className="text-right">
                          <span className="text-slate-500 text-sm">{item.date}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'data' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <h2 className="text-xl font-semibold text-slate-900 mb-4">Your Health Data</h2>
                  <p className="text-slate-600 mb-6">
                    View a summary of the de-identified data you're sharing with researchers.
                    All identifying information has been removed or encrypted.
                  </p>
                  
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="border border-slate-200 rounded-lg p-4">
                      <h3 className="font-semibold text-slate-700 mb-2">Demographics</h3>
                      <ul className="space-y-2 text-sm text-slate-600">
                        <li>Age Range: 50-60</li>
                        <li>Sex: Male</li>
                        <li>Region: Northeast US</li>
                      </ul>
                    </div>
                    <div className="border border-slate-200 rounded-lg p-4">
                      <h3 className="font-semibold text-slate-700 mb-2">Diagnosis</h3>
                      <ul className="space-y-2 text-sm text-slate-600">
                        <li>Cancer Type: Diffuse Large B-Cell Lymphoma</li>
                        <li>Stage at Diagnosis: III</li>
                        <li>Year Diagnosed: 2023</li>
                      </ul>
                    </div>
                    <div className="border border-slate-200 rounded-lg p-4">
                      <h3 className="font-semibold text-slate-700 mb-2">Treatments</h3>
                      <ul className="space-y-2 text-sm text-slate-600">
                        <li>R-CHOP (6 cycles)</li>
                        <li>Response: Complete Remission</li>
                      </ul>
                    </div>
                    <div className="border border-slate-200 rounded-lg p-4">
                      <h3 className="font-semibold text-slate-700 mb-2">Follow-up</h3>
                      <ul className="space-y-2 text-sm text-slate-600">
                        <li>Status: In Remission</li>
                        <li>Time Since Treatment: 18 months</li>
                        <li>Last Scan: Negative</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
                  <h3 className="font-semibold text-blue-900 mb-2">🔒 Your Privacy is Protected</h3>
                  <p className="text-blue-700 text-sm">
                    Your data is de-identified using industry-standard techniques. Your name, 
                    medical record number, and other identifiers are never shared with researchers.
                  </p>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientPortal;

