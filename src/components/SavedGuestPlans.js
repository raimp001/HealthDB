import React, { useEffect, useState } from 'react';
import { MAX_SAVED_PLANS, SAVED_PLANS_KEY, readSavedPlans, removePlanCopy, savePlanCopy } from '../lib/savedGuestPlans';

const button = 'border border-white/30 rounded px-4 py-2 hover:border-emerald-300 focus-visible:outline focus-visible:outline-emerald-300';

export default function SavedGuestPlans({ draft, onOpen }) {
  const [plans, setPlans] = useState([]);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [pending, setPending] = useState(null);
  const [removing, setRemoving] = useState(null);
  useEffect(() => {
    function refresh(event) {
      if (event && event.key !== SAVED_PLANS_KEY && event.key !== null) return;
      try { setPlans(readSavedPlans()); setError(''); }
      catch { setError('Saved copies could not be read. Download your current draft to keep it. Existing saved copies have not been changed.'); }
    }
    refresh();
    window.addEventListener('storage', refresh);
    return () => window.removeEventListener('storage', refresh);
  }, []);
  function save() {
    try {
      setPlans(savePlanCopy(draft)); setError('');
      setMessage('Copy saved on this device. You can reopen it after closing this tab. Later edits need a new saved copy.');
    } catch (cause) {
      setError(cause.message.startsWith('You have 10') ? cause.message : 'Could not save a copy on this device. Download or copy your draft instead. Existing saved copies have not been changed.');
      setMessage('');
    }
  }
  function remove(id) {
    try {
      setPlans(removePlanCopy(id)); setRemoving(null); setError('');
      if (pending?.id === id) setPending(null);
      setMessage('Saved copy removed from this device. Your open plan has not changed.');
    } catch { setError('Could not remove this saved copy. Please try again.'); }
  }
  return <section className="border border-emerald-300/30 bg-emerald-300/5 rounded-xl p-5 space-y-4" aria-labelledby="saved-plans-title">
    <h2 id="saved-plans-title" className="text-2xl">Return to your work</h2>
    <p>Save a named copy to reopen in this browser after closing the tab. Copies include your variables, mapping reviews, and contribution history.</p>
    <p className="text-sm text-white/70">Optional device storage · Anyone using this browser profile can open these copies. Use fictional planning content only, never patient information. Copies are not shared or backed up; clearing browser data removes them.</p>
    <button type="button" onClick={save} disabled={plans.length >= MAX_SAVED_PLANS} className={`${button} bg-emerald-300 text-black disabled:opacity-40`}>Save a copy on this device</button>
    <p className="text-sm text-white/70">Saved copies do not update automatically. Save a new copy after making changes, or download a draft for a separate backup.</p>
    <p role="status">{message}</p>
    {error && <p role="alert" className="text-red-300">{error}</p>}
    <h3 className="font-semibold">Saved copies ({plans.length}/{MAX_SAVED_PLANS})</h3>
    {!plans.length && !error && <p>No saved copies yet. Your current plan is still kept in this tab.</p>}
    {plans.length >= MAX_SAVED_PLANS && <p>All 10 spaces are in use. Download and remove an older copy to save another.</p>}
    <ul className="space-y-3">{plans.map(copy => <li key={copy.id} className="border border-white/20 rounded-lg p-4 space-y-2">
      <h4 className="font-semibold break-words">{copy.plan.title || 'Untitled study'}</h4>
      <p className="text-sm text-white/70"><time dateTime={copy.savedAt}>{new Date(copy.savedAt).toLocaleString()}</time> · {copy.plan.variables.length} variables · {copy.plan.reviewHistory.length} reviews · {copy.plan.events.length} contributions</p>
      <div className="flex flex-wrap gap-3"><button type="button" className={button} aria-label={`Preview saved copy: ${copy.plan.title || 'Untitled study'}`} onClick={() => { setPending(copy); setRemoving(null); }}>Preview and reopen</button><button type="button" className={button} aria-label={`Remove saved copy: ${copy.plan.title || 'Untitled study'}`} onClick={() => setRemoving(copy.id)}>Remove copy</button></div>
      {removing === copy.id && <div className="space-y-2"><p>Remove this saved copy? Keep a downloaded backup if you need it. Your open plan will stay unchanged.</p><button type="button" className={button} onClick={() => remove(copy.id)}>Confirm removal</button> <button type="button" className={button} onClick={() => setRemoving(null)}>Keep copy</button></div>}
    </li>)}</ul>
    {pending && <div className="border border-emerald-300 rounded-lg p-4 space-y-3" role="region" aria-label="Saved copy preview">
      <h3 className="font-semibold">Reopen {pending.plan.title || 'Untitled study'}?</h3>
      <p className="break-words">{pending.plan.question || 'No research question yet.'}</p>
      <p>{pending.plan.variables.length} variables · {pending.plan.reviewHistory.length} review snapshots · {pending.plan.events.length} contributions</p>
      <p>This replaces your open plan. Save or download your current work first if you want to keep both. History and reviewer roles remain unverified.</p>
      <button type="button" className={button} onClick={() => { onOpen(pending.plan); setPending(null); setMessage('Saved copy reopened. Later edits need a new saved copy.'); }}>Replace open plan with saved copy</button> <button type="button" className={button} onClick={() => setPending(null)}>Cancel reopening</button>
    </div>}
  </section>;
}
