import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const API_URL = process.env.NODE_ENV === 'production' ? '' : (process.env.REACT_APP_API_URL || 'http://localhost:8000');

// State machine states
const STATES = {
  LOADING: 'loading',
  READY: 'ready',
  ERROR: 'error',
};

const PatientPortal = () => {
  // Core state
  const [pageState, setPageState] = useState(STATES.LOADING);
  const [activeTab, setActiveTab] = useState('overview');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Data state
  const [profile, setProfile] = useState(null);
  const [consents, setConsents] = useState([]);
  const [consentTemplates, setConsentTemplates] = useState([]);
  const [rewards, setRewards] = useState(null);
  const [accessLog, setAccessLog] = useState([]);
  const [connections, setConnections] = useState([]);
  const [extractedData, setExtractedData] = useState([]);
  const [dataSummary, setDataSummary] = useState(null);

  // Modal state
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const token = localStorage.getItem('token');

  const fetchData = useCallback(async () => {
    if (!token) {
      navigate('/login');
      return;
    }

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.user_type !== 'patient') {
      navigate('/research');
      return;
    }

    try {
      const headers = { Authorization: `Bearer ${token}` };

      const [profileRes, consentsRes, templatesRes, rewardsRes, logRes, connectionsRes, dataRes, summaryRes] = await Promise.all([
        fetch(`${API_URL}/api/patient/profile`, { headers }),
        fetch(`${API_URL}/api/patient/consents`, { headers }),
        fetch(`${API_URL}/api/consent/templates`, { headers }),
        fetch(`${API_URL}/api/patient/rewards`, { headers }),
        fetch(`${API_URL}/api/patient/data-access-log`, { headers }),
        fetch(`${API_URL}/api/patient/connections`, { headers }),
        fetch(`${API_URL}/api/patient/extracted-data`, { headers }),
        fetch(`${API_URL}/api/patient/data-summary`, { headers }),
      ]);

      if (profileRes.ok) setProfile(await profileRes.json());
      if (consentsRes.ok) setConsents(await consentsRes.json());
      if (templatesRes.ok) setConsentTemplates(await templatesRes.json());
      if (rewardsRes.ok) setRewards(await rewardsRes.json());
      if (logRes.ok) setAccessLog(await logRes.json());
      if (connectionsRes.ok) setConnections(await connectionsRes.json());
      if (dataRes.ok) setExtractedData(await dataRes.json());
      if (summaryRes.ok) setDataSummary(await summaryRes.json());

      setPageState(STATES.READY);
    } catch (err) {
      console.error('Failed to fetch patient data:', err);
      setError('Failed to load your data. Please try again.');
      setPageState(STATES.ERROR);
    }
  }, [token, navigate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSignConsent = async (templateId, signature) => {
    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_URL}/api/consent/sign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          template_id: templateId,
          signature: signature,
          consent_options: { all_categories: true },
        }),
      });

      const data = await response.json();
      if (response.ok) {
        setShowConsentModal(false);
        setSelectedTemplate(null);
        await fetchData(); // Refresh all data
        alert(data.message);
      } else {
        alert(data.detail || 'Failed to sign consent');
      }
    } catch (err) {
      alert('Error signing consent. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRevokeConsent = async (consentId) => {
    if (!window.confirm('Are you sure you want to revoke this consent? Your data will no longer be shared.')) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/consent/${consentId}/revoke`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        await fetchData();
        alert('Consent revoked successfully.');
      }
    } catch (err) {
      alert('Error revoking consent.');
    }
  };

  const handleConnectRecords = async (sourceType, sourceName) => {
    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_URL}/api/patient/connections`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          source_type: sourceType,
          source_name: sourceName,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        setShowConnectionModal(false);
        alert(data.message);
        // Poll for completion
        setTimeout(() => fetchData(), 3000);
      } else {
        alert(data.detail || 'Failed to connect records');
      }
    } catch (err) {
      alert('Error connecting records. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'consent', label: 'Consent' },
    { id: 'data', label: 'My Data' },
    { id: 'rewards', label: 'Rewards' },
  ];

  const hasActiveResearchConsent = consents.some(c => c.consent_type === 'research_data_sharing' && c.status === 'active');

  if (pageState === STATES.LOADING) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center pt-20">
        <div className="text-center">
          <div className="w-8 h-8 border border-white/20 border-t-white/60 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white/40 text-sm">Loading your data...</p>
        </div>
      </div>
    );
  }

  if (pageState === STATES.ERROR) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center pt-20">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <button onClick={() => { setPageState(STATES.LOADING); fetchData(); }} className="px-4 py-2 bg-white text-black text-sm">
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
              <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">Patient Portal</p>
              <h1 className="heading-display text-4xl md:text-5xl text-white/90">Your Dashboard</h1>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <p className="text-white/40 text-xs mb-1">Consent Status</p>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${hasActiveResearchConsent ? 'bg-[#00d4aa]' : 'bg-amber-500'}`}></span>
                  <span className={`uppercase text-sm tracking-wider ${hasActiveResearchConsent ? 'text-[#00d4aa]' : 'text-amber-500'}`}>
                    {hasActiveResearchConsent ? 'Active' : 'Action Required'}
                  </span>
                </div>
              </div>
              <div className="h-8 w-px bg-white/10"></div>
              <div className="text-right">
                <p className="text-white/40 text-xs mb-1">Rewards</p>
                <p className="text-white font-mono text-lg">{profile?.points_balance || 0} pts</p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Alert for no consent */}
      {!hasActiveResearchConsent && (
        <section className="px-6 py-4 bg-amber-500/10 border-b border-amber-500/20">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-amber-500">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </span>
              <p className="text-amber-400 text-sm">
                <strong>Action Required:</strong> Sign a research consent to start contributing to cancer research and earn rewards.
              </p>
            </div>
            <button
              onClick={() => setActiveTab('consent')}
              className="px-4 py-2 bg-amber-500 text-black text-xs uppercase tracking-wider font-medium hover:bg-amber-400 transition-colors"
            >
              Sign Now
            </button>
          </div>
        </section>
      )}

      {/* Tabs */}
      <section className="border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-4 text-xs uppercase tracking-wider transition-colors ${
                  activeTab === tab.id ? 'text-white border-b-2 border-white' : 'text-white/40 hover:text-white/60'
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
            {/* OVERVIEW TAB */}
            {activeTab === 'overview' && (
              <motion.div key="overview" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/5 mb-12">
                  <div className="card-glass p-6">
                    <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Points Balance</p>
                    <p className="text-2xl font-light text-white font-mono">{profile?.points_balance || 0}</p>
                  </div>
                  <div className="card-glass p-6">
                    <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Active Consents</p>
                    <p className="text-2xl font-light text-white font-mono">{consents.filter(c => c.status === 'active').length}</p>
                  </div>
                  <div className="card-glass p-6">
                    <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Data Records</p>
                    <p className="text-2xl font-light text-white font-mono">{dataSummary?.total_records || 0}</p>
                  </div>
                  <div className="card-glass p-6">
                    <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Completeness</p>
                    <p className="text-2xl font-light text-white font-mono">{Math.round(dataSummary?.completeness_score || 0)}%</p>
                  </div>
                </div>

                {/* Progress Steps */}
                <div className="mb-12">
                  <h2 className="text-lg font-medium text-white mb-6">Getting Started</h2>
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className={`card-glass p-6 ${hasActiveResearchConsent ? 'border-l-2 border-[#00d4aa]' : 'border-l-2 border-amber-500'}`}>
                      <div className="flex items-center gap-3 mb-4">
                        <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${hasActiveResearchConsent ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : 'bg-amber-500/20 text-amber-500'}`}>
                          {hasActiveResearchConsent ? (
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          ) : '1'}
                        </span>
                        <span className="text-white font-medium">Sign Consent</span>
                      </div>
                      <p className="text-white/40 text-sm mb-4">
                        {hasActiveResearchConsent 
                          ? 'You have signed the research data sharing consent.'
                          : 'Sign a consent to allow your de-identified data to be used for research.'}
                      </p>
                      {!hasActiveResearchConsent && (
                        <button onClick={() => setActiveTab('consent')} className="text-[#00d4aa] text-sm hover:underline">
                          Sign consent →
                        </button>
                      )}
                    </div>

                    <div className={`card-glass p-6 ${connections.length > 0 ? 'border-l-2 border-[#00d4aa]' : 'border-l-2 border-white/20'}`}>
                      <div className="flex items-center gap-3 mb-4">
                        <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${connections.length > 0 ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : 'bg-white/10 text-white/40'}`}>
                          {connections.length > 0 ? (
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          ) : '2'}
                        </span>
                        <span className="text-white font-medium">Connect Records</span>
                      </div>
                      <p className="text-white/40 text-sm mb-4">
                        {connections.length > 0
                          ? `Connected to ${connections.length} source(s).`
                          : 'Connect your medical records to contribute data.'}
                      </p>
                      {hasActiveResearchConsent && connections.length === 0 && (
                        <button onClick={() => setActiveTab('data')} className="text-[#00d4aa] text-sm hover:underline">
                          Connect records →
                        </button>
                      )}
                    </div>

                    <div className={`card-glass p-6 ${extractedData.length > 0 ? 'border-l-2 border-[#00d4aa]' : 'border-l-2 border-white/20'}`}>
                      <div className="flex items-center gap-3 mb-4">
                        <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${extractedData.length > 0 ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : 'bg-white/10 text-white/40'}`}>
                          {extractedData.length > 0 ? (
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          ) : '3'}
                        </span>
                        <span className="text-white font-medium">Earn Rewards</span>
                      </div>
                      <p className="text-white/40 text-sm mb-4">
                        {extractedData.length > 0
                          ? `Contributing ${extractedData.length} data record(s) to research.`
                          : 'Earn points for each data contribution.'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Recent Activity */}
                <div>
                  <h2 className="text-lg font-medium text-white mb-6">Recent Activity</h2>
                  {accessLog.length > 0 ? (
                    <div className="space-y-px">
                      {accessLog.slice(0, 5).map((log, index) => (
                        <div key={index} className="card-glass p-4 flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                            <span className="text-white/70 text-sm">{log.institution} accessed {log.data_type} for {log.purpose}</span>
                          </div>
                          <span className="text-white/30 text-xs">{log.date}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="card-glass p-8 text-center">
                      <p className="text-white/40">No data access activity yet</p>
                      <p className="text-white/30 text-sm mt-2">When researchers access your de-identified data, it will appear here.</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* CONSENT TAB */}
            {activeTab === 'consent' && (
              <motion.div key="consent" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="max-w-4xl">
                  <h2 className="text-lg font-medium text-white mb-2">Consent Management</h2>
                  <p className="text-white/40 mb-8">Control how your de-identified data is shared with researchers.</p>

                  {/* Active Consents */}
                  {consents.filter(c => c.status === 'active').length > 0 && (
                    <div className="mb-12">
                      <h3 className="text-sm uppercase tracking-wider text-white/40 mb-4">Active Consents</h3>
                      <div className="space-y-3">
                        {consents.filter(c => c.status === 'active').map((consent) => (
                          <div key={consent.id} className="card-glass p-6 border-l-2 border-[#00d4aa]">
                            <div className="flex items-start justify-between">
                              <div>
                                <h4 className="text-white font-medium mb-1">{consent.consent_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                                <p className="text-white/40 text-sm">Signed {new Date(consent.signed_date).toLocaleDateString()}</p>
                                {consent.expires_at && (
                                  <p className="text-white/30 text-xs mt-1">Expires {new Date(consent.expires_at).toLocaleDateString()}</p>
                                )}
                              </div>
                              <button
                                onClick={() => handleRevokeConsent(consent.id)}
                                className="px-3 py-1 border border-red-500/30 text-red-400 text-xs uppercase tracking-wider hover:bg-red-500/10 transition-colors"
                              >
                                Revoke
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Available Consents */}
                  <div>
                    <h3 className="text-sm uppercase tracking-wider text-white/40 mb-4">Available Consents</h3>
                    <div className="space-y-3">
                      {consentTemplates.map((template) => {
                        const isSigned = consents.some(c => c.consent_type === template.consent_type && c.status === 'active');
                        return (
                          <div key={template.id} className={`card-glass p-6 ${isSigned ? 'opacity-50' : 'card-hover cursor-pointer'}`}>
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                  <h4 className="text-white font-medium">{template.name}</h4>
                                  {isSigned && <span className="px-2 py-0.5 text-xs bg-[#00d4aa]/20 text-[#00d4aa]">SIGNED</span>}
                                </div>
                                <p className="text-white/40 text-sm mb-3">{template.description}</p>
                                <div className="flex flex-wrap gap-2">
                                  {template.data_categories.map((cat) => (
                                    <span key={cat} className="px-2 py-1 text-xs bg-white/5 text-white/40">{cat}</span>
                                  ))}
                                </div>
                                {template.duration_months && (
                                  <p className="text-white/30 text-xs mt-3">Valid for {template.duration_months} months</p>
                                )}
                              </div>
                              {!isSigned && (
                                <button
                                  onClick={() => { setSelectedTemplate(template); setShowConsentModal(true); }}
                                  className="ml-4 px-4 py-2 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors"
                                >
                                  Review & Sign
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Revoked/Expired */}
                  {consents.filter(c => c.status !== 'active').length > 0 && (
                    <div className="mt-12">
                      <h3 className="text-sm uppercase tracking-wider text-white/40 mb-4">Past Consents</h3>
                      <div className="space-y-2">
                        {consents.filter(c => c.status !== 'active').map((consent) => (
                          <div key={consent.id} className="card-glass p-4 opacity-50">
                            <div className="flex items-center justify-between">
                              <span className="text-white/60">{consent.consent_type.replace(/_/g, ' ')}</span>
                              <span className="px-2 py-0.5 text-xs bg-white/10 text-white/40">{consent.status.toUpperCase()}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* DATA TAB */}
            {activeTab === 'data' && (
              <motion.div key="data" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="max-w-4xl">
                  <h2 className="text-lg font-medium text-white mb-2">Your Contributed Data</h2>
                  <p className="text-white/40 mb-8">View and manage the de-identified data you've contributed to the platform.</p>

                  {/* Requirement check */}
                  {!hasActiveResearchConsent ? (
                    <div className="card-glass p-8 text-center border border-amber-500/20">
                      <div className="mx-auto w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center mb-4">
                        <svg className="w-6 h-6 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <h3 className="text-white font-medium mb-2">Consent Required</h3>
                      <p className="text-white/40 mb-6">You must sign the Research Data Sharing consent before connecting your medical records.</p>
                      <button
                        onClick={() => setActiveTab('consent')}
                        className="px-6 py-3 bg-amber-500 text-black text-xs uppercase tracking-wider font-medium"
                      >
                        Sign Consent First
                      </button>
                    </div>
                  ) : (
                    <>
                      {/* Connected Sources */}
                      <div className="mb-8">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-sm uppercase tracking-wider text-white/40">Connected Sources</h3>
                          <button
                            onClick={() => setShowConnectionModal(true)}
                            className="px-4 py-2 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors"
                          >
                            + Connect Records
                          </button>
                        </div>
                        
                        {connections.length > 0 ? (
                          <div className="space-y-3">
                            {connections.map((conn) => (
                              <div key={conn.id} className="card-glass p-4 flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                  <div className={`w-3 h-3 rounded-full ${conn.connection_status === 'connected' ? 'bg-[#00d4aa]' : conn.connection_status === 'pending' ? 'bg-amber-500 animate-pulse' : 'bg-red-500'}`}></div>
                                  <div>
                                    <p className="text-white font-medium">{conn.source_name}</p>
                                    <p className="text-white/40 text-sm">{conn.source_type.replace(/_/g, ' ')} • {conn.records_synced} records</p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-4">
                                  {conn.last_sync && (
                                    <span className="text-white/30 text-xs">Last sync: {new Date(conn.last_sync).toLocaleDateString()}</span>
                                  )}
                                  <span className={`px-2 py-1 text-xs uppercase ${conn.connection_status === 'connected' ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : conn.connection_status === 'pending' ? 'bg-amber-500/20 text-amber-500' : 'bg-red-500/20 text-red-400'}`}>
                                    {conn.connection_status}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="card-glass p-8 text-center">
                            <div className="mx-auto w-12 h-12 rounded-full bg-white/10 flex items-center justify-center mb-4">
                              <svg className="w-6 h-6 text-white/40" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9 2a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2V6.414A2 2 0 0016.414 5L14 2.586A2 2 0 0012.586 2H9z" />
                                <path d="M3 8a2 2 0 012-2v10h8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
                              </svg>
                            </div>
                            <h3 className="text-white font-medium mb-2">No Records Connected</h3>
                            <p className="text-white/40 mb-6">Connect your medical records to start contributing to cancer research.</p>
                            <button
                              onClick={() => setShowConnectionModal(true)}
                              className="px-6 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium"
                            >
                              Connect Records
                            </button>
                          </div>
                        )}
                      </div>

                      {/* Extracted Data Summary */}
                      {extractedData.length > 0 && (
                        <div>
                          <h3 className="text-sm uppercase tracking-wider text-white/40 mb-4">De-identified Data Summary</h3>
                          <div className="space-y-3">
                            {extractedData.map((data) => (
                              <div key={data.id} className="card-glass p-4">
                                <div className="flex items-start justify-between">
                                  <div>
                                    <div className="flex items-center gap-2 mb-2">
                                      <span className="text-white font-medium">{data.data_category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                                      {data.data_type && <span className="text-white/40 text-sm">• {data.data_type}</span>}
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                      {Object.entries(data.summary || {}).slice(0, 4).map(([key, value]) => (
                                        <span key={key} className="px-2 py-1 text-xs bg-white/5 text-white/60">
                                          {key.replace(/_/g, ' ')}: {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <span className="text-[#00d4aa] text-sm font-mono">{Math.round(data.data_quality_score || 0)}%</span>
                                    <p className="text-white/30 text-xs">quality</p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </motion.div>
            )}

            {/* REWARDS TAB */}
            {activeTab === 'rewards' && (
              <motion.div key="rewards" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="grid md:grid-cols-2 gap-8">
                  <div>
                    <h2 className="text-lg font-medium text-white mb-6">Your Rewards</h2>
                    <div className="card-glass p-8 mb-8">
                      <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Available Balance</p>
                      <p className="text-5xl font-light text-white font-mono mb-2">{profile?.points_balance || 0}</p>
                      <p className="text-white/40 text-sm mb-4">≈ ${((profile?.points_balance || 0) / 100).toFixed(2)} value</p>
                      <div className="pt-4 border-t border-white/10 grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-white/30">Total Earned</p>
                          <p className="text-white font-mono">{rewards?.total_earned || 0} pts</p>
                        </div>
                        <div>
                          <p className="text-white/30">Redeemed</p>
                          <p className="text-white font-mono">{rewards?.total_redeemed || 0} pts</p>
                        </div>
                      </div>
                    </div>
                    <button
                      disabled={!profile?.points_balance || profile.points_balance < 500}
                      className="w-full py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      Redeem Points (min 500)
                    </button>
                  </div>

                  <div>
                    <h2 className="text-lg font-medium text-white mb-6">How to Earn</h2>
                    <div className="space-y-3 mb-8">
                      {[
                        {
                          action: 'Sign a consent',
                          points: 50,
                          icon: (
                            <svg className="w-5 h-5 text-white/60" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V8z" clipRule="evenodd" />
                            </svg>
                          )
                        },
                        {
                          action: 'Connect medical records',
                          points: 100,
                          icon: (
                            <svg className="w-5 h-5 text-white/60" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                            </svg>
                          )
                        },
                        {
                          action: 'Complete your profile',
                          points: 25,
                          icon: (
                            <svg className="w-5 h-5 text-white/60" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                            </svg>
                          )
                        },
                        {
                          action: 'Data used in research',
                          points: 10,
                          icon: (
                            <svg className="w-5 h-5 text-white/60" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M7 2a1 1 0 00-.707 1.707L7 4.414v3.758a1 1 0 01-.293.707l-4 4C.817 14.769 2.156 18 4.828 18h10.343c2.673 0 4.012-3.231 2.122-5.121l-4-4A1 1 0 0113 8.172V4.414l.707-.707A1 1 0 0013 2H7zm2 6.172V4h2v4.172a3 3 0 00.879 2.12l1.027 1.028a4 4 0 00-2.171.102l-.47.156a4 4 0 01-2.53 0l-.563-.187a1.993 1.993 0 00-.114-.035l1.063-1.063A3 3 0 009 8.172z" clipRule="evenodd" />
                            </svg>
                          ),
                          note: 'per access'
                        },
                      ].map((item) => (
                        <div key={item.action} className="card-glass p-4 flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center flex-shrink-0">
                              {item.icon}
                            </div>
                            <div>
                              <p className="text-white/80 text-sm">{item.action}</p>
                              {item.note && <p className="text-white/30 text-xs">{item.note}</p>}
                            </div>
                          </div>
                          <span className="text-[#00d4aa] font-mono">+{item.points}</span>
                        </div>
                      ))}
                    </div>

                    <h2 className="text-lg font-medium text-white mb-4">Recent Activity</h2>
                    {rewards?.history && rewards.history.length > 0 ? (
                      <div className="space-y-2">
                        {rewards.history.slice(0, 5).map((item, index) => (
                          <div key={index} className="card-glass p-3 flex items-center justify-between">
                            <div>
                              <p className="text-white/70 text-sm">{item.activity}</p>
                              <p className="text-white/30 text-xs">{item.date}</p>
                            </div>
                            <span className="text-[#00d4aa] font-mono text-sm">+{item.points}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="card-glass p-6 text-center">
                        <p className="text-white/40 text-sm">No rewards activity yet</p>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      {/* Consent Modal */}
      <AnimatePresence>
        {showConsentModal && selectedTemplate && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowConsentModal(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-black border border-white/10 max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-white/10 flex items-center justify-between">
                <h2 className="text-xl text-white">{selectedTemplate.name}</h2>
                <button onClick={() => setShowConsentModal(false)} className="p-2 hover:bg-white/10">
                  <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                <div className="prose prose-invert prose-sm max-w-none">
                  <div className="whitespace-pre-wrap text-white/70 text-sm leading-relaxed">
                    {selectedTemplate.content}
                  </div>
                </div>
              </div>
              <div className="p-6 border-t border-white/10">
                <p className="text-white/40 text-sm mb-4">
                  By clicking "I Agree", you confirm that you have read and understood this consent.
                </p>
                <div className="flex gap-4">
                  <button
                    onClick={() => setShowConsentModal(false)}
                    className="flex-1 py-3 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white/10 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleSignConsent(selectedTemplate.id, `digital_signature_${Date.now()}`)}
                    disabled={isSubmitting}
                    className="flex-1 py-3 bg-[#00d4aa] text-black text-xs uppercase tracking-wider font-medium hover:bg-[#00d4aa]/90 transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? 'Signing...' : 'I Agree & Sign'}
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Connection Modal */}
      <AnimatePresence>
        {showConnectionModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowConnectionModal(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-black border border-white/10 max-w-lg w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-white/10 flex items-center justify-between">
                <h2 className="text-xl text-white">Connect Medical Records</h2>
                <button onClick={() => setShowConnectionModal(false)} className="p-2 hover:bg-white/10">
                  <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6 space-y-4">
                <p className="text-white/40 text-sm mb-6">Choose how you'd like to connect your medical records:</p>
                
                {[
                  {
                    type: 'epic_mychart',
                    name: 'Epic MyChart',
                    icon: (
                      <svg className="w-6 h-6 text-white/60" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 0l-2 2a1 1 0 101.414 1.414L8 10.414l1.293 1.293a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    ),
                    desc: 'Connect via MyChart patient portal'
                  },
                  {
                    type: 'cerner_patient_portal',
                    name: 'Cerner',
                    icon: (
                      <svg className="w-6 h-6 text-white/60" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V4a2 2 0 00-2-2H6zm1 2a1 1 0 000 2h6a1 1 0 100-2H7zm6 7a1 1 0 011 1v3a1 1 0 11-2 0v-3a1 1 0 011-1zm-3 3a1 1 0 100 2h.01a1 1 0 100-2H10zm-4 1a1 1 0 011-1h.01a1 1 0 110 2H7a1 1 0 01-1-1zm1-4a1 1 0 100 2h.01a1 1 0 100-2H7zm2 1a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1zm4-4a1 1 0 100 2h.01a1 1 0 100-2H13zM9 9a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1zM7 8a1 1 0 000 2h.01a1 1 0 000-2H7z" clipRule="evenodd" />
                      </svg>
                    ),
                    desc: 'Connect via Cerner patient portal'
                  },
                  {
                    type: 'manual_upload',
                    name: 'Manual Upload',
                    icon: (
                      <svg className="w-6 h-6 text-white/60" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8 4a3 3 0 00-3 3v4a5 5 0 0010 0V7a1 1 0 112 0v4a7 7 0 11-14 0V7a5 5 0 0110 0v4a3 3 0 11-6 0V7a1 1 0 012 0v4a1 1 0 102 0V7a3 3 0 00-3-3z" clipRule="evenodd" />
                      </svg>
                    ),
                    desc: 'Upload medical records manually'
                  },
                ].map((source) => (
                  <button
                    key={source.type}
                    onClick={() => handleConnectRecords(source.type, source.name)}
                    disabled={isSubmitting}
                    className="w-full card-glass card-hover p-4 text-left flex items-center gap-4 disabled:opacity-50"
                  >
                    <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center flex-shrink-0">
                      {source.icon}
                    </div>
                    <div>
                      <p className="text-white font-medium">{source.name}</p>
                      <p className="text-white/40 text-sm">{source.desc}</p>
                    </div>
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default PatientPortal;
