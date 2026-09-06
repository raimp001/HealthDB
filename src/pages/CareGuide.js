import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import catalog from '../data/careGuides.json';
import './CareGuide.css';

export function planText(guide, checked = []) {
  return [`HealthDB — ${guide.title}`, 'General US education, not a personalized recommendation or referral.',
    guide.summary, guide.limits, `Source: ${guide.source}`, `Source date: ${guide.published}; content checked: ${catalog.version}`,
    '', 'Questions for your clinician', ...guide.questions.map(q => `• ${q}`), '',
    'My preparation checklist (self-reported, not a clinical record)',
    ...guide.steps.map((step, i) => `${checked.includes(i) ? '[x]' : '[ ]'} ${step}`), '',
    `${guide.directory.label}: ${guide.directory.url}`,
    guide.assistance ? `${guide.assistance.label}: ${guide.assistance.url}` : '',
    'Directory listings are not bookings or endorsements. Confirm services and coverage directly.',
    'HealthDB does not monitor symptoms or results. For a medical emergency, call 911 in the US.'].filter(Boolean).join('\n\n');
}

function ExternalLink({ url, children }) {
  return <a href={url} target="_blank" rel="noopener noreferrer" className="care-link">{children} <span className="text-sm">↗ (external)</span></a>;
}

