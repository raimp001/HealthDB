import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

// Use relative URL in production (same origin), fallback to localhost in dev
const API_URL = process.env.NODE_ENV === 'production' ? '' : (process.env.REACT_APP_API_URL || 'http://localhost:8000');

const PatientPortal = () => {
  const [profile, setProfile] = useState(null);
  const [consents, setConsents] = useState([]);
  const [rewards, setRewards] = useState(null);
  const [accessLog, setAccessLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    if (!token) {
      navigate('/login');
      return;
    }

    if (user.user_type !== 'patient') {
      navigate('/research');
      return;
    }

    const fetchData = async () => {
      try {
        const headers = { Authorization: `Bearer ${token}` };

        // Fetch profile
        const profileRes = await fetch(`${API_URL}/api/patient/profile`, { headers });
        if (profileRes.ok) {
          setProfile(await profileRes.json());
        }

        // Fetch consents
        const consentsRes = await fetch(`${API_URL}/api/patient/consents`, { headers });
        if (consentsRes.ok) {
          setConsents(await consentsRes.json());
        }

        // Fetch rewards
        const rewardsRes = await fetch(`${API_URL}/api/patient/rewards`, { headers });
        if (rewardsRes.ok) {
          setRewards(await rewardsRes.json());
        }

        // Fetch access log
        const logRes = await fetch(`${API_URL}/api/patient/data-access-log`, { headers });
        if (logRes.ok) {
          setAccessLog(await logRes.json());
        }

        setLoading(false);
      } catch (err) {
        console.error('Failed to fetch patient data:', err);
        setError('Failed to load your data. Please try again.');
        setLoading(false);
      }
    };

    fetchData();
  }, [navigate]);

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

  if (error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center pt-20">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-white text-black text-sm"
          >
            Retry
          </button>
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
                  <span className={`w-2 h-2 rounded-full ${consents.some(c => c.status === 'active') ? 'bg-[#00d4aa]' : 'bg-white/30'}`}></span>
                  <span className={`uppercase text-sm tracking-wider ${consents.some(c => c.status === 'active') ? 'text-[#00d4aa]' : 'text-white/40'}`}>
                    {consents.some(c => c.status === 'active') ? 'Active' : 'No Active Consent'}
                  </span>
                </div>
              </div>
              <div className="h-8 w-px bg-white/10"></div>
              <div className="text-right">
                <p className="text-white/40 text-xs mb-1">Rewards</p>
                <p className="text-white font-mono text-lg">
                  {profile?.points_balance || 0} pts
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
                <div className="card-glass p-6">
                  <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Points Balance</p>
                  <p className="text-2xl font-light text-white font-mono">{profile?.points_balance || 0}</p>
                </div>
                <div className="card-glass p-6">
                  <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Active Consents</p>
                  <p className="text-2xl font-light text-white font-mono">{profile?.consents_active || 0}</p>
                </div>
                <div className="card-glass p-6">
                  <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Studies Contributing</p>
                  <p className="text-2xl font-light text-white font-mono">{profile?.studies_contributing || 0}</p>
                </div>
                <div className="card-glass p-6">
                  <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Data Accesses</p>
                  <p className="text-2xl font-light text-white font-mono">{profile?.data_accesses || 0}</p>
                </div>
              </div>

              {/* Recent Activity */}
              <div className="mb-12">
                <h2 className="text-lg font-medium text-white mb-6">Recent Data Access</h2>
                {accessLog.length > 0 ? (
                  <div className="space-y-px">
                    {accessLog.slice(0, 5).map((log, index) => (
                      <div key={index} className="card-glass card-hover p-4 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                          <span className="text-white/70 text-sm">
                            {log.institution} accessed {log.data_type} for {log.purpose}
                          </span>
                        </div>
                        <span className="text-white/30 text-xs">{log.date}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="card-glass p-8 text-center">
                    <p className="text-white/40">No data access activity yet</p>
                    <p className="text-white/30 text-sm mt-2">
                      When researchers access your de-identified data, it will appear here.
                    </p>
                  </div>
                )}
              </div>

              {/* Quick Actions */}
              <div>
                <h2 className="text-lg font-medium text-white mb-6">Quick Actions</h2>
                <div className="grid md:grid-cols-3 gap-4">
                  <button
                    onClick={() => setActiveTab('consent')}
                    className="card-glass card-hover p-6 text-left group"
                  >
                    <span className="text-2xl mb-4 block">🔒</span>
                    <h3 className="text-white font-medium mb-2 group-hover:text-[#00d4aa] transition-colors">
                      Manage Consent
                    </h3>
                    <p className="text-white/40 text-sm">Review and update sharing preferences</p>
                  </button>
                  <button
                    onClick={() => setActiveTab('rewards')}
                    className="card-glass card-hover p-6 text-left group"
                  >
                    <span className="text-2xl mb-4 block">🎁</span>
                    <h3 className="text-white font-medium mb-2 group-hover:text-[#00d4aa] transition-colors">
                      View Rewards
                    </h3>
                    <p className="text-white/40 text-sm">See earned points and redeem</p>
                  </button>
                  <button
                    onClick={() => setActiveTab('data')}
                    className="card-glass card-hover p-6 text-left group"
                  >
                    <span className="text-2xl mb-4 block">📊</span>
                    <h3 className="text-white font-medium mb-2 group-hover:text-[#00d4aa] transition-colors">
                      View My Data
                    </h3>
                    <p className="text-white/40 text-sm">See what data you've contributed</p>
                  </button>
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

                {consents.length > 0 ? (
                  <div className="space-y-4 mb-8">
                    {consents.map((consent) => (
                      <div key={consent.id} className="card-glass p-4 flex items-center justify-between">
                        <div>
                          <span className="text-white/70">{consent.consent_type}</span>
                          <p className="text-white/30 text-xs mt-1">
                            {consent.signed_date ? `Signed ${new Date(consent.signed_date).toLocaleDateString()}` : 'Pending'}
                          </p>
                        </div>
                        <span className={`px-3 py-1 text-xs uppercase ${
                          consent.status === 'active' ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : 'bg-white/10 text-white/40'
                        }`}>
                          {consent.status}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="card-glass p-8 text-center mb-8">
                    <p className="text-white/40">No consents signed yet</p>
                    <p className="text-white/30 text-sm mt-2">
                      Sign a consent to start contributing to research.
                    </p>
                  </div>
                )}

                <button className="px-6 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors">
                  Sign New Consent
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
                View the de-identified data you've contributed to the platform.
              </p>

              <div className="card-glass p-8 text-center">
                <p className="text-white/40">No data contributed yet</p>
                <p className="text-white/30 text-sm mt-2">
                  Connect your medical records or manually add treatment history to start contributing.
                </p>
                <button className="mt-6 px-6 py-3 border border-white/20 text-white/60 text-xs uppercase tracking-wider hover:bg-white hover:text-black transition-all">
                  Connect Records
                </button>
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
                      {profile?.points_balance || 0}
                    </p>
                    <p className="text-white/40 text-sm">
                      ≈ ${((profile?.points_balance || 0) / 100).toFixed(2)} value
                    </p>
                  </div>
                  <button 
                    disabled={!profile?.points_balance}
                    className="w-full py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    Redeem Points
                  </button>
                </div>

                <div>
                  <h2 className="text-lg font-medium text-white mb-6">Earning History</h2>
                  {rewards?.history && rewards.history.length > 0 ? (
                    <div className="space-y-px">
                      {rewards.history.map((item, index) => (
                        <div key={index} className="card-glass p-4 flex items-center justify-between">
                          <div>
                            <p className="text-white/70 text-sm">{item.activity}</p>
                            <p className="text-white/30 text-xs">{item.date}</p>
                          </div>
                          <span className="text-[#00d4aa] font-mono">+{item.points}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="card-glass p-8 text-center">
                      <p className="text-white/40">No rewards history yet</p>
                      <p className="text-white/30 text-sm mt-2">
                        Earn points by signing consents, contributing data, and participating in studies.
                      </p>
                    </div>
                  )}
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
