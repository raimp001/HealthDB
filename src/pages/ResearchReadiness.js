import React, { useState } from 'react';
import { apiRequest } from '../lib/api';
import { useSearchParams } from 'react-router-dom';
import EvidenceWithdrawal from '../components/EvidenceWithdrawal';

const request = (path, options = {}) => apiRequest(path, { ...options,
  headers: { Authorization: `Bearer ${sessionStorage.getItem('token')}`, 'Content-Type': 'application/json' },
});

export default function ResearchReadiness() {
  const [params] = useSearchParams();
  const [study, setStudy] = useState(params.get('study') || '');
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [category, setCategory] = useState('ehr_validation');
  const [reference, setReference] = useState('');
  const [hash, setHash] = useState('');
  const [scope, setScope] = useState('');
  const [expiry, setExpiry] = useState('');
  const load = async () => {
    setBusy(true); setError(''); setReport(null);
    try { setReport(await request(`/api/researcher/studies/${encodeURIComponent(study)}/readiness`)); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const submit = async e => {
    e.preventDefault(); setBusy(true); setError('');
    try {
      await request(`/api/researcher/studies/${encodeURIComponent(study)}/readiness`, {
        method: 'POST', body: JSON.stringify({ category, reference, sha256: hash, scope, expires_at: new Date(expiry).toISOString() }),
      });
      setReference(''); setHash(''); setScope(''); setExpiry('');
      await load();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };
  const review = async (id, decision) => {
    setBusy(true); setError('');
    try {
      await request(`/api/research-evidence/${id}/review`, { method: 'POST', body: JSON.stringify({ decision }) });
      await load();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };
  return <article className="max-w-4xl mx-auto px-6 py-16 text-white">
    <h1 className="text-4xl mb-5">Institutional launch readiness</h1>
    <p className="text-white/70 mb-8">Track evidence for EHR validation, privacy, agreements and licensing. Store documents in your institution’s approved repository—not here. Use document reference IDs and hashes only; do not enter patient information, credentials or signed document contents.</p>
    <form onSubmit={e => { e.preventDefault(); load(); }} className="flex flex-wrap gap-4 items-end mb-8">
      <label>Study ID<input required disabled={busy} value={study} onChange={e => { setStudy(e.target.value); setReport(null); }} className="block bg-black border p-3 mt-2" /></label>
      <button disabled={busy} className="bg-white text-black px-5 py-3 disabled:opacity-50">Load readiness</button>
    </form>
    {busy && <p role="status">Saving or loading…</p>}
    {error && <p role="alert" className="text-red-300 my-5">{error}</p>}
    {report && <>
      <p className="border border-amber-300 p-4 mb-6">{report.notice}</p>
      <h2 className="text-2xl mb-4">{report.evidence_complete ? 'Evidence references complete — launch still blocked' : 'Evidence still needed'}</h2>
      <ul className="space-y-3 mb-8">{report.requirements.map(r => <li key={r.category}>{r.evidence_current ? '✓ Current reviewed evidence' : '○ Missing or expired'} — {r.title}</li>)}</ul>
      <p className="mb-6">All {report.requirements.length} requirement references must cover the same scope. Current complete scopes: {report.complete_scopes.join('; ') || 'None'}.</p>
      {!!report.open_withdrawals && <p className="border border-amber-300 p-4 mb-6">{report.open_withdrawals} open withdrawal follow-up(s). Blocked scopes: {(report.blocked_scopes || []).join('; ')}. Replacement evidence cannot clear an unresolved withdrawal.</p>}
      {report.can_submit && <>
      <h2 className="text-2xl mb-4">Submit an evidence reference</h2>
      <p className="text-white/60 mb-4">Study owners only. An independent platform administrator must inspect the source document outside this app before verifying its reference. This is not an electronic signature.</p>
      <p className="text-white/60 mb-4">Consent and authorization references cover the study’s reviewed process and document version, not individual participants. Store signed consent and patient linkage only in the institution’s approved system.</p>
      <form onSubmit={submit} className="grid gap-4">
        <label>Requirement<select value={category} onChange={e => setCategory(e.target.value)} className="block bg-black border p-3 w-full">{report.requirements.map(r => <option key={r.category} value={r.category}>{r.title}</option>)}</select></label>
        <label>Document reference ID<input required pattern="[A-Za-z0-9_.:/-]+" maxLength={120} value={reference} onChange={e => setReference(e.target.value)} className="block bg-black border p-3 w-full" /></label>
        <label>Document SHA-256 (64 lowercase hexadecimal characters)<input required pattern="[a-f0-9]{64}" value={hash} onChange={e => setHash(e.target.value)} className="block bg-black border p-3 w-full" /></label>
        <label>Scope: institution IDs, dataset version, approved purpose and recipient IDs<input required minLength={10} maxLength={200} value={scope} onChange={e => setScope(e.target.value)} className="block bg-black border p-3 w-full" /></label>
        <label>Review expiration (your local time)<input required type="datetime-local" value={expiry} onChange={e => setExpiry(e.target.value)} className="block bg-black border p-3" /></label>
        <button disabled={busy} className="bg-emerald-300 text-black p-3 disabled:opacity-50">Submit for review</button>
      </form>
      </>}
      <h2 className="text-2xl mt-10 mb-4">Evidence history</h2>
      {!report.evidence.length && <p>No evidence submitted.</p>}
      {report.evidence.map(item => <section key={item.id} className="border border-white/20 p-4 mb-3 break-words">
        <h3>{item.category} · {item.status}</h3><p>{item.reference} — {item.scope}</p>
        <p>Expires: {new Date(item.expires_at).toLocaleString()}</p><p className="text-sm text-white/60">SHA-256: {item.sha256}</p>
        {item.review_history.map((event, index) => <div key={index} className="text-sm border-l pl-3 mt-2"><p>{event.decision} · {new Date(event.at).toLocaleString()} · reviewer {event.reviewer_id}</p>{event.reference && <p>Reference: {event.reference}</p>}{event.reason && <p>{event.reason}</p>}{event.future_use && <p>Future use: {event.future_use} · Recipients: {event.recipients} · Held data: {event.retained_data}</p>}</div>)}
        {report.can_review && item.can_independently_review !== false && <div className="flex gap-4 mt-4">
          {item.status === 'submitted' && <><button disabled={busy} onClick={() => review(item.id, 'verified')} className="border p-2">Verify reviewed evidence</button><button disabled={busy} onClick={() => review(item.id, 'rejected')} className="border p-2">Reject</button></>}
          {item.status === 'verified' && <button disabled={busy} onClick={() => review(item.id, 'revoked')} className="border p-2">Revoke verification</button>}
        </div>}
        <EvidenceWithdrawal item={item} canWithdraw={report.can_submit || report.can_review} disabled={busy} onSaved={load} />
      </section>)}
    </>}
  </article>;
}
