import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

// Use relative URL in production (same origin), fallback to localhost in dev
const API_URL = process.env.NODE_ENV === 'production' ? '' : (process.env.REACT_APP_API_URL || 'http://localhost:8000');

const PatientPortal = () => {
  const [patientData, setPatientData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const token = localStorage.getItem('token');
    fetch(`${API_URL}/api/patient/dashboard`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => res.json())
      .then(data => {
        setPatientData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch patient data:', err);
        // Demo data for display
        setPatientData({
          consent_status: 'active',
          rewards_points: 450,
          last_contribution: '2024-01-15',
          data_access_log: [],
        });
        setLoading(false);
      });
  }, []);

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'consent', label: 'Consent' },
    { id: 'data', label: 'My Data' },
    { id: 'rewards', label: 'Rewards' },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center pt-20">
        <div className="text-center">
          <div className="w-8 h-8 border border-white/20 border-t-white/60 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white/40 text-sm">Loading your data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black pt-20">
      {/* Header */}
      <section className="py-16 px-6 border-b border-white/5">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex flex-col md:flex-row md:items-end justify-between gap-6"
          >
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
                Patient Portal
              </p>
              <h1 className="heading-display text-4xl md:text-5xl text-white/90">
                Your Dashboard
              </h1>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <p className="text-white/40 text-xs mb-1">Consent Status</p>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-[#00d4aa] rounded-full"></span>
                  <span className="text-[#00d4aa] uppercase text-sm tracking-wider">
                    {patientData?.consent_status || 'Active'}
                  </span>
                </div>
              </div>
              <div className="h-8 w-px bg-white/10"></div>
              <div className="text-right">
                <p className="text-white/40 text-xs mb-1">Rewards</p>
                <p className="text-white font-mono text-lg">
                  {patientData?.rewards_points || 0} pts
                </p>
              </div>
            </div>
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
          {activeTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/5 mb-12">
                {[
                  { label: 'Data Points Shared', value: '2,847' },
                  { label: 'Studies Contributing To', value: '12' },
                  { label: 'Rewards Earned', value: `${patientData?.rewards_points || 450}` },
                  { label: 'Data Requests', value: '3' },
                ].map((stat) => (
                  <div key={stat.label} className="card-glass p-6">
                    <p className="text-white/40 text-xs uppercase tracking-wider mb-2">{stat.label}</p>
                    <p className="text-2xl font-light text-white font-mono">{stat.value}</p>
                  </div>
                ))}
              </div>

              {/* Recent Activity */}
              <div className="mb-12">
                <h2 className="text-lg font-medium text-white mb-6">Recent Activity</h2>
                <div className="space-y-px">
                  {[
                    { action: 'Data accessed by Memorial Sloan Kettering', date: '2 hours ago', type: 'access' },
                    { action: 'Treatment update added', date: '1 day ago', type: 'update' },
                    { action: '+25 rewards points earned', date: '3 days ago', type: 'reward' },
                    { action: 'New study invitation received', date: '1 week ago', type: 'invite' },
                  ].map((activity, index) => (
                    <div key={index} className="card-glass card-hover p-4 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-2 h-2 rounded-full ${
                          activity.type === 'access' ? 'bg-blue-400' :
                          activity.type === 'reward' ? 'bg-[#00d4aa]' :
                          activity.type === 'invite' ? 'bg-purple-400' : 'bg-white/40'
                        }`}></div>
                        <span className="text-white/70 text-sm">{activity.action}</span>
                      </div>
                      <span className="text-white/30 text-xs">{activity.date}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Actions */}
              <div>
                <h2 className="text-lg font-medium text-white mb-6">Quick Actions</h2>
                <div className="grid md:grid-cols-3 gap-4">
                  {[
                    { title: 'Update My Data', description: 'Add new treatment or test results', icon: '📝' },
                    { title: 'Manage Consent', description: 'Review and update sharing preferences', icon: '🔒' },
                    { title: 'View Rewards', description: 'See earned points and redeem', icon: '🎁' },
                  ].map((action) => (
                    <button
                      key={action.title}
                      className="card-glass card-hover p-6 text-left group"
                    >
                      <span className="text-2xl mb-4 block">{action.icon}</span>
                      <h3 className="text-white font-medium mb-2 group-hover:text-[#00d4aa] transition-colors">
                        {action.title}
                      </h3>
                      <p className="text-white/40 text-sm">{action.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'consent' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <div className="max-w-2xl">
                <h2 className="text-lg font-medium text-white mb-6">Consent Management</h2>
                <p className="text-white/40 mb-8">
                  Control how your de-identified data is shared with researchers.
                </p>

                <div className="space-y-4">
                  {[
                    { label: 'Share with academic researchers', enabled: true },
                    { label: 'Share with pharmaceutical companies', enabled: false },
                    { label: 'Allow use in AI/ML training', enabled: true },
                    { label: 'Participate in clinical trial matching', enabled: true },
                  ].map((option, index) => (
                    <div key={index} className="card-glass p-4 flex items-center justify-between">
                      <span className="text-white/70">{option.label}</span>
                      <button
                        className={`w-12 h-6 rounded-full transition-colors relative ${
                          option.enabled ? 'bg-[#00d4aa]' : 'bg-white/20'
                        }`}
                      >
                        <span
                          className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                            option.enabled ? 'right-1' : 'left-1'
                          }`}
                        ></span>
                      </button>
                    </div>
                  ))}
                </div>

                <button className="mt-8 px-6 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors">
                  Save Preferences
                </button>
              </div>
            </motion.div>
          )}

          {activeTab === 'data' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <h2 className="text-lg font-medium text-white mb-6">Your Data</h2>
              <p className="text-white/40 mb-8">
                View and manage the de-identified data you've contributed.
              </p>

              <div className="space-y-px">
                {[
                  { category: 'Demographics', records: 1, updated: '2024-01-15' },
                  { category: 'Diagnosis', records: 3, updated: '2024-01-10' },
                  { category: 'Treatment History', records: 8, updated: '2024-01-15' },
                  { category: 'Lab Results', records: 24, updated: '2024-01-12' },
                  { category: 'Imaging', records: 6, updated: '2023-12-20' },
                ].map((item) => (
                  <div key={item.category} className="card-glass card-hover p-4 flex items-center justify-between">
                    <div>
                      <h3 className="text-white font-medium">{item.category}</h3>
                      <p className="text-white/40 text-sm">{item.records} record(s)</p>
                    </div>
                    <div className="flex items-center gap-6">
                      <span className="text-white/30 text-xs">Updated {item.updated}</span>
                      <button className="px-4 py-2 border border-white/20 text-white/60 text-xs uppercase tracking-wider hover:bg-white hover:text-black transition-all">
                        View
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'rewards' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <div className="grid md:grid-cols-2 gap-8">
                <div>
                  <h2 className="text-lg font-medium text-white mb-6">Your Rewards</h2>
                  <div className="card-glass p-8 mb-8">
                    <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Total Points</p>
                    <p className="text-5xl font-light text-white font-mono mb-4">
                      {patientData?.rewards_points || 450}
                    </p>
                    <p className="text-white/40 text-sm">
                      ≈ ${((patientData?.rewards_points || 450) * 0.10).toFixed(2)} value
                    </p>
                  </div>
                  <button className="w-full py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors">
                    Redeem Points
                  </button>
                </div>

                <div>
                  <h2 className="text-lg font-medium text-white mb-6">Earning History</h2>
                  <div className="space-y-px">
                    {[
                      { action: 'Treatment update', points: '+25', date: '3 days ago' },
                      { action: 'Monthly participation', points: '+100', date: '1 week ago' },
                      { action: 'Survey completed', points: '+50', date: '2 weeks ago' },
                      { action: 'Data quality bonus', points: '+75', date: '1 month ago' },
                    ].map((item, index) => (
                      <div key={index} className="card-glass p-4 flex items-center justify-between">
                        <div>
                          <p className="text-white/70 text-sm">{item.action}</p>
                          <p className="text-white/30 text-xs">{item.date}</p>
                        </div>
                        <span className="text-[#00d4aa] font-mono">{item.points}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </section>
    </div>
  );
};

export default PatientPortal;
