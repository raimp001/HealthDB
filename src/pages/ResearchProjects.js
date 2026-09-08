import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { apiRequest, readSessionUser } from '../lib/api';
import { myelomaPilot } from '../data/myelomaPilot';
import SiteFeasibility from '../components/SiteFeasibility';
import WorkLedger from '../components/WorkLedger';

const request = (path, options = {}) => apiRequest(`/api/workspace${path}`, { ...options, headers: { Authorization: `Bearer ${sessionStorage.getItem('token')}`, 'Content-Type': 'application/json' } });
const input = 'w-full bg-black border border-white/30 rounded-lg p-3 mt-2 text-white';
const button = 'border border-white/30 rounded-lg px-4 py-2 hover:bg-white/10 disabled:opacity-40';
const fields = [['question', 'Research question', 'What specific question will this study answer?'], ['population', 'Population and eligibility', 'Define inclusion, exclusion and the population of interest.'], ['exposure', 'Exposure and comparator', 'Define treatment, exposure, comparison group and time zero.'], ['outcome', 'Primary outcome', 'Define the outcome, measurement window and censoring rules.'], ['analysis', 'Analysis plan', 'Describe confounders, missing data, bias checks and sensitivity analyses.'], ['impact', 'Intended use of the result', 'What decision would this inform? What further validation would be needed?'], ['seeking', 'Collaborators needed', 'For example: a statistician and sites with the relevant data.']];

