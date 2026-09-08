import React, { useState } from 'react';
import { apiRequest } from '../lib/api';

export default function EvidenceWithdrawal({ item, canWithdraw, onSaved, disabled }) {
  const [action, setAction] = useState('');
  const [reference, setReference] = useState('');
  const [reason, setReason] = useState('');
  const [futureUse, setFutureUse] = useState('');
  const [recipients, setRecipients] = useState('');
  const [retained, setRetained] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const submit = async e => {
    e.preventDefault(); setBusy(true); setError('');
    const body = { reference, reason };
    if (action === 'disposition') Object.assign(body, { future_use: futureUse, recipients, retained_data: retained });
    try {
      await apiRequest(`/api/research-evidence/${encodeURIComponent(item.id)}/${action}`, {
        method: 'POST', headers: { Authorization: `Bearer ${sessionStorage.getItem('token')}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      setAction(''); setReference(''); setReason('');
      await onSaved();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };
  const input = 'block bg-black border p-2 w-full mt-1';
  return <div className="mt-4">
    {item.status === 'withdrawn' && <p className="text-amber-300">Open withdrawal: this scope is blocked until an independent administrator records the external disposition.</p>}
    {!action && <>
      {canWithdraw && ['submitted', 'verified', 'revoked'].includes(item.status) && <button disabled={disabled} className="border p-2" onClick={() => setAction('withdraw')}>Withdraw evidence and open follow-up</button>}
      {item.can_close_withdrawal && <button disabled={disabled} className="border p-2" onClick={() => setAction('disposition')}>Record reviewed disposition</button>}
    </>}
    {action && <form onSubmit={submit} className="border border-amber-300/40 p-4 grid gap-3 mt-3">
      <p>{action === 'withdraw' ? 'This immediately removes this evidence from readiness and blocks its scope. A replacement alone cannot close the follow-up.' : 'Record actions verified in your institution’s approved system. Closing follow-up does not reactivate this evidence.'}</p>
      <p className="text-sm text-white/70">Administrative metadata only. No patient identifiers, patient-level document references, signed links or document contents. This form does not stop integrations, notify recipients or delete data.</p>
      <fieldset disabled={busy || disabled} className="grid gap-3">
        <label>External administrative reference ID<input required pattern="[A-Za-z0-9_.:/-]+" maxLength={120} className={input} value={reference} onChange={e => setReference(e.target.value)} /></label>
        <label>Reason and scope-level disposition rationale<textarea required minLength={10} maxLength={1000} className={input} value={reason} onChange={e => setReason(e.target.value)} /></label>
        {action === 'disposition' && <>
          <label>Future use<select required className={input} value={futureUse} onChange={e => setFutureUse(e.target.value)}><option value="">Select verified outcome</option><option value="stopped">Stopped externally</option><option value="not_applicable">Not applicable — explain in rationale</option></select></label>
          <label>Recipient notification<select required className={input} value={recipients} onChange={e => setRecipients(e.target.value)}><option value="">Select verified outcome</option><option value="notified">Recipients notified externally</option><option value="not_applicable">Not applicable — explain in rationale</option></select></label>
          <label>Previously held data<select required className={input} value={retained} onChange={e => setRetained(e.target.value)}><option value="">Select reviewed disposition</option><option value="removed">Removed externally</option><option value="retained_under_reviewed_policy">Retained under externally reviewed policy</option><option value="not_applicable">No applicable data — explain in rationale</option></select></label>
        </>}
        <div className="flex gap-3"><button className="border p-2" type="submit">{busy ? 'Saving…' : 'Save administrative record'}</button><button type="button" className="border p-2" onClick={() => { setAction(''); setError(''); }}>Cancel</button></div>
      </fieldset>
    </form>}
    {error && <p role="alert" className="text-red-300">{error}</p>}
  </div>;
}
