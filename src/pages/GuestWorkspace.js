import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import GuestMappingReview, { fictionalSites } from '../components/GuestMappingReview';
import SavedGuestPlans from '../components/SavedGuestPlans';
import { GUEST_DRAFT_KEY, parseGuestDraft, readGuestDraft } from '../lib/guestDraft';

const initialVariables = [
  { id: 1, name: 'Treatment class', a: 'available', b: 'unknown', c: 'available' },
  { id: 2, name: 'Response category', a: 'derivable', b: 'available', c: 'unavailable' },
];
const options = ['unknown', 'available', 'derivable', 'unavailable'];
const inputClass = 'w-full bg-black border border-white/30 rounded p-3';

export default function GuestWorkspace() {
  const [restored] = useState(readGuestDraft);
  const [title, setTitle] = useState(restored.plan?.title ?? 'Synthetic multi-site outcomes study');
  const [question, setQuestion] = useState(restored.plan?.question ?? 'How do response patterns differ across treatment classes?');
  const [variables, setVariables] = useState(restored.plan?.variables ?? initialVariables);
  const [variable, setVariable] = useState('');
  const [work, setWork] = useState('');
  const [events, setEvents] = useState(restored.plan?.events ?? []);
  const [notice, setNotice] = useState(restored.message ?? '');
  const [showDraft, setShowDraft] = useState(false);
  const [reviews, setReviews] = useState(restored.plan?.reviews ?? {});
  const [reviewHistory, setReviewHistory] = useState(restored.plan?.reviewHistory ?? []);
  const [saveStatus, setSaveStatus] = useState('');
  const [importText, setImportText] = useState('');
  const [importError, setImportError] = useState('');
  const [pendingImport, setPendingImport] = useState(null);
  const counts = variables.flatMap(v => fictionalSites.map(site => v[site])).reduce((total, value) => ({ ...total, [value]: total[value] + 1 }), { unknown: 0, available: 0, derivable: 0, unavailable: 0 });
  const activeReviews = Object.fromEntries(Object.entries(reviews).filter(([key]) => variables.some(v => key.startsWith(`${v.id}:`))));
  const draft = JSON.stringify({ schema_version: 1, mode: 'guest_demo', synthetic_only: true, title, question, variables, reviews: activeReviews, reviewHistory, events }, null, 2);
  useEffect(() => {
    try {
      parseGuestDraft(draft);
      sessionStorage.setItem(GUEST_DRAFT_KEY, draft);
      setSaveStatus('Autosaved in this tab. Save a device copy or download before closing the tab.');
    } catch {
      setSaveStatus('Could not save the latest changes in this tab. Download or copy your draft before leaving.');
    }
  }, [draft]);
  function changeStudy(setter, value) {
    setter(value);
    setReviews(items => Object.fromEntries(Object.entries(items).map(([key, item]) => [key, { ...item, status: 'draft' }])));
  }
  function inspectImport() {
    try { setPendingImport(parseGuestDraft(importText)); setImportError(''); }
    catch (error) { setPendingImport(null); setImportError(error.message); }
  }
  function restorePlan(plan) {
    setTitle(plan.title); setQuestion(plan.question); setVariables(plan.variables);
    setReviews(plan.reviews); setReviewHistory(plan.reviewHistory); setEvents(plan.events);
    setPendingImport(null); setImportText(''); setImportError(''); setVariable(''); setWork('');
    setNotice('Draft reopened. Imported history is unverified; nothing was submitted to HealthDB.');
  }
  function changeReview(key, review, label) {
    if (label && reviewHistory.length >= 1000) { setNotice('This demo supports up to 1,000 review snapshots. Download a copy of your work.'); return; }
    setReviews(items => ({ ...items, [key]: review }));
    if (label) {
      const [variableId, site] = key.split(':');
      const availability = variables.find(v => String(v.id) === variableId)?.[site];
      setReviewHistory(items => [...items, { sequence: items.length + 1, key, label, ...review, availability, title, question, at: new Date().toISOString() }]);
      setNotice(`Demo review recorded for ${label}. No institutional approval was created.`);
    }
  }
  function map(id, site, value) {
    setVariables(items => items.map(item => item.id === id ? { ...item, [site]: value } : item));
    const key = `${id}:${site}`;
    setReviews(items => items[key] ? { ...items, [key]: { ...items[key], status: 'draft' } } : items);
  }
  function addVariable(e) {
    e.preventDefault();
    const name = variable.trim();
    if (!name) return;
    if (variables.length >= 100) { setNotice('This demo supports up to 100 variables.'); return; }
    if (variables.some(v => v.name.toLowerCase() === name.toLowerCase())) {
      setNotice('That variable is already in the dictionary.'); return;
    }
    const usedIds = [...variables.map(v => v.id), ...Object.keys(reviews).map(key => Number(key.split(':')[0])), ...reviewHistory.map(v => Number(v.key.split(':')[0]))];
    const id = Math.max(0, ...usedIds) + 1;
    if (!Number.isSafeInteger(id)) { setNotice('Cannot add another variable to this draft.'); return; }
    setVariables(items => [...items, { id, name, a: 'unknown', b: 'unknown', c: 'unknown' }]);
    setVariable(''); setNotice('Variable added. Declare availability for each fictional site.');
  }
  function addWork(e) {
    e.preventDefault();
    if (!work.trim()) return;
    if (events.length >= 1000) { setNotice('This demo supports up to 1,000 contributions. Download a copy of your work.'); return; }
    setEvents(items => [...items, { sequence: items.length + 1, action: 'Submitted', description: work.trim(), at: new Date().toISOString() }]);
    setWork(''); setNotice('Demo contribution recorded. Independent review is available in the private workspace.');
  }
  function download() {
    const blob = new Blob([draft], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'healthdb-guest-plan.json';
    document.body.appendChild(anchor); anchor.click(); anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    setShowDraft(true);
    setNotice('Download requested. If your browser blocks it, select and copy the draft below. Nothing has been submitted to HealthDB.');
  }
  return <div className="max-w-5xl mx-auto px-6 py-16 text-white space-y-10">
    <header><p className="text-emerald-300">Guest workspace · No sign-in required</p>
      <h1 className="text-4xl my-4">Turn a research question into a shared plan</h1>
      <p className="text-xl mb-4">Find data gaps before a study starts. Define the variables, compare three fictional sites, and capture the work needed to move forward.</p>
      <p className="text-white/70">Explore the workflow with fictional sites. Changes are kept in this tab. Save a copy on this device to return later, or download a draft to reopen elsewhere. Do not enter patient information.</p>
      <p role="status" className="text-emerald-300 text-sm">{saveStatus}</p>
      <p className="text-white/60 mt-3">This is a temporary demo, not a shared study or an auditable institutional record. No live records, invitations, approvals, or payments are created.</p>
    </header>
    <SavedGuestPlans draft={draft} onOpen={restorePlan} />
    <nav aria-label="Study planning steps" className="flex flex-wrap gap-3">{[['guest-plan', '1. Define your question'], ['guest-mapping', '2. Find data gaps'], ['guest-ledger', '3. Recognize the work']].map(([id, label]) => <a key={id} href={`#${id}`} className="rounded-full border border-white/30 px-4 py-2 hover:border-emerald-300 focus-visible:outline focus-visible:outline-emerald-300">{label}</a>)}</nav>
    <section className="space-y-4" aria-labelledby="guest-plan"><h2 id="guest-plan" className="text-2xl">1. Define the study</h2>
      <label className="block">Study title<input className={inputClass} maxLength={160} value={title} onChange={e => changeStudy(setTitle, e.target.value)} /></label>
      <label className="block">Research question<textarea className={inputClass} maxLength={2000} value={question} onChange={e => changeStudy(setQuestion, e.target.value)} /></label>
      <p className="text-sm text-white/70">Changing the study title or question reopens mapping reviews. Earlier snapshots remain in the history.</p>
    </section>
    <section className="space-y-4" aria-labelledby="guest-mapping"><h2 id="guest-mapping" className="text-2xl">2. Map variable availability</h2>
      <p className="text-white/70">These declarations are fictional. “Unknown” means availability has not been assessed; “derivable” means a transformation would need validation.</p>
      <div className="rounded-xl border border-emerald-300/30 bg-emerald-300/5 p-5 space-y-3" aria-label="Availability summary">
        <h3 className="text-lg">Your planning snapshot</h3>
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4">{[['available', 'Available'], ['unknown', 'Need assessment'], ['derivable', 'Need validation'], ['unavailable', 'Unavailable']].map(([key, label]) => <div key={key}><dt className="text-sm text-white/70">{label}</dt><dd className="text-2xl font-semibold">{counts[key]}</dd></div>)}</dl>
        <p className="text-sm text-white/70">Counts describe variable–site declarations, not patients or verified data.</p>
        <p>{!variables.length ? 'Add a variable to begin assessing availability.' : counts.unknown ? 'Next: assess the unknown declarations with each site.' : counts.unavailable ? 'Next: discuss alternatives for unavailable variables before finalizing the study.' : counts.derivable ? 'Next: agree and validate the transformations for derivable variables.' : 'All fictional declarations are available. Real study feasibility still requires institutional validation.'}</p>
      </div>
      <div className="overflow-x-auto"><table className="w-full text-left"><caption className="sr-only">Variable availability at fictional sites A, B and C</caption><thead><tr><th scope="col" className="p-2">Variable</th>{fictionalSites.map(site => <th key={site} scope="col" className="p-2">Fictional site {site.toUpperCase()}</th>)}</tr></thead>
        <tbody>{variables.map(v => <tr key={v.id}><th scope="row" className="p-2 break-words">{v.name}<button type="button" aria-label={`Remove ${v.name}`} onClick={() => { setVariables(items => items.filter(item => item.id !== v.id)); setNotice(`${v.name} removed from this draft.`); }} className="block text-sm font-normal text-white/70 underline py-2">Remove</button></th>{fictionalSites.map(site => <td key={site} className="p-2"><select className={inputClass} aria-label={`${v.name}: fictional site ${site.toUpperCase()}`} value={v[site]} onChange={e => map(v.id, site, e.target.value)}>{options.map(o => <option key={o}>{o}</option>)}</select></td>)}</tr>)}</tbody></table></div>
      <form onSubmit={addVariable} className="flex flex-wrap gap-3 items-end"><label className="flex-1">New variable<input className={inputClass} maxLength={100} required value={variable} onChange={e => setVariable(e.target.value)} /></label><button className="border border-emerald-300 rounded px-4 py-3">Add variable</button></form>
      <Link to="/demo" className="inline-block text-emerald-300 underline">Run a synthetic cohort query →</Link>
    </section>
    <GuestMappingReview variables={variables} reviews={reviews} onChange={changeReview} />
    {reviewHistory.length > 0 && <details className="border border-white/20 rounded-xl p-4"><summary>Demo review history ({reviewHistory.length})</summary><ol className="space-y-2 mt-3">{reviewHistory.map(entry => <li key={entry.sequence}>#{entry.sequence} · {entry.label} · {entry.owner} · {entry.nextAction}<time className="block text-sm text-white/70" dateTime={entry.at}>{entry.at}</time></li>)}</ol><p className="text-sm text-white/70 mt-3">Past snapshots stay in the draft even if a variable changes or is removed. This local history has no verified reviewer identity.</p></details>}
    <section className="space-y-4" aria-labelledby="guest-ledger"><h2 id="guest-ledger" className="text-2xl">3. Try the contribution ledger</h2>
      <p className="text-white/70">Record example work such as defining variables or reviewing a protocol. Entries here have no verified contributor, approval, or financial value.</p>
      <form onSubmit={addWork} className="space-y-3"><label className="block">Example contribution<input className={inputClass} maxLength={300} required value={work} onChange={e => setWork(e.target.value)} /></label><button className="border border-emerald-300 rounded px-4 py-3">Record demo contribution</button></form>
      {events.length ? <ol className="space-y-3">{events.map(e => <li key={e.sequence} className="border border-white/20 rounded p-3 break-words">#{e.sequence} · {e.action} · {e.description}<time className="block text-sm text-white/60" dateTime={e.at}>{e.at}</time></li>)}</ol> : <p className="text-white/60">No demo contributions yet.</p>}
    </section>
    <p role="status" aria-live="polite">{notice}</p>
    <section className="border-t border-white/20 pt-6 space-y-4" aria-labelledby="guest-next"><h2 id="guest-next" className="text-2xl">Keep your plan. Take the next step.</h2><p className="text-white/70">Keep a copy before closing this tab. To discuss a supported institutional pilot, contact the team with your study idea and data needs.</p>
    <div className="flex flex-wrap gap-5 items-center"><button onClick={download} className="bg-emerald-300 text-black rounded px-5 py-3">Download draft</button><button aria-expanded={showDraft} aria-controls="guest-draft" onClick={() => setShowDraft(value => !value)} className="border border-white/30 rounded px-5 py-3">{showDraft ? 'Hide draft' : 'Preview draft'}</button><Link to="/contact" className="text-emerald-300 underline">Discuss a research pilot →</Link></div>
    {showDraft && <label id="guest-draft" className="block">Draft JSON — select and copy<textarea readOnly value={draft} rows={12} className={`${inputClass} mt-2 font-mono text-sm`} /></label>}
    <details className="border border-white/20 rounded-xl p-4"><summary className="cursor-pointer">Reopen an exported draft</summary>
      <p className="text-white/70 my-3">Paste the JSON from a guest draft. Only synthetic planning content is supported. This stays in your browser; it does not verify data, identities, or approvals.</p>
      <label className="block">Guest draft JSON<textarea id="guest-import" value={importText} maxLength={1000000} rows={6} className={`${inputClass} font-mono text-sm`} onChange={e => { setImportText(e.target.value); setPendingImport(null); setImportError(''); }} /></label>
      <button type="button" disabled={!importText.trim()} onClick={inspectImport} className="border border-emerald-300 rounded px-4 py-3 mt-3 disabled:opacity-40">Check draft</button>
      {importError && <p role="alert" className="text-red-300 mt-3">{importError}</p>}
      {pendingImport && <div className="space-y-3 mt-4"><p>Ready to reopen: {pendingImport.title || 'Untitled study'} · {pendingImport.variables.length} variables · {pendingImport.reviewHistory.length} review snapshots · {pendingImport.events.length} contributions.</p><p>This replaces your current plan. Download the current draft first if you want to keep both.</p><button type="button" onClick={() => restorePlan(pendingImport)} className="bg-emerald-300 text-black rounded px-4 py-3">Replace current plan with this draft</button></div>}
    </details>
    <Link to="/projects" className="inline-block text-emerald-300 underline">Open private workspace (sign-in required)</Link></section>
  </div>;
}
