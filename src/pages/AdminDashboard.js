import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { API_URL, apiRequest } from '../lib/api';

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [offset, setOffset] = useState(0);
  const [audit, setAudit] = useState(null);
  const [dateState, setDateState] = useState(null);
  const [dateResult, setDateResult] = useState(null);
  const [confirmDates, setConfirmDates] = useState(false);
  const headers = () => ({ Authorization: `Bearer ${sessionStorage.getItem('token')}`, 'Content-Type': 'application/json' });
  const load = async () => {
    setBusy(true); setError(''); setData(null);
    try { setData(await apiRequest(`/api/admin/overview?offset=${offset}`, { headers: headers() })); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  // Each page change starts a fresh bounded inbox request.
  useEffect(() => { load(); }, [offset]);
  const update = async (path, body) => {
    setBusy(true); setError('');
    try { await apiRequest(path, { method: 'POST', headers: headers(), body: JSON.stringify(body) }); await load(); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const runAudit = async () => {
    setBusy(true); setError(''); setAudit(null);
    try {
      const response = await fetch(`${API_URL}/api/health/invariants`, { headers: headers(), signal: AbortSignal.timeout(20000) });
      const report = await response.json();
      if (![200, 503].includes(response.status) || !Array.isArray(report.findings)) throw new Error('Unable to run operational checks. Try again.');
      setAudit(report);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  // The date migration is irreversible, so it is read first, confirmed
  // separately, and never a single click from the page loading.
  const loadDateState = async () => {
    setBusy(true); setError(''); setDateResult(null); setConfirmDates(false);
    try { setDateState(await apiRequest('/api/admin/maintenance/date-truncation', { headers: headers() })); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const runDateTruncation = async () => {
    setBusy(true); setError('');
    try {
      setDateResult(await apiRequest('/api/admin/maintenance/date-truncation', {
        method: 'POST', headers: headers(),
        body: JSON.stringify({ confirm: 'truncate-dates-permanently' }),
      }));
      setConfirmDates(false);
      setDateState(await apiRequest('/api/admin/maintenance/date-truncation', { headers: headers() }));
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const button = 'border border-white/40 rounded px-4 py-2 disabled:opacity-40';
  return <main className="max-w-6xl mx-auto px-6 py-16 text-white">
    <h1 className="text-4xl mb-4">Admin workspace</h1>
    <Link className="inline-block text-emerald-300 underline mb-4" to="/projects">Plan research and discover projects</Link>
    <p className="text-white/70 mb-6">Review incoming requests, confirm and approve researchers for testing, and check platform readiness.</p>
    <div className="flex gap-4 mb-6"><button className={button} disabled={busy} onClick={load}>Refresh inbox</button><Link className={button} to="/research-readiness">Review study evidence</Link></div>
    {error && <p role="alert" className="text-red-300 mb-6">{error}</p>}
    {busy && <p role="status">Working…</p>}
    {data && <>
      <h2 className="text-2xl mt-8 mb-3">Incoming requests</h2>
      <p className="text-white/70 mb-4">Requests appear here. Status changes do not send email or create accounts. Research access is approved separately below.</p>
      {!data.contacts.length && <p>No requests on this page.</p>}
      {data.contacts.map(c => <section className="border border-white/20 rounded p-5 mb-3 break-words" key={c.id}>
        <h3 className="text-xl">{c.name} — {c.email}</h3><p>{c.organization || 'No organization supplied'} · {c.interest || 'General request'}</p>
        <p className="whitespace-pre-wrap my-3">{c.message}</p>
        <label>Request status <select className="bg-black border p-2" disabled={busy} value={c.status} onChange={e => update(`/api/admin/contacts/${c.id}/status`, { status: e.target.value })}>
          <option value="new">New</option><option value="contacted">Contacted</option><option value="closed">Closed</option>
        </select></label>
      </section>)}
      <h2 className="text-2xl mt-8 mb-3">Researcher access</h2>
      <p className="text-white/70 mb-4">Two decisions, kept separate on purpose. First confirm who the applicant is and where they work. Only then approve research access. Approval does not authorize live patient data, licensing, or EHR access.</p>
      {!data.researchers.length && <p>No researcher accounts on this page.</p>}
      {data.researchers.map(u => <section className="border border-white/20 rounded p-5 mb-3" key={u.id}>
        <h3 className="text-xl break-words">{u.name} — {u.email}</h3><p>{u.organization || 'No organization supplied'}</p>
        <p className="my-3">{u.approved ? 'Approved' : 'Pending approval'} · {u.verified ? 'Identity confirmed' : 'Identity not confirmed'} · {u.active ? 'Active account' : 'Inactive account'}</p>
        {!u.verified && <p className="text-white/50 text-sm mb-3">Establish who this person is and where they work before confirming — a call to the department, an institutional directory, a colleague who knows them. There is no email link; controlling a mailbox does not establish affiliation.</p>}
        <div className="flex flex-wrap gap-3">
          <button className={button} disabled={busy || (u.verified && u.approved)} onClick={() => update(`/api/admin/researchers/${u.id}/decision`, { decision: u.verified ? 'withdraw-identity' : 'confirm-identity' })}>{u.verified ? 'Withdraw identity confirmation' : 'Confirm identity and affiliation'}</button>
          <button className={button} disabled={busy || (!u.approved && (!u.verified || !u.active))} onClick={() => update(`/api/admin/researchers/${u.id}/decision`, { decision: u.approved ? 'revoke' : 'approve' })}>{u.approved ? 'Revoke research access' : 'Approve for testing'}</button>
        </div>
      </section>)}
      <div className="flex gap-4 my-6"><button className={button} disabled={busy || offset === 0} onClick={() => setOffset(offset - 50)}>Previous</button><span>Page {offset / 50 + 1}</span><button className={button} disabled={busy || !data.has_more} onClick={() => setOffset(offset + 50)}>Next</button></div>
      <h2 className="text-2xl mt-8 mb-3">Availability and setup</h2>
      <p className="text-white/70 mb-4">These are server configuration states, not proof of successful end-to-end operation. Live integrations and commercial licensing still require institutional setup.</p>
      <ul className="space-y-2">{data.capabilities.map(c => <li key={c.name}>{c.name}: <strong>{c.enabled ? 'Enabled in configuration' : 'Unavailable / not enabled'}</strong></li>)}</ul>
    </>}
    <h2 className="text-2xl mt-8 mb-3">Operational checks</h2>
    <p className="text-white/70 mb-4">Run read-only database and privacy safeguards checks. These checks do not certify regulatory compliance.</p>
    <button className={button} disabled={busy} onClick={runAudit}>Run checks</button>
    {audit && <section className="mt-4"><p>{audit.summary}</p><ul className="space-y-3 mt-3">{audit.findings.map(f => <li key={f.name}>{f.passed ? 'Pass' : 'Needs attention'} — {f.summary} ({f.severity})</li>)}</ul></section>}

    <h2 className="text-2xl mt-10 mb-3">Stored date precision</h2>
    <p className="text-white/70 mb-4">
      Safe Harbor permits no date element more precise than a year. New records already store a
      year only. Records created before that change may still hold a month and a day; this
      removes them permanently.
    </p>
    <button className={button} disabled={busy} onClick={loadDateState}>Check stored dates</button>

    {dateState && <section className="mt-4 border border-white/20 rounded p-5">
      {dateState.already_applied ? (
        <p>Already applied. No stored clinical date carries a month or a day.</p>
      ) : (<>
        <p className="mb-2">
          <strong>{dateState.rows_with_month_and_day}</strong> record(s) still hold a month and a day.
        </p>
        <p className="text-amber-300/80 mb-4">
          This cannot be undone. The month and day are destroyed, not archived. Restoring them
          would need a backup taken beforehand.
        </p>
        {!confirmDates ? (
          <button className={button} disabled={busy} onClick={() => setConfirmDates(true)}>
            Truncate these dates to the year
          </button>
        ) : (
          <div className="flex flex-wrap gap-3 items-center">
            <span>Permanently destroy month and day on {dateState.rows_with_month_and_day} record(s)?</span>
            <button className={button} disabled={busy} onClick={runDateTruncation}>Yes, truncate permanently</button>
            <button className={button} disabled={busy} onClick={() => setConfirmDates(false)}>Cancel</button>
          </div>
        )}
      </>)}
    </section>}
    {dateResult && <p role="status" className="mt-3">
      {dateResult.applied
        ? `Truncated ${dateResult.rows_truncated} record(s). ${dateResult.rows_remaining} remain.`
        : dateResult.reason}
    </p>}
  </main>;
}