export default function CareGuide() {
  const [topic, setTopic] = useState('breast');
  const [progress, setProgress] = useState({});
  const [message, setMessage] = useState('');
  const guide = catalog.guides.find(g => g.id === topic);
  const checked = progress[topic] || [];
  const toggle = index => setProgress(previous => {
    const items = previous[topic] || [];
    return { ...previous, [topic]: items.includes(index) ? items.filter(i => i !== index) : [...items, index] };
  });
  const download = () => {
    try {
      const url = URL.createObjectURL(new Blob([planText(guide, checked)], { type: 'text/plain;charset=utf-8' }));
      const anchor = document.createElement('a');
      anchor.href = url; anchor.download = `healthdb-${topic}-guide.txt`;
      document.body.appendChild(anchor); anchor.click(); anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setMessage('Download requested. The file includes this topic and your checklist; keep it private on shared devices.');
    } catch { setMessage('Download could not start. You can select and copy the guide text instead.'); }
  };
  return <div className="care-page">
    <div className="max-w-6xl mx-auto px-5 py-12 md:py-16">
      <header className="max-w-3xl mb-10">
        <p className="care-eyebrow">Your next step, made clearer</p>
        <h1 className="text-4xl md:text-6xl font-semibold tracking-tight mt-3 mb-5">Understand screening.<br />Find your way to care.</h1>
        <p className="text-lg text-slate-600">Explore trusted US screening guidance, prepare questions, and find services. No account or medical records needed.</p>
      </header>
      <aside className="care-notice mb-8" aria-label="Clinical boundaries">
        <strong>A guide for a conversation with your clinician.</strong> These are general guidelines, not a decision about which tests you personally need. HealthDB does not book appointments, issue referrals, interpret results, or monitor your care. New symptoms need clinical assessment; for a medical emergency, call 911 in the US.
      </aside>
      <div className="grid lg:grid-cols-[240px_1fr] gap-8 items-start">
        <nav aria-label="Screening topics" className="care-card">
          <h2 className="font-semibold mb-4">What would you like to explore?</h2>
          <div className="flex flex-col gap-2">{catalog.guides.map(item => <button key={item.id} type="button" aria-pressed={topic === item.id}
            className={`care-topic ${topic === item.id ? 'care-topic-active' : ''}`}
            onClick={() => { setTopic(item.id); setMessage(''); }}>{item.title}</button>)}</div>
          <p className="text-sm text-slate-600 mt-5">A starting collection, not a complete preventive-care schedule. Ask your clinician about other screenings and vaccinations.</p>
        </nav>
        <div className="space-y-6">
          <section className="care-card" aria-labelledby="guideline-title" aria-live="polite">
            <p className="care-eyebrow">01 · Understand the guidance</p>
            <h2 id="guideline-title" className="text-3xl font-semibold my-4">{guide.title}</h2>
            <p className="text-lg leading-relaxed mb-4">{guide.summary}</p>
            <p className="text-slate-600 leading-relaxed mb-5">{guide.limits}</p>
            <ExternalLink url={guide.source}>Read the full USPSTF recommendation</ExternalLink>
            <p className="text-sm text-slate-500 mt-3">Published {guide.published} · Content checked {catalog.version} · Other professional guidelines may differ.</p>
          </section>
          <section className="care-card">
            <p className="care-eyebrow">02 · Find care and understand costs</p>
            <h2 className="text-2xl font-semibold my-4">Start with a real service</h2>
            <div className="space-y-4"><p><ExternalLink url={guide.directory.url}>{guide.directory.label}</ExternalLink></p>
              {guide.assistance && <p><ExternalLink url={guide.assistance.url}>{guide.assistance.label}</ExternalLink></p>}
              {topic === 'breast' && <p><ExternalLink url="https://findahealthcenter.hrsa.gov/">Find a primary care health center</ExternalLink></p>}
            </div>
            <p className="text-slate-600 mt-5">These official directories open outside HealthDB. Contact the service and your insurer to confirm availability, services, referral requirements, accessibility, and cost. Assistance eligibility varies. A listing is not a booking, partnership, or endorsement.</p>
            <details className="mt-5"><summary className="font-semibold cursor-pointer">Questions to ask when calling</summary><p className="mt-3 text-slate-600">“Do you offer this test? Do I need a clinician's order? Are you in my plan's network, and what could I pay? Is financial assistance available? Can you meet my language, mobility, or transport needs? Who receives the report, and whom should I call about results?”</p></details>
          </section>
          <section className="care-card">
            <p className="care-eyebrow">03 · Prepare for the conversation</p>
            <h2 className="text-2xl font-semibold my-4">Bring these questions</h2>
            <ul className="list-disc pl-5 space-y-3">{guide.questions.map(q => <li key={q}>{q}</li>)}</ul>
          </section>
          <section className="care-card">
            <p className="care-eyebrow">04 · Keep track of your next steps</p>
            <h2 className="text-2xl font-semibold my-4">From discussion to follow-up</h2>
            <p className="text-slate-600 mb-4">Optional, self-reported preparation checklist. It does not verify that care occurred. Progress stays in this page's memory and clears on reload; nothing here is sent to HealthDB.</p>
            <p role="status" className="font-semibold mb-2">{checked.length} of {guide.steps.length} steps checked</p>
            <progress aria-label="Checklist progress" value={checked.length} max={guide.steps.length} className="w-full h-2 mb-5" />
            <div className="space-y-3">{guide.steps.map((step, index) => <label key={`${topic}-${index}`} className="care-step"><input type="checkbox" checked={checked.includes(index)} onChange={() => toggle(index)} /><span>{step}</span></label>)}</div>
            {checked.length === guide.steps.length && <p className="care-notice mt-5">Your checklist is complete. Follow your care team's instructions for any outstanding care or future screening; this is not a clinical clearance.</p>}
            <div className="flex flex-wrap gap-3 mt-6"><button type="button" className="care-primary" onClick={download}>Download my guide</button><button type="button" className="care-secondary" onClick={() => { setProgress({}); setMessage('All checklist progress cleared.'); }}>Clear all progress</button></div>
            <p role="status" className="text-sm text-slate-600 mt-3">{message}</p>
          </section>
          <footer className="text-sm text-slate-600 pb-6">No health score, cash reward, or data sharing is required to use this guide. <Link to="/contact?interest=patient" className="care-link">Help improve the experience</Link> without including personal health information.</footer>
        </div>
      </div>
    </div>
  </div>;
}
