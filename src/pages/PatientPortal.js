import toast from 'react-hot-toast';
import { API_URL, apiFetch as fetch, readSessionUser } from '../lib/api';
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const SYNTHETIC_FHIR_UPLOADS_ENABLED = process.env.REACT_APP_ENABLE_SYNTHETIC_FHIR_UPLOADS === 'true';
const PATIENT_STUDY_ENROLLMENT_ENABLED = process.env.REACT_APP_ENABLE_PATIENT_STUDY_ENROLLMENT === 'true';

// State machine states
const STATES = {
  LOADING: 'loading',
  READY: 'ready',
  ERROR: 'error',
};

// Renders the consent text's small markdown subset as real elements.
//
// It was previously printed verbatim, so the most important thing a patient
// reads arrived with "#" and "##" and "-" still in it, looking like something
// nobody had finished. Deliberately structural rather than HTML injection:
// this text should never be able to carry markup, even from our own seed.
const ConsentText = ({ content }) => {
  const blocks = [];
  let bullets = [];
  let paragraph = [];

  const flushBullets = () => {
    if (!bullets.length) return;
    blocks.push(
      <ul key={`ul-${blocks.length}`} className="list-disc pl-5 space-y-1 mb-4 text-white/70 text-sm">
        {bullets.map((item, i) => <li key={i}>{item}</li>)}
      </ul>
    );
    bullets = [];
  };
  // The source is hard-wrapped, so consecutive lines are one sentence and
  // have to be joined. Emitting a paragraph per line broke sentences across
  // visual gaps and made the text look like it had been badly pasted.
  const flushParagraph = () => {
    if (!paragraph.length) return;
    blocks.push(
      <p key={blocks.length} className="text-white/70 text-sm leading-relaxed mb-4">
        {paragraph.join(' ')}
      </p>
    );
    paragraph = [];
  };
  const flushAll = () => { flushParagraph(); flushBullets(); };

  String(content || '').split('\n').forEach((raw) => {
    const line = raw.trim();
    if (!line) { flushAll(); return; }
    if (line.startsWith('## ')) {
      flushAll();
      blocks.push(<h4 key={blocks.length} className="text-white font-medium mt-5 mb-2">{line.slice(3)}</h4>);
    } else if (line.startsWith('# ')) {
      flushAll();
      blocks.push(<h3 key={blocks.length} className="text-white text-base font-medium mb-3">{line.slice(2)}</h3>);
    } else if (line.startsWith('- ')) {
      flushParagraph();
      bullets.push(line.slice(2));
    } else {
      flushBullets();
      paragraph.push(line);
    }
  });
  flushAll();
  return <>{blocks}</>;
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
  const [accessLog, setAccessLog] = useState([]);
  const [dataReleases, setDataReleases] = useState([]);
  const [studyResults, setStudyResults] = useState([]);
  const [contribution, setContribution] = useState(null);
  const [reconsent, setReconsent] = useState([]);
  const [connections, setConnections] = useState([]);
  const [extractedData, setExtractedData] = useState([]);
  const [dataSummary, setDataSummary] = useState(null);
  const [availableStudies, setAvailableStudies] = useState([]);
  const [myStudies, setMyStudies] = useState([]);
  const [studyActionId, setStudyActionId] = useState(null);

  // Modal state
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const token = sessionStorage.getItem('token');

  const fetchData = useCallback(async () => {
    if (!token) {
      navigate('/login');
      return;
    }

    const user = (readSessionUser() || {});
    if (user.user_type !== 'patient') {
      navigate('/research');
      return;
    }

    const headers = { Authorization: `Bearer ${token}` };
    // Each panel is fetched independently and allowed to fail on its own.
    //
    // These used to run under Promise.all, and apiFetch throws on any
    // non-2xx, so a single gated or briefly unavailable endpoint rejected the
    // batch and the whole portal rendered as an error page. Someone who had
    // simply not signed one optional consent lost their consents, their
    // records, their releases and their contribution record along with it —
    // a portal made of independent panels should not die because one of them
    // is unavailable.
    const settled = await Promise.allSettled([
      fetch(`${API_URL}/api/patient/profile`, { headers }),
      fetch(`${API_URL}/api/patient/consents`, { headers }),
      fetch(`${API_URL}/api/consent/templates`, { headers }),
      fetch(`${API_URL}/api/patient/data-access-log`, { headers }),
      fetch(`${API_URL}/api/patient/connections`, { headers }),
      fetch(`${API_URL}/api/patient/extracted-data`, { headers }),
      fetch(`${API_URL}/api/patient/data-summary`, { headers }),
      fetch(`${API_URL}/api/studies/available`, { headers }),
      fetch(`${API_URL}/api/patient/studies`, { headers }),
      fetch(`${API_URL}/api/patient/data-releases`, { headers }),
      fetch(`${API_URL}/api/patient/study-results`, { headers }),
      fetch(`${API_URL}/api/patient/contribution`, { headers }),
      fetch(`${API_URL}/api/patient/reconsent`, { headers }),
    ]);

    const panel = async (index) => {
      const result = settled[index];
      if (result.status !== 'fulfilled') return null;
      try { return await result.value.json(); } catch { return null; }
    };

    const [profileData, consentsData, templatesData, logData, connectionsData,
           dataData, summaryData, availableData, myStudiesData, releasesData,
           resultsData, contributionData, reconsentData] = await Promise.all(
      settled.map((_, index) => panel(index)));

    // The profile is the one exception. Without it there is no person whose
    // portal this is, and rendering empty panels would be a lie.
    if (!profileData) {
      const reason = settled[0].status === 'rejected'
        ? settled[0].reason?.message : null;
      setError(reason || 'Your profile could not be loaded.');
      setPageState(STATES.ERROR);
      return;
    }

    setProfile(profileData);
    setConsents(consentsData || []);
    setConsentTemplates(templatesData || []);
    setAccessLog(logData || []);
    setConnections(connectionsData || []);
    setExtractedData(dataData || []);
    setDataSummary(summaryData);
    setAvailableStudies(availableData || []);
    setMyStudies(myStudiesData || []);
    setDataReleases(releasesData || []);
    setStudyResults(resultsData || []);
    setContribution(contributionData);
    setReconsent(reconsentData || []);
    setPageState(STATES.READY);
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
        toast(data.message);
      } else {
        toast(data.detail || 'Failed to sign consent');
      }
    } catch (err) {
      toast('Error signing consent. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Answering is the only thing that changes anything here. Leaving the
  // question open is already the safe state — the person's records are out
  // of the pool while it stands.
  const handleReconsent = async (studyId, decision) => {
    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_URL}/api/patient/reconsent/${studyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ decision }),
      });
      const data = await response.json().catch(() => ({}));
      if (response.ok) {
        await fetchData();
        toast(data.message);
      } else {
        toast(data.detail || 'Could not record your answer.');
      }
    } catch (err) {
      toast('Error recording your answer. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRevokeConsent = async (consentId) => {
    // "Your data will no longer be shared" was not true, and this is the
    // moment a person is most entitled to the truth. Revoking stops every
    // future extract; it cannot reach a file a researcher already downloaded.
    if (!window.confirm(
      'Revoke this consent?\n\n'
      + 'No new extract will include your data.\n\n'
      + 'Any extract already downloaded by a study team is held outside this '
      + 'system and cannot be recalled automatically. If there is one, it will '
      + 'be flagged for follow-up and you will see it under "What your data did".'
    )) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/consent/${consentId}/revoke`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await response.json().catch(() => ({}));
      if (response.ok) {
        await fetchData();
        // Say what actually happened, including the part we cannot undo.
        toast(data.outstanding_obligation
          ? `Consent revoked. ${data.prior_releases_downloaded} extract(s) containing your data were already downloaded; the receiving researchers have been notified to destroy their copies.`
          : 'Consent revoked. No extract containing your data has been downloaded.');
      } else {
        toast(data.detail || 'Could not revoke this consent.');
      }
    } catch (err) {
      toast('Error revoking consent.');
    }
  };

  const handleFHIRUpload = async (event) => {
    if (!SYNTHETIC_FHIR_UPLOADS_ENABLED) {
      toast('FHIR uploads are disabled in this deployment. Do not submit real health information.');
      return;
    }

    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;

    let bundle;
    try {
      bundle = JSON.parse(await file.text());
    } catch (err) {
      toast('That file is not valid JSON.');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_URL}/api/patient/connections/fhir`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ bundle, source_name: file.name }),
      });
      const data = await response.json();
      if (response.ok) {
        setShowConnectionModal(false);
        toast(data.message);
        await fetchData();
      } else {
        toast(data.detail || 'Failed to upload FHIR records');
      }
    } catch (err) {
      toast('Error uploading FHIR records. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleJoinStudy = async (studyId) => {
    setStudyActionId(studyId);
    try {
      const response = await fetch(`${API_URL}/api/studies/${studyId}/join`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (response.ok) {
        await fetchData();
      } else {
        toast(data.detail || 'Failed to join study');
      }
    } catch (err) {
      toast('Error joining study. Please try again.');
    } finally {
      setStudyActionId(null);
    }
  };

  const handleLeaveStudy = async (studyId) => {
    if (!window.confirm('Are you sure you want to leave this study?')) return;
    setStudyActionId(studyId);
    try {
      const response = await fetch(`${API_URL}/api/studies/${studyId}/leave`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        await fetchData();
      } else {
        const data = await response.json();
        toast(data.detail || 'Failed to leave study');
      }
    } catch (err) {
      toast('Error leaving study. Please try again.');
    } finally {
      setStudyActionId(null);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'consent', label: 'Acknowledgement' },
    { id: 'studies', label: 'Study concept' },
    { id: 'data', label: 'Test Data' },
    { id: 'contribution', label: 'What your data did' },
  ];

  const hasActiveResearchConsent = consents.some(c => c.consent_type === 'research_data_sharing' && c.status === 'active');
  const hasActiveTrialMatchingConsent = consents.some(c => c.consent_type === 'clinical_trial_matching' && c.status === 'active');

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
              <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">Patient Workflow Pilot</p>
              <h1 className="heading-display text-4xl md:text-5xl text-white/90">Your Dashboard</h1>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <p className="text-white/40 text-xs mb-1">Test Acknowledgement</p>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${hasActiveResearchConsent ? 'bg-[#00d4aa]' : 'bg-amber-500'}`}></span>
                  <span className={`uppercase text-sm tracking-wider ${hasActiveResearchConsent ? 'text-[#00d4aa]' : 'text-amber-500'}`}>
                    {hasActiveResearchConsent ? 'Recorded' : 'Optional Review'}
                  </span>
                </div>
              </div>
              <div className="h-8 w-px bg-white/10"></div>
              <div className="text-right max-w-xs">
                <p className="text-white/40 text-xs mb-1">Your contribution</p>
                <p className="text-white/75 text-sm leading-snug">
                  {contribution?.summary || 'Loading your contribution record…'}
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* A study has moved away from what someone agreed to. Placed above
          everything because their records are already out of the pool, and
          a question you have to go looking for is not really being asked. */}
      {reconsent.length > 0 && (
        <section className="px-6 py-6 bg-amber-500/10 border-b border-amber-500/20" data-testid="reconsent-prompt">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-amber-300 text-sm uppercase tracking-wider mb-4">
              {reconsent.length === 1 ? 'A study you joined has changed' : `${reconsent.length} studies you joined have changed`}
            </h2>
            <div className="space-y-5">
              {reconsent.map((item) => (
                <div key={item.study_id} className="border border-amber-400/20 p-5">
                  <h3 className="text-white font-medium mb-3">{item.study_name}</h3>
                  <ul className="space-y-1 mb-4">
                    {item.changes.map((line, i) => (
                      <li key={i} className="text-white/70 text-sm">{line}</li>
                    ))}
                  </ul>
                  {item.current_purpose && (
                    <p className="text-white/50 text-sm mb-2">
                      <span className="text-white/35">The study now says: </span>{item.current_purpose}
                    </p>
                  )}
                  {item.current_eligibility && (
                    <p className="text-white/50 text-sm mb-4">
                      <span className="text-white/35">Who it is for: </span>{item.current_eligibility}
                    </p>
                  )}
                  <p className="text-white/40 text-xs mb-4 leading-relaxed">{item.note}</p>
                  <div className="flex flex-wrap gap-3">
                    <button
                      onClick={() => handleReconsent(item.study_id, 'continue')}
                      disabled={isSubmitting}
                      className="px-5 py-2.5 border border-white/25 text-white text-xs uppercase tracking-wider hover:bg-white/5 transition-colors disabled:opacity-50"
                    >
                      Stay in this study
                    </button>
                    <button
                      onClick={() => handleReconsent(item.study_id, 'withdraw')}
                      disabled={isSubmitting}
                      className="px-5 py-2.5 border border-white/25 text-white text-xs uppercase tracking-wider hover:bg-white/5 transition-colors disabled:opacity-50"
                    >
                      Leave this study
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Alert for no consent */}
      {!hasActiveResearchConsent && (
        <section className="px-6 py-4 bg-amber-500/10 border-b border-amber-500/20">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-amber-500">⚠️</span>
              <p className="text-amber-400 text-sm">
                <strong>Pilot step:</strong> Review the consent workflow using synthetic test information only.
              </p>
            </div>
            <button
              onClick={() => setActiveTab('consent')}
              className="px-4 py-2 bg-amber-500 text-black text-xs uppercase tracking-wider font-medium hover:bg-amber-400 transition-colors"
            >
              Review
            </button>
          </div>
        </section>
      )}

      {/* Tabs */}
      <section className="border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex gap-1 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 sm:px-6 py-4 text-xs uppercase tracking-wider transition-colors whitespace-nowrap ${
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
                    <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Records Contributed</p>
                    <p className="text-2xl font-light text-white font-mono">
                      {contribution?.stages?.find(st => st.key === 'contributed')?.items?.length !== undefined
                        ? (extractedData.length || 0)
                        : 0}
                    </p>
                  </div>
                  <div className="card-glass p-6">
                    <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Test Acknowledgements</p>
                    <p className="text-2xl font-light text-white font-mono">{consents.filter(c => c.status === 'active').length}</p>
                  </div>
                  <div className="card-glass p-6">
                    <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Synthetic Records</p>
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
                        <span className={`w-8 h-8 rounded-full flex items-center justify-center ${hasActiveResearchConsent ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : 'bg-amber-500/20 text-amber-500'}`}>
                          {hasActiveResearchConsent ? '✓' : '1'}
                        </span>
                        <span className="text-white font-medium">Review Acknowledgement</span>
                      </div>
                      <p className="text-white/40 text-sm mb-4">
                        {hasActiveResearchConsent 
                          ? 'You recorded the synthetic workflow acknowledgement.'
                          : 'Review how a future consent interaction could be presented.'}
                      </p>
                      {!hasActiveResearchConsent && (
                        <button onClick={() => setActiveTab('consent')} className="text-[#00d4aa] text-sm hover:underline">
                          Review acknowledgement →
                        </button>
                      )}
                    </div>

                    <div className={`card-glass p-6 ${connections.length > 0 ? 'border-l-2 border-[#00d4aa]' : 'border-l-2 border-white/20'}`}>
                      <div className="flex items-center gap-3 mb-4">
                        <span className={`w-8 h-8 rounded-full flex items-center justify-center ${connections.length > 0 ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : 'bg-white/10 text-white/40'}`}>
                          {connections.length > 0 ? '✓' : '2'}
                        </span>
                        <span className="text-white font-medium">Test FHIR Import</span>
                      </div>
                      <p className="text-white/40 text-sm mb-4">
                        {!SYNTHETIC_FHIR_UPLOADS_ENABLED
                          ? 'Disabled in this deployment. No real health records are accepted.'
                          : connections.length > 0
                          ? `Connected to ${connections.length} source(s).`
                          : 'Import a synthetic FHIR bundle to test this workflow.'}
                      </p>
                      {SYNTHETIC_FHIR_UPLOADS_ENABLED && hasActiveResearchConsent && connections.length === 0 && (
                        <button onClick={() => setActiveTab('data')} className="text-[#00d4aa] text-sm hover:underline">
                          Open test import →
                        </button>
                      )}
                    </div>

                    <div className={`card-glass p-6 ${extractedData.length > 0 ? 'border-l-2 border-[#00d4aa]' : 'border-l-2 border-white/20'}`}>
                      <div className="flex items-center gap-3 mb-4">
                        <span className={`w-8 h-8 rounded-full flex items-center justify-center ${extractedData.length > 0 ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : 'bg-white/10 text-white/40'}`}>
                          {extractedData.length > 0 ? '✓' : '3'}
                        </span>
                        <span className="text-white font-medium">Review Activity</span>
                      </div>
                      <p className="text-white/40 text-sm mb-4">
                        {extractedData.length > 0
                          ? `${extractedData.length} synthetic record(s) are available for pilot testing.`
                          : 'Nothing has been contributed yet. What you contribute, and what it does, is tracked under "What your data did".'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* What came of it. Contributing data and hearing nothing
                    back is the most common complaint about research sharing. */}
                {studyResults.length > 0 && (
                  <div className="mb-12" data-testid="patient-study-results">
                    <h2 className="text-lg font-medium text-white mb-2">Findings from studies you joined</h2>
                    <p className="text-white/40 text-sm mb-6">
                      Written by the study team for participants. These describe what researchers
                      found across a group — they are not advice about your own care.
                    </p>
                    <div className="space-y-3">
                      {studyResults.map((result) => (
                        <article key={result.id} className="card-glass p-5">
                          <p className="text-white/30 text-xs uppercase tracking-wider mb-2">{result.study_name}</p>
                          <h3 className="text-white font-medium mb-3">{result.title}</h3>
                          <p className="text-white/60 text-sm leading-relaxed whitespace-pre-line">
                            {result.plain_language_summary}
                          </p>
                          <p className="text-white/30 text-xs mt-4">
                            Published {new Date(result.published_at).toLocaleDateString()}
                          </p>
                          {result.citation && (
                            <a
                              href={result.citation}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-block text-emerald-300 text-sm mt-2 hover:underline"
                            >
                              Read the full publication →
                            </a>
                          )}
                          <p className="text-white/35 text-xs mt-4 pt-3 border-t border-white/10">
                            {result.disclaimer}
                          </p>
                        </article>
                      ))}
                    </div>
                  </div>
                )}

                {/* Where the data has gone. An access log says a query ran; this
                    says a file exists and who holds it. */}
                {dataReleases.length > 0 && (
                  <div className="mb-12" data-testid="patient-data-releases">
                    <h2 className="text-lg font-medium text-white mb-2">Extracts containing your data</h2>
                    <p className="text-white/40 text-sm mb-6">
                      Revoking consent stops any new extract. A file a researcher has already
                      downloaded is held outside this system and cannot be recalled automatically.
                    </p>
                    <div className="space-y-px">
                      {dataReleases.map((release) => (
                        <div key={release.id} className="card-glass p-4">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="text-white/70 text-sm">{release.study_name}</span>
                            <span className={`text-xs uppercase tracking-wider ${release.downloaded ? 'text-amber-300' : 'text-white/40'}`}>
                              {release.downloaded ? 'Downloaded' : 'Not downloaded'}
                            </span>
                          </div>
                          <p className="text-white/30 text-xs mt-1">
                            Released {release.released_at ? new Date(release.released_at).toLocaleDateString() : 'unknown'}
                            {' • '}alongside {release.subject_count} participant(s)
                            {' • '}sha256:{(release.content_digest || '').slice(0, 12)}
                          </p>
                          {release.withdrawal_required && (
                            <p className="text-amber-300/80 text-xs mt-1">
                              You revoked consent. The receiving researcher has been notified to destroy their copy.
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

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
                      <p className="text-white/30 text-sm mt-2">When a pilot query exercises your synthetic test data, the event will appear here.</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* CONSENT TAB */}
            {activeTab === 'consent' && (
              <motion.div key="consent" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="max-w-4xl">
                  <h2 className="text-lg font-medium text-white mb-2">Acknowledgement Prototype</h2>
                  <p className="text-white/40 mb-8">Evaluate consent language and state changes with synthetic examples. This is not research consent.</p>

                  {/* Active Consents */}
                  {consents.filter(c => c.status === 'active').length > 0 && (
                    <div className="mb-12">
                      <h3 className="text-sm uppercase tracking-wider text-white/40 mb-4">Recorded Acknowledgements</h3>
                      <div className="space-y-3">
                        {consents.filter(c => c.status === 'active').map((consent) => (
                          <div key={consent.id} className="card-glass p-6 border-l-2 border-[#00d4aa]">
                            <div className="flex items-start justify-between">
                              <div>
                                <h4 className="text-white font-medium mb-1">{consent.consent_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                                <p className="text-white/40 text-sm">Recorded {new Date(consent.signed_date).toLocaleDateString()}</p>
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
                    <h3 className="text-sm uppercase tracking-wider text-white/40 mb-4">Available Test Acknowledgements</h3>
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
                      <h3 className="text-sm uppercase tracking-wider text-white/40 mb-4">Archived Test Events</h3>
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

            {/* STUDIES TAB */}
            {activeTab === 'studies' && (
              <motion.div key="studies" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="max-w-4xl">
                  <h2 className="text-lg font-medium text-white mb-2">Study Matching Concept</h2>
                  <p className="text-white/40 mb-8">A future workflow concept for discovery and opt-in. HealthDB is not enrolling participants.</p>

                  {!PATIENT_STUDY_ENROLLMENT_ENABLED ? (
                    <div className="card-glass p-8 text-center border border-amber-500/20">
                      <span className="text-4xl mb-4 block">⏸</span>
                      <h3 className="text-white font-medium mb-2">Enrollment is not available</h3>
                      <p className="text-white/40 max-w-xl mx-auto">No studies on HealthDB are recruiting real participants. This area is retained for guided interface review only.</p>
                    </div>
                  ) : !hasActiveTrialMatchingConsent ? (
                    <div className="card-glass p-8 text-center border border-amber-500/20">
                      <span className="text-4xl mb-4 block">🔒</span>
                      <h3 className="text-white font-medium mb-2">Consent Required</h3>
                      <p className="text-white/40 mb-6">Review the test matching acknowledgement to exercise this synthetic workflow.</p>
                      <button
                        onClick={() => setActiveTab('consent')}
                        className="px-6 py-3 bg-amber-500 text-black text-xs uppercase tracking-wider font-medium"
                      >
                        Review Acknowledgement
                      </button>
                    </div>
                  ) : (
                    <>
                      {/* My Enrollments */}
                      {myStudies.filter(s => s.status === 'enrolled').length > 0 && (
                        <div className="mb-12">
                          <h3 className="text-sm uppercase tracking-wider text-white/40 mb-4">Studies You've Joined</h3>
                          <div className="space-y-3">
                            {myStudies.filter(s => s.status === 'enrolled').map((s) => (
                              <div key={s.id} className="card-glass p-6 border-l-2 border-[#00d4aa]">
                                <div className="flex items-start justify-between">
                                  <div>
                                    <h4 className="text-white font-medium mb-1">{s.study_name}</h4>
                                    <p className="text-white/40 text-sm">Joined {new Date(s.enrolled_at).toLocaleDateString()}</p>
                                  </div>
                                  <button
                                    onClick={() => handleLeaveStudy(s.study_id)}
                                    disabled={studyActionId === s.study_id}
                                    className="px-3 py-1 border border-red-500/30 text-red-400 text-xs uppercase tracking-wider hover:bg-red-500/10 transition-colors disabled:opacity-50"
                                  >
                                    Leave
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Available Studies */}
                      <div>
                        <h3 className="text-sm uppercase tracking-wider text-white/40 mb-4">Recruiting Now</h3>
                        {availableStudies.length > 0 ? (
                          <div className="space-y-3">
                            {availableStudies.map((study) => (
                              <div key={study.id} className={`card-glass p-6 ${study.already_enrolled ? 'opacity-50' : ''}`}>
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                      <h4 className="text-white font-medium">{study.name}</h4>
                                      {study.already_enrolled && <span className="px-2 py-0.5 text-xs bg-[#00d4aa]/20 text-[#00d4aa]">JOINED</span>}
                                    </div>
                                    {study.description && <p className="text-white/40 text-sm mb-3">{study.description}</p>}
                                    {study.eligibility_summary && (
                                      <p className="text-white/50 text-sm mb-3"><span className="text-white/30 uppercase text-xs tracking-wider">Eligibility: </span>{study.eligibility_summary}</p>
                                    )}
                                    <div className="flex items-center gap-4 text-white/30 text-xs">
                                      {study.principal_investigator && <span>PI: {study.principal_investigator}</span>}
                                      <span>{study.enrolled_count} participant{study.enrolled_count === 1 ? '' : 's'}</span>
                                    </div>
                                  </div>
                                  {!study.already_enrolled && (
                                    <button
                                      onClick={() => handleJoinStudy(study.id)}
                                      disabled={studyActionId === study.id}
                                      className="ml-4 px-4 py-2 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors disabled:opacity-50"
                                    >
                                      {studyActionId === study.id ? 'Joining...' : 'Join Study'}
                                    </button>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="card-glass p-8 text-center">
                            <p className="text-white/40">No studies are currently recruiting</p>
                            <p className="text-white/30 text-sm mt-2">Check back later for new research opportunities matching your profile.</p>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              </motion.div>
            )}

            {/* DATA TAB */}
            {activeTab === 'data' && (
              <motion.div key="data" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="max-w-4xl">
                  <h2 className="text-lg font-medium text-white mb-2">Synthetic Test Data</h2>
                  <p className="text-white/40 mb-8">This pilot workspace is for fictional or generated records only.</p>

                  {/* Requirement check */}
                  {!SYNTHETIC_FHIR_UPLOADS_ENABLED ? (
                    <div className="card-glass p-8 text-center border border-amber-500/20">
                      <span className="text-4xl mb-4 block">⏸</span>
                      <h3 className="text-white font-medium mb-2">Record intake is closed</h3>
                      <p className="text-white/40 max-w-xl mx-auto">
                        This deployment does not accept FHIR uploads or real health information. A controlled pilot can enable synthetic imports explicitly.
                      </p>
                    </div>
                  ) : !hasActiveResearchConsent ? (
                    <div className="card-glass p-8 text-center border border-amber-500/20">
                      <span className="text-4xl mb-4 block">🔒</span>
                      <h3 className="text-white font-medium mb-2">Consent Required</h3>
                      <p className="text-white/40 mb-6">Review the synthetic workflow acknowledgement before importing test records.</p>
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
                          <h3 className="text-sm uppercase tracking-wider text-white/40">Synthetic Sources</h3>
                          <button
                            onClick={() => setShowConnectionModal(true)}
                            className="px-4 py-2 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors"
                          >
                            + Import Test Bundle
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
                            <span className="text-4xl mb-4 block">📋</span>
                            <h3 className="text-white font-medium mb-2">No Synthetic Records Imported</h3>
                            <p className="text-white/40 mb-6">Use a fictional FHIR R4 bundle to evaluate the workflow. Never upload real patient data.</p>
                            <button
                              onClick={() => setShowConnectionModal(true)}
                              className="px-6 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium"
                            >
                              Import Test Bundle
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

            {/* WHAT YOUR DATA DID — the chain, including where it stops */}
            {activeTab === 'contribution' && (
              <motion.div key="contribution" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="max-w-3xl">
                  <h2 className="text-lg font-medium text-white mb-2">What your data did</h2>
                  <p className="text-white/45 text-sm mb-8 leading-relaxed">
                    {contribution?.summary || 'Loading your contribution record…'}
                  </p>

                  {contribution?.stages && (
                    <ol className="relative" data-testid="contribution-chain">
                      {contribution.stages.map((stageItem, index) => (
                        <li key={stageItem.key} className="relative pl-10 pb-8 last:pb-0">
                          {/* The connecting line stops where the chain stops. */}
                          {index < contribution.stages.length - 1 && (
                            <span
                              aria-hidden="true"
                              className={`absolute left-[11px] top-6 bottom-0 w-px ${
                                stageItem.reached ? 'bg-emerald-400/30' : 'bg-white/10'
                              }`}
                            />
                          )}
                          <span
                            aria-hidden="true"
                            className={`absolute left-0 top-1 w-[23px] h-[23px] rounded-full border flex items-center justify-center text-[11px] ${
                              stageItem.reached
                                ? 'border-emerald-400/50 text-emerald-300'
                                : 'border-white/15 text-white/25'
                            }`}
                          >
                            {stageItem.reached ? '\u2713' : index + 1}
                          </span>

                          <h3 className={`text-sm font-medium mb-1 ${
                            stageItem.reached ? 'text-white' : 'text-white/45'
                          }`}>
                            {stageItem.headline}
                          </h3>
                          <p className="text-white/45 text-sm leading-relaxed">{stageItem.detail}</p>

                          {stageItem.blocked_because && (
                            <p className="text-white/30 text-xs mt-2">{stageItem.blocked_because}</p>
                          )}

                          {stageItem.key === 'enrolled' && stageItem.items.length > 0 && (
                            <ul className="mt-3 space-y-1">
                              {stageItem.items.map((item, i) => (
                                <li key={i} className="text-white/60 text-sm">{item.study_name}</li>
                              ))}
                            </ul>
                          )}

                          {stageItem.key === 'released' && stageItem.items.length > 0 && (
                            <ul className="mt-3 space-y-2">
                              {stageItem.items.map((item, i) => (
                                <li key={i} className="text-xs text-white/40">
                                  {item.released_at ? new Date(item.released_at).toLocaleDateString() : 'date unknown'}
                                  {' \u00b7 '}{item.downloaded ? 'downloaded by the study team' : 'not downloaded'}
                                  {' \u00b7 '}sha256:{(item.content_digest || '').slice(0, 12)}
                                  {item.withdrawal_required && (
                                    <span className="text-amber-300/80"> \u00b7 withdrawal requested</span>
                                  )}
                                </li>
                              ))}
                            </ul>
                          )}

                          {stageItem.key === 'published' && stageItem.items.length > 0 && (
                            <ul className="mt-3 space-y-1">
                              {stageItem.items.map((item, i) => (
                                <li key={i} className="text-white/60 text-sm">{item.title}</li>
                              ))}
                            </ul>
                          )}
                        </li>
                      ))}
                    </ol>
                  )}

                  <p className="text-white/30 text-xs mt-10 pt-6 border-t border-white/10 leading-relaxed">
                    HealthDB does not pay for data and does not offer points, gift cards or
                    redemption. Paying people for their medical history prices them; this record
                    is meant to show you what your contribution did instead.
                  </p>
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
                <div className="max-w-none">
                  <ConsentText content={selectedTemplate.content} />
                </div>
              </div>
              <div className="p-6 border-t border-white/10">
                <p className="text-white/40 text-sm mb-4">
                  By clicking “Record test acknowledgement,” you confirm only that you reviewed this prototype screen. This is not research consent.
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
                    {isSubmitting ? 'Recording...' : 'Record test acknowledgement'}
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Connection Modal */}
      <AnimatePresence>
        {showConnectionModal && SYNTHETIC_FHIR_UPLOADS_ENABLED && (
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
                <h2 className="text-xl text-white">Import Synthetic FHIR Data</h2>
                <button onClick={() => setShowConnectionModal(false)} className="p-2 hover:bg-white/10">
                  <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6 space-y-4">
                <p className="text-white/40 text-sm mb-6">
                  Upload a fictional or generated FHIR R4 Bundle to exercise the pilot workflow.
                  Do not upload real patient records, identifiers, or protected health information.
                </p>

                <label className={`w-full card-glass card-hover p-4 text-left flex items-center gap-4 cursor-pointer ${isSubmitting ? 'opacity-50 pointer-events-none' : ''}`}>
                  <span className="text-2xl">⬆️</span>
                  <div>
                    <p className="text-white font-medium">
                      {isSubmitting ? 'Importing…' : 'Upload synthetic FHIR bundle'}
                    </p>
                    <p className="text-white/40 text-sm">Choose a test JSON file with resourceType “Bundle”</p>
                  </div>
                  <input
                    type="file"
                    accept=".json,application/json"
                    onChange={handleFHIRUpload}
                    disabled={isSubmitting}
                    className="hidden"
                  />
                </label>

                <p className="text-white/40 text-xs leading-relaxed">
                  The prototype runs identifier-removal checks, but those controls have not been
                  independently validated for real-world health data. Synthetic input is required.
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default PatientPortal;
