import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { API_URL, apiFetch } from '../lib/api';

export default function Demo() {
  const [diagnosis, setDiagnosis] = useState('');
  const [age, setAge] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const criteria = { cancer_types: diagnosis ? [diagnosis] : [], age_min: age === '' ? null : Number(age) };
  const change = (setter) => (event) => { setter(event.target.value); setResult(null); setError(''); };
  async function run(event) {
    event.preventDefault(); setBusy(true); setError(''); setResult(null);
    try {
      const response = await apiFetch(`${API_URL}/api/demo/cohort/build`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(criteria),
      });
      setResult(await response.json());
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  return <div className="max-w-5xl mx-auto px-6 py-16 text-white">
    <p className="text-emerald-300 text-sm uppercase tracking-widest">Try without an account</p>
    <h1 className="text-4xl md:text-5xl my-5">Build your first synthetic cohort.</h1>
    <p className="text-white/70 text-lg max-w-3xl">Explore 24 fictional profiles. Choose a diagnosis and minimum age, then run a query through the same filter evaluator used by the pilot research workspace.</p>
    <p className="text-white/60 my-4">This demo never reads patient data. Its simplified fixtures are for software evaluation, not clinical interpretation or estimates of available patients.</p>
    <div className="grid md:grid-cols-2 gap-8 mt-10">
      <form onSubmit={run} className="border border-white/20 rounded-xl p-6 space-y-5">
        <fieldset disabled={busy} className="space-y-5">
          <div><label htmlFor="demo-diagnosis" className="block mb-2">Diagnosis</label>
            <select id="demo-diagnosis" value={diagnosis} onChange={change(setDiagnosis)} className="w-full bg-black border border-white/30 rounded p-3">
              <option value="">All diagnoses</option>{['Multiple Myeloma', 'DLBCL', 'AML'].map(d => <option key={d}>{d}</option>)}
            </select></div>
          <div><label htmlFor="demo-age" className="block mb-2">Minimum age (optional)</label>
            <input id="demo-age" type="number" min="0" max="130" step="1" value={age} onChange={change(setAge)} className="w-full bg-black border border-white/30 rounded p-3" /></div>
          <button className="bg-emerald-300 text-black rounded px-5 py-3 font-medium disabled:opacity-50" type="submit">{busy ? 'Running query…' : 'Run feasibility'}</button>
        </fieldset>
        {error && <p role="alert" className="text-red-300">{error} You can retry the query.</p>}
      </form>
      <section aria-live="polite" aria-busy={busy} className="border border-white/20 rounded-xl p-6">
        <h2 className="text-xl mb-4">Query result</h2>
        {result ? <><p className="text-5xl text-emerald-300 mb-3">{result.patient_count}<span className="text-lg text-white/60"> / {result.total_profiles}</span></p><p>Fictional profiles match these filters.</p><p className="text-white/60 mt-3">{result.data_points} synthetic records · fixture version {result.fixture_version}</p></> : <p className="text-white/60">Run a query to see the matching count. Changing filters clears the previous result.</p>}
      </section>
    </div>
    <section className="mt-10"><h2 className="text-2xl mb-3">Use the same query from an AI agent</h2><p className="text-white/70 mb-4">POST this JSON to <code>/api/demo/cohort/build</code>. The public demo requires no API key.</p><pre className="bg-white/5 p-5 rounded overflow-x-auto text-sm">{JSON.stringify(criteria, null, 2)}</pre><Link className="inline-block text-emerald-300 underline mt-4" to="/developers">Open the API quickstart →</Link></section>
    <section className="mt-12 border-t border-white/20 pt-8"><h2 className="text-2xl mb-3">Help shape the pilot</h2><p className="text-white/70 mb-4">Evaluate cohort definition, field selection, and approval workflows with us. We welcome researchers, institutional design partners, and funders interested in validating the next milestones.</p><Link to="/contact" className="text-emerald-300 underline">Discuss a pilot or partnership →</Link></section>
  </div>;
}
