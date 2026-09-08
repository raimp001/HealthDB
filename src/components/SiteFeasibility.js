import React, { useEffect, useState } from 'react';
import { apiRequest } from '../lib/api';

const input = 'w-full bg-black border border-white/30 rounded p-3 mt-2';
export default function SiteFeasibility({ studyId, planRevision, planDirty }) {
  const [data, setData] = useState(null);
  const [draft, setDraft] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [dirty, setDirty] = useState(false);
  const request = options => apiRequest(`/api/workspace/projects/${encodeURIComponent(studyId)}/feasibility`, {
    ...options, headers: { Authorization: `Bearer ${sessionStorage.getItem('token')}`, 'Content-Type': 'application/json' },
  });
  const load = async () => {
    setBusy(true); setError(''); setNotice('');
    try {
      const r = await request(); setData(r);
      const own = r.declarations.find(d => d.mine);
      setDraft({ revision: own?.revision || 0, plan_revision: r.plan_revision, site_label: own?.site_label || '', approvals_needed: own?.approvals_needed || '',
        mappings: r.variables.map(v => own?.mappings.find(m => m.variable === v.name) || { variable: v.name, availability: 'unknown', source: '', transformation: '' }) });
      setDirty(false);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  useEffect(() => { setData(null); setDraft(null); load(); }, [studyId]);
  const edit = (key, value) => { setDraft(d => ({ ...d, [key]: value })); setDirty(true); setNotice(''); };
  const mapping = (i, key, value) => edit('mappings', draft.mappings.map((m, j) => i === j ? { ...m, [key]: value } : m));
  const save = async e => {
    e.preventDefault(); setBusy(true); setError('');
    try { await request({ method: 'PUT', body: JSON.stringify(draft) }); await load(); setNotice('Declaration saved. This is a planning statement, not validated data access.'); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const outdated = data && data.plan_revision !== planRevision;
  return <section className="border border-white/20 rounded-xl p-5 my-8">
    <h3 className="text-2xl mb-3">Site feasibility and data mapping</h3>
    <p className="text-white/60 mb-4">Each accepted team member can declare expected availability for one site. Site names and mappings are self-reported, not verified institutional commitments. Enter definitions only—no patient values, counts, identifiers or credentials.</p>
    {error && <p role="alert" className="text-red-300 my-3">{error}</p>}
    {notice && <p role="status" className="text-emerald-300 my-3">{notice}</p>}
    {busy && <p role="status">Loading or saving feasibility…</p>}
    <button type="button" disabled={busy} className="border rounded px-4 py-2 mb-4" onClick={load}>Reload saved declarations</button>
    {dirty && <p className="text-amber-200">Unsaved declaration. Reloading discards these edits.</p>}
    {(outdated || planDirty) && <p className="text-amber-200 my-3">Save the project plan first, then reload declarations and check every mapping before saving.</p>}
    {data && <>
      <h4 className="text-xl my-4">Team declarations</h4>
      {!data.declarations.length && <p>No declarations yet.</p>}
      {data.declarations.map((d, i) => <details key={i} className="border-b border-white/20 py-3">
        <summary className="cursor-pointer">{d.site_label} · {d.reporter}{d.mine ? ' · Yours' : ''} · {d.stale || d.plan_revision !== planRevision ? 'Needs review: plan changed' : 'Matches saved plan revision'}</summary>
        <p className="my-3">Approvals or blockers: {d.approvals_needed || 'Not specified; this does not mean approved'}</p>
        <ul className="space-y-2">{d.mappings.map(m => <li key={m.variable}><strong>{m.variable}</strong>: {m.availability} · Source: {m.source || 'Unspecified'}{m.transformation && <p>Mapping: {m.transformation}</p>}</li>)}</ul>
      </details>)}
      {!data.variables.length ? <p className="mt-4">Add variables to the study plan and save it before declaring feasibility.</p> : draft && <form className="mt-6" onSubmit={save}>
        <fieldset disabled={busy || outdated || planDirty} className="space-y-4">
          <legend className="text-xl mb-3">Your site declaration</legend>
          <label className="block">Site label<input required minLength={3} maxLength={150} className={input} value={draft.site_label} onChange={e => edit('site_label', e.target.value)} /></label>
          <label className="block">Approvals needed and remaining blockers<textarea maxLength={1000} className={input} value={draft.approvals_needed} onChange={e => edit('approvals_needed', e.target.value)} /></label>
          {draft.mappings.map((m, i) => <div key={m.variable} className="border border-white/20 rounded-lg p-4">
            <h5 className="font-semibold">{m.variable}{data.variables.find(v => v.name === m.variable)?.required ? ' · Required' : ' · Optional'}</h5>
            <p className="text-white/60">{data.variables.find(v => v.name === m.variable)?.definition}</p>
            <label className="block">Expected availability<select className={input} value={m.availability} onChange={e => mapping(i, 'availability', e.target.value)}>{['unknown', 'available', 'derivable', 'unavailable'].map(s => <option key={s}>{s}</option>)}</select></label>
            <label className="block mt-3">Source field or system<input required={['available', 'derivable'].includes(m.availability)} maxLength={200} className={input} value={m.source} onChange={e => mapping(i, 'source', e.target.value)} /></label>
            <label className="block mt-3">Transformation, units and coding rules<textarea required={m.availability === 'derivable'} maxLength={500} className={input} value={m.transformation} onChange={e => mapping(i, 'transformation', e.target.value)} /></label>
          </div>)}
          <button className="bg-emerald-300 text-black rounded px-5 py-3" disabled={!dirty && !data.declarations.some(d => d.mine && d.stale)}>Save my declaration</button>
        </fieldset>
      </form>}
    </>}
  </section>;
}