export default function ResearchProjects() {
  const isAdmin = readSessionUser()?.user_type === 'admin';
  const [params, setParams] = useSearchParams();
  const id = params.get('study');
  const [projects, setProjects] = useState([]);
  const [report, setReport] = useState(null);
  const [interests, setInterests] = useState([]);
  const [comments, setComments] = useState([]);
  const [comment, setComment] = useState('');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [dirty, setDirty] = useState(false);
  const [query, setQuery] = useState('');
  const [directory, setDirectory] = useState({ items: [], has_more: false });
  const [page, setPage] = useState(0);
  const [interestMessages, setInterestMessages] = useState({});
  const load = async () => {
    setBusy(true); setError('');
    try {
      const [owned, listed, r] = await Promise.all([request('/projects'), request('/opportunities'), id ? request(`/projects/${encodeURIComponent(id)}`) : Promise.resolve(null)]);
      setProjects(owned); setDirectory(listed); setPage(0);
      if (id) {
        setReport(r); setDirty(false);
        const [discussion, applicants] = await Promise.all([request(`/projects/${encodeURIComponent(id)}/discussion`), r.can_edit ? request(`/projects/${encodeURIComponent(id)}/interests`) : Promise.resolve([])]);
        setComments(discussion); setInterests(applicants);
      }
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  useEffect(() => { setReport(null); setNotice(''); setDirty(false); load(); }, [id]);
  const discover = async (nextPage = 0) => {
    setBusy(true); setError('');
    try { setDirectory(await request(`/opportunities?q=${encodeURIComponent(query)}&offset=${nextPage * 20}`)); setPage(nextPage); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const change = (key, value) => { setReport(r => ({ ...r, plan: { ...r.plan, [key]: value } })); setDirty(true); setNotice(''); };
  const rowChange = (key, i, field, value) => change(key, report.plan[key].map((r, j) => j === i ? { ...r, [field]: value } : r));
  const mutate = async (path, body, after) => {
    setBusy(true); setError(''); setNotice('');
    try { const result = await request(path, { method: 'POST', body: JSON.stringify(body) }); await after(result); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const save = async e => {
    e.preventDefault(); setBusy(true); setError(''); setNotice('');
    try {
      const saved = await request(`/projects/${id}`, { method: 'PUT', body: JSON.stringify({ revision: report.revision, listed: report.listed, plan: report.plan }) });
      setReport(r => ({ ...r, revision: saved.revision })); setDirty(false); setNotice('Plan saved.');
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const download = () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify({ study_id: id, name: report.name, revision: report.revision, purpose: 'Research planning metadata only; not patient data or approved clinical evidence', plan: report.plan }, null, 2)], { type: 'application/json' }));
    const a = document.createElement('a'); a.href = url; a.download = 'healthdb-research-plan.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return <main className="max-w-6xl mx-auto px-6 py-16 text-white">
    <p className="text-emerald-300">HealthDB AI · Research workspace</p>
    <h1 className="text-4xl my-4">Turn a question into a shared project</h1>
    <p className="text-white/70 max-w-3xl mb-6">Define the data you need, organize the work, and connect with approved researchers. Enter study definitions only—never patient records, identifiers or individual results.</p>
    <div className="flex flex-wrap gap-3 mb-6">{!isAdmin && <Link className={button} to="/collaborations">Invitation inbox</Link>}<Link className={button} to={isAdmin ? '/admin' : '/research'}>{isAdmin ? 'Admin workspace' : 'Cohorts and study operations'}</Link></div>
    {error && <p role="alert" className="border border-red-400 p-4 my-4">{error} Your unsaved edits remain in this form.</p>}
    {notice && <p role="status" className="text-emerald-300 my-4">{notice}</p>}
    {busy && <p role="status">Working…</p>}
    <section className="border border-white/20 rounded-xl p-5 mb-8">
      <h2 className="text-2xl mb-4">Your projects</h2>
      <div className="flex flex-wrap gap-3 mb-4">{projects.map(p => <button className={button} disabled={busy || dirty} key={p.id} onClick={() => setParams({ study: p.id })}>{p.name}{p.owner ? '' : ' · Shared'}</button>)}</div>
      {!projects.length && !busy && <p className="text-white/60 mb-4">Create your first plan, or accept a collaboration invitation.</p>}
      <form className="flex flex-wrap gap-3 items-end" onSubmit={e => { e.preventDefault(); mutate('/projects', { name }, r => { setName(''); setParams({ study: r.id }); }); }}>
        <label className="flex-1">New project title<input required minLength={3} maxLength={150} value={name} onChange={e => setName(e.target.value)} className={input} /></label><button disabled={busy || dirty} className={button}>Create project</button>
      </form>
    </section>
    {report && <section className="mb-10">
      <h2 className="text-3xl mb-2">{report.name}</h2>
      <p className="text-white/60 mb-4">Revision {report.revision} · {dirty ? 'Unsaved edits: save or reload before switching projects' : 'Saved version'} · {report.can_edit ? 'Owner editing' : 'Shared plan: suggest changes in discussion'}</p>
      <div className="flex flex-wrap gap-3 mb-6"><button className={button} disabled={busy} onClick={load}>Reload saved plan</button><button className={button} disabled={dirty || busy || !report.revision} onClick={download}>Download plan JSON</button><Link className={button} to={`/research-readiness?study=${encodeURIComponent(id)}`}>Institutional readiness</Link></div>
      <form onSubmit={save}>
        <fieldset disabled={busy || !report.can_edit} className="space-y-5">
          {report.can_edit && report.revision === 0 && !dirty && <div className="border border-emerald-300/30 rounded-lg p-4"><p className="mb-3">Start with a proposed myeloma bispecific tumor-flare planning scaffold. It contains definitions and tasks only, requires clinical and governance review, and stays private until you choose to list it.</p><button type="button" className={button} onClick={() => { setReport(r => ({ ...r, listed: false, plan: JSON.parse(JSON.stringify(myelomaPilot)) })); setDirty(true); }}>Use myeloma pilot scaffold</button></div>}
          <div className="grid md:grid-cols-2 gap-5">{fields.map(([key, title, hint]) => <label key={key}>{title}<textarea className={input} rows={3} maxLength={key === 'analysis' ? 2000 : key === 'seeking' ? 300 : 1000} placeholder={hint} value={report.plan[key]} onChange={e => change(key, e.target.value)} /></label>)}</div>
          <h3 className="text-2xl">Data specification</h3>
          <p className="text-white/60">Define variables, not patient values. Source and unit definitions make site-to-site mapping reviewable. Saving this specification does not connect an EHR.</p>
          {!report.plan.variables.length && <p>No variables defined yet.</p>}
          {report.plan.variables.map((v, i) => <div key={i} className="grid md:grid-cols-2 gap-3 border border-white/20 rounded-lg p-4">
            <label>Variable name<input required pattern="[a-z][a-z0-9_]*" maxLength={80} className={input} value={v.name} onChange={e => rowChange('variables', i, 'name', e.target.value)} /></label>
            <label>Type<select className={input} value={v.type} onChange={e => rowChange('variables', i, 'type', e.target.value)}>{['number', 'category', 'boolean', 'year'].map(t => <option key={t}>{t}</option>)}</select></label>
            <label>Definition<input required minLength={3} maxLength={500} className={input} value={v.definition} onChange={e => rowChange('variables', i, 'definition', e.target.value)} /></label>
            <label>Expected source<input maxLength={150} className={input} value={v.source} onChange={e => rowChange('variables', i, 'source', e.target.value)} /></label>
            <label>Units or allowed categories<input maxLength={80} className={input} value={v.units} onChange={e => rowChange('variables', i, 'units', e.target.value)} /></label>
            <div className="flex items-center gap-4"><label><input type="checkbox" checked={v.required} onChange={e => rowChange('variables', i, 'required', e.target.checked)} /> Required</label><button type="button" className={button} onClick={() => change('variables', report.plan.variables.filter((_, j) => i !== j))}>Remove variable</button></div>
          </div>)}
          <button type="button" className={button} disabled={report.plan.variables.length >= 100} onClick={() => change('variables', [...report.plan.variables, { name: '', definition: '', type: 'category', source: '', units: '', required: true }])}>Add variable</button>
          <h3 className="text-2xl">Execution milestones</h3>
          <p className="text-white/60">{report.plan.milestones.filter(m => m.status === 'done').length} of {report.plan.milestones.length} complete. These are team-reported progress states, not regulatory approvals.</p>
          {report.plan.milestones.map((m, i) => <div className="grid md:grid-cols-3 gap-3 border border-white/20 p-4 rounded-lg" key={i}>
            <label>Milestone<input required minLength={3} maxLength={150} className={input} value={m.title} onChange={e => rowChange('milestones', i, 'title', e.target.value)} /></label><label>Responsible role<input maxLength={100} className={input} value={m.owner} onChange={e => rowChange('milestones', i, 'owner', e.target.value)} /></label>
            <label>Status<select className={input} value={m.status} onChange={e => rowChange('milestones', i, 'status', e.target.value)}><option value="todo">To do</option><option value="in_progress">In progress</option><option value="done">Done</option></select></label><button type="button" className={button} onClick={() => change('milestones', report.plan.milestones.filter((_, j) => i !== j))}>Remove milestone</button>
          </div>)}
          <button type="button" className={button} disabled={report.plan.milestones.length >= 40} onClick={() => change('milestones', [...report.plan.milestones, { title: '', owner: '', status: 'todo' }])}>Add milestone</button>
          <label className="block border border-emerald-300/30 rounded-lg p-4"><input type="checkbox" checked={report.listed} onChange={e => { setReport({ ...report, listed: e.target.checked }); setDirty(true); }} /> List this project for approved researchers to discover.<span className="block text-white/60 mt-2">Shares the project title, research question and collaborator needs. Full plans stay private to the accepted team. Clear this checkbox and save to unlist.</span></label>
          {report.can_edit && <button className="bg-emerald-300 text-black rounded-lg px-6 py-3 disabled:opacity-40" disabled={!dirty}>Save plan</button>}
        </fieldset>
      </form>
      <SiteFeasibility key={id} studyId={id} planRevision={report.revision} planDirty={dirty} />
      <WorkLedger key={'ledger-' + id} studyId={id} />
      <h3 className="text-2xl mt-8 mb-3">Team discussion</h3>
      <form onSubmit={e => { e.preventDefault(); mutate(`/projects/${id}/discussion`, { message: comment }, async () => { setComment(''); setComments(await request(`/projects/${id}/discussion`)); }); }}><label>Suggest a change or share an update<textarea className={input} required minLength={10} maxLength={1000} value={comment} onChange={e => setComment(e.target.value)} /></label><button className={button} disabled={busy}>Post update</button></form>
      {!comments.length && <p className="my-4 text-white/60">No updates yet.</p>}{comments.map(c => <div key={c.id} className="border-b border-white/20 py-4"><strong>{c.name}</strong><p className="whitespace-pre-wrap break-words">{c.message}</p></div>)}
      {report.can_edit && <><h3 className="text-2xl mt-8 mb-3">Collaboration requests</h3><p className="text-white/60">Inviting creates an in-app invitation. The researcher must accept before seeing the plan. No email is sent.</p>{!interests.length && <p className="my-3">No requests yet.</p>}{interests.map(r => <div key={r.id} className="border border-white/20 rounded-lg p-4 my-3"><h4>{r.name} · {r.organization || 'Affiliation not supplied'}</h4><p className="my-3">{r.message}</p><p>{r.status}</p>{r.status === 'pending' && <div className="flex gap-3 mt-3">{['invite', 'decline'].map(decision => <button key={decision} disabled={busy} className={button} onClick={() => mutate(`/projects/${id}/interests/${r.id}`, { decision }, async () => setInterests(await request(`/projects/${id}/interests`)))}>{decision === 'invite' ? 'Invite to team' : 'Decline'}</button>)}</div>}</div>)}</>}
    </section>}
    <section className="border-t border-white/20 pt-8">
      <h2 className="text-3xl mb-3">Find a project to contribute to</h2><p className="text-white/60 mb-4">Only owner-listed projects appear. Listings describe research plans, not validated findings or available datasets.</p>
      <form className="flex gap-3 items-end" onSubmit={e => { e.preventDefault(); discover(0); }}><label className="flex-1">Search project titles<input className={input} maxLength={100} value={query} onChange={e => setQuery(e.target.value)} /></label><button className={button} disabled={busy}>Search</button></form>
      {!directory.items.length && <p className="my-5">No listed projects found. You can create a plan and list it when ready.</p>}
      {directory.items.map(p => <section key={p.id} className="border border-white/20 rounded-lg p-5 my-4"><h3 className="text-xl">{p.name}</h3><p className="my-3">{p.question}</p><p>Seeking: {p.seeking}</p>{p.mine || isAdmin ? <p className="text-emerald-300 mt-3">{p.mine ? 'Your listing' : 'Invitation requests are for approved researcher accounts'}</p> : <form className="mt-4" onSubmit={e => { e.preventDefault(); mutate(`/opportunities/${p.id}/interest`, { message: interestMessages[p.id] || '' }, r => setNotice(r.message)); }}><label>How would you contribute?<textarea className={input} required minLength={10} maxLength={1000} value={interestMessages[p.id] || ''} onChange={e => setInterestMessages({ ...interestMessages, [p.id]: e.target.value })} /></label><button className={button} disabled={busy}>Request an invitation</button></form>}</section>)}
      <div className="flex gap-3 mt-4"><button className={button} disabled={busy || page === 0} onClick={() => discover(page - 1)}>Previous</button><span>Page {page + 1}</span><button className={button} disabled={busy || !directory.has_more} onClick={() => discover(page + 1)}>Next</button></div>
    </section>
  </main>;
}
