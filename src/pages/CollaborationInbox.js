import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest, loadPanels } from '../lib/api';

const authorizedRequest = (path, options = {}) => apiRequest(path, {
  ...options, headers: { Authorization: `Bearer ${sessionStorage.getItem('token')}` },
});

export default function CollaborationInbox() {
  const [invitations, setInvitations] = useState([]);
  const [studies, setStudies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      // Two independent lists. One being unavailable should not hide the
      // other — an invitation you cannot see is one you cannot answer.
      const { values, failures } = await loadPanels([
        () => authorizedRequest('/api/researcher/invitations'),
        () => authorizedRequest('/api/researcher/collaborations'),
      ]);
      setInvitations(values[0] || []); setStudies(values[1] || []);
      if (failures.length === values.length) setError(failures[0].error?.message || 'Could not load your inbox.');
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  const respond = async (id, decision) => {
    setBusy(true); setError('');
    try {
      await authorizedRequest(`/api/researcher/invitations/${id}/respond?decision=${decision}`, { method: 'POST' });
      await load();
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };
  return <article className="max-w-5xl mx-auto px-6 py-16 text-white">
    <p className="text-emerald-300">HealthDB AI · Research network</p>
    <h1 className="text-4xl my-5">Your collaborations</h1>
    <Link to="/projects" className="inline-block text-emerald-300 underline mb-5">Find projects and open shared plans</Link>
    <p className="text-white/70 mb-8">Review invitations before granting participation. Accepting joins a pilot workspace; it does not authorize patient-data transfer or replace institutional agreements.</p>
    {error && <div role="alert" className="border border-red-300 p-4 mb-5">{error} <button onClick={load} disabled={busy || loading} className="underline">Retry</button></div>}
    {loading ? <p role="status">Loading collaborations…</p> : <>
      <h2 className="text-2xl mb-4">Pending invitations</h2>
      {!invitations.length && <p className="text-white/60 mb-8">No pending invitations. Study owners can invite you using your account email. Invitations appear here; email delivery is not enabled.</p>}
      {invitations.map(item => <section key={item.id} className="border border-white/20 p-5 mb-4 rounded-lg">
        <h3 className="text-xl">{item.study_name}</h3><p className="text-white/60 my-3">Role: {item.role.replaceAll('_', ' ')}</p>
        <div className="flex gap-4"><button disabled={busy} onClick={() => respond(item.id, 'accept')} className="bg-emerald-300 text-black px-5 py-3 rounded disabled:opacity-50">Accept invitation</button><button disabled={busy} onClick={() => respond(item.id, 'decline')} className="border px-5 py-3 rounded disabled:opacity-50">Decline invitation</button></div>
      </section>)}
      <h2 className="text-2xl mt-10 mb-4">Accepted studies</h2>
      {!studies.length && <p className="text-white/60">No accepted collaborations yet.</p>}
      {studies.map(study => <section key={study.study_id} className="border border-white/20 p-5 mb-4 rounded-lg"><h3 className="text-xl">{study.study_name}</h3><p className="text-white/70 mt-2">{study.pi_name} · {study.pi_organization || 'Institution not specified'} · {study.my_role.replaceAll('_', ' ')}</p><p className="mt-3">{study.description}</p></section>)}
    </>}
    <Link to="/research-readiness" className="block text-emerald-300 underline mt-8">Review institutional launch readiness</Link>
    <Link to="/research" className="inline-block text-emerald-300 underline mt-8">Open research workspace</Link>
  </article>;
}
