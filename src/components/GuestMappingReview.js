import React from 'react';

export const fictionalSites = ['a', 'b', 'c'];
const field = 'w-full bg-black border border-white/30 rounded p-3';
export default function GuestMappingReview({ variables, reviews, onChange }) {
  const rows = variables.flatMap(variable => fictionalSites.map(site => ({ variable, site, key: `${variable.id}:${site}` })));
  const pending = rows.filter(row => reviews[row.key]?.status !== 'reviewed');
  return <section className="space-y-4" aria-labelledby="mapping-review">
    <h2 id="mapping-review" className="text-2xl">Review mappings and assign next actions</h2>
    <p className="text-white/70">Availability alone does not establish feasibility. Describe how each fictional site's field matches the study variable, then record a demo review. Changing availability resets that review.</p>
    <div className="grid sm:grid-cols-3 gap-4">{fictionalSites.map(site => {
      const gaps = variables.filter(v => v[site] !== 'available').length;
      const outstanding = pending.filter(row => row.site === site).length;
      return <article key={site} className="border border-white/20 rounded-xl p-4"><h3 className="font-semibold">Fictional site {site.toUpperCase()}</h3><p>{variables.length ? `${gaps} availability gaps · ${outstanding} mappings awaiting review` : 'No variables defined'}</p><p className="text-sm text-emerald-300 mt-2">{!variables.length ? 'Define required variables first' : gaps || outstanding ? 'Further assessment needed' : 'Demo checklist complete — real feasibility unvalidated'}</p></article>;
    })}</div>
    <p className="text-sm text-white/70">All variables in this demo are treated as required. Assignments are local examples; no one is notified. Review labels are not institutional approval.</p>
    {rows.map(({ variable, site, key }) => {
      const review = reviews[key] || { mapping: '', owner: '', nextAction: '', status: 'draft' };
      const label = `${variable.name} — site ${site.toUpperCase()}`;
      return <details key={key} className="border border-white/20 rounded-xl p-4">
        <summary className="cursor-pointer py-2">{label} · {variable[site]} · {review.status === 'reviewed' ? 'Demo reviewed' : 'Needs review'}</summary>
        <div className="grid sm:grid-cols-2 gap-4 mt-4">
          <label className="sm:col-span-2">Mapping notes: {label}<textarea className={field} maxLength={1000} value={review.mapping} placeholder="Example: local response_code → study response category; document categories, missing values, and any transformation." onChange={e => onChange(key, { ...review, mapping: e.target.value, status: 'draft' })} /></label>
          <label>Action owner: {label}<select className={field} value={review.owner} onChange={e => onChange(key, { ...review, owner: e.target.value, status: 'draft' })}><option value="">Assign a fictional role</option><option>Site data steward</option><option>Study coordinator</option><option>Methods reviewer</option></select></label>
          <label>Next action: {label}<input className={field} maxLength={300} value={review.nextAction} placeholder="Example: validate category definitions" onChange={e => onChange(key, { ...review, nextAction: e.target.value, status: 'draft' })} /></label>
          <button type="button" disabled={!review.mapping.trim() || !review.owner || !review.nextAction.trim() || review.status === 'reviewed'} onClick={() => onChange(key, { ...review, status: 'reviewed' }, label)} className="border border-emerald-300 rounded px-4 py-3 disabled:opacity-40">Record demo review: {label}</button>
        </div>
      </details>;
    })}
  </section>;
}
