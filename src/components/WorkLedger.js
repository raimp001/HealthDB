import React, { useEffect, useState } from 'react';
import { apiRequest } from '../lib/api';
const input = 'w-full bg-black border border-white/30 rounded p-3 mt-2';
const empty = { title: '', description: '', evidence_ref: '', minutes: 1 };
export default function WorkLedger({ studyId }) {
  const [data, setData] = useState(null), [draft, setDraft] = useState(empty);
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [selected, setSelected] = useState(null), [reason, setReason] = useState(''), [policy, setPolicy] = useState('');
  const request = (suffix = '', options = {}) => apiRequest(`/api/workspace/projects/${encodeURIComponent(studyId)}/contributions${suffix}`, {
    ...options, headers: { Authorization: `Bearer ${sessionStorage.getItem('token')}`, 'Content-Type': 'application/json' },
  });
  const load = async () => { setBusy(true); setError(''); try { setData(await request()); setSelected(null); } catch (e) { setError(e.message); } finally { setBusy(false); } };
  useEffect(() => { load(); }, [studyId]);
  const submit = async e => {
    e.preventDefault(); setBusy(true); setError('');
    try { await request('', { method: 'POST', body: JSON.stringify(draft) }); setDraft(empty); await load(); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const decide = async e => {
    e.preventDefault(); setBusy(true); setError('');
    try { await request(`/${selected.id}/events`, { method: 'POST', body: JSON.stringify({ revision: selected.revision, action: selected.action, reason, policy_ref: ['accepted', 'changes_requested'].includes(selected.action) ? policy : '' }) }); await load(); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const choose = (row, action) => { setSelected({ id: row.id, revision: row.revision, action }); setReason(''); setPolicy(''); };
  return <section className="border border-white/20 rounded-xl p-5 my-8">
    <h3 className="text-2xl mb-3">Research contribution ledger</h3>
    <p className="text-white/60">Record work and its evidence reference, then have the project owner review it. Acceptance credits work; it does not approve a payment or authorship. No self-approval. Enter work metadata only, with no patient information or private access links.</p>
    {error && <p role="alert" className="text-red-300 my-3">{error}</p>}
    {busy && <p role="status">Updating ledger…</p>}
    <button type="button" disabled={busy} onClick={load} className="border rounded px-4 py-2 my-4">Refresh ledger</button>
    {data && !data.items.length && <p>No work submitted yet.</p>}
    {data?.has_more && <p>Showing the first 200 entries. Full ledger browsing is not yet available.</p>}
    {data?.items.map(row => <article key={row.id} className="border-b border-white/20 py-4">
      <h4 className="text-xl">{row.title} · {row.status.replaceAll('_', ' ')}{row.mine ? ' · Yours' : ''}</h4>
      <p>{row.description}</p><p className="text-white/60">Reported time: {row.minutes} minutes · Evidence reference: {row.evidence_ref}</p>
      <details className="my-3"><summary>Audit history ({row.events.length})</summary><ol className="space-y-3 my-3">{row.events.map(ev => <li key={ev.revision}>
        <strong>{ev.action.replaceAll('_', ' ')}</strong> · {ev.actor} · {new Date(ev.timestamp).toLocaleString()} · Revision {ev.revision}
        {ev.content.reason && <p>{ev.content.reason}</p>}{ev.content.policy_ref && <p>Policy reference (not independently validated): {ev.content.policy_ref}</p>}
      </li>)}</ol></details>
      <div className="flex flex-wrap gap-3">
        {row.can_review && ['submitted', 'resubmitted', 'disputed'].includes(row.status) && <>
          <button disabled={busy} className="border rounded p-2" onClick={() => choose(row, 'accepted')}>Accept work</button>
          <button disabled={busy} className="border rounded p-2" onClick={() => choose(row, 'changes_requested')}>Request changes</button>
        </>}
        {row.mine && ['accepted', 'changes_requested'].includes(row.status) && <button disabled={busy} className="border rounded p-2" onClick={() => choose(row, 'disputed')}>Dispute decision</button>}
        {row.mine && row.status === 'changes_requested' && <button disabled={busy} className="border rounded p-2" onClick={() => choose(row, 'resubmitted')}>Resubmit with explanation</button>}
      </div>
    </article>)}
    {selected && <form onSubmit={decide} className="my-5"><fieldset disabled={busy}>
      <legend className="text-xl">Record: {selected.action.replaceAll('_', ' ')}</legend>
      <label className="block">Reason and evidence of changes<textarea required minLength={10} maxLength={1000} className={input} value={reason} onChange={e => setReason(e.target.value)} /></label>
      {['accepted', 'changes_requested'].includes(selected.action) && <label className="block">Applicable policy reference (optional; no payment authorization)<input maxLength={300} className={input} value={policy} onChange={e => setPolicy(e.target.value)} /></label>}
      <button className="border rounded p-3 mt-3">Record decision</button>
      <button type="button" className="p-3" onClick={() => setSelected(null)}>Cancel</button>
    </fieldset></form>}
    <form onSubmit={submit} className="mt-6"><fieldset disabled={busy} className="space-y-3">
      <legend className="text-xl mb-3">Submit completed work</legend>
      <label className="block">Work title<input required minLength={3} maxLength={150} className={input} value={draft.title} onChange={e => setDraft({ ...draft, title: e.target.value })} /></label>
      <label className="block">What you completed<textarea required minLength={10} maxLength={1000} className={input} value={draft.description} onChange={e => setDraft({ ...draft, description: e.target.value })} /></label>
      <label className="block">Evidence reference (document ID or revision)<input required minLength={3} maxLength={300} className={input} value={draft.evidence_ref} onChange={e => setDraft({ ...draft, evidence_ref: e.target.value })} /></label>
      <label className="block">Time spent, minutes<input type="number" required min={1} max={100000} step={1} className={input} value={draft.minutes} onChange={e => setDraft({ ...draft, minutes: Number(e.target.value) })} /></label>
      <button className="bg-emerald-300 text-black rounded px-5 py-3">Submit work for review</button>
    </fieldset></form>
  </section>;
}
