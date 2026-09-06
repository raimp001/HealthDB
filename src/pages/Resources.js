import { API_URL, apiFetch as fetch } from '../lib/api';
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const resources = [
  {
    to: '/platform',
    label: 'Product roadmap',
    description: 'See which modules exist in the prototype and which remain target architecture.',
  },
  {
    to: '/security-posture',
    label: 'Security posture map',
    description: 'Review current safeguards, missing controls, and the intended trust boundary.',
  },
  {
    to: '/data-flow',
    label: 'Current data flow',
    description: 'Follow the narrow synthetic-data path and see what is still required for real-world use.',
  },
  {
    to: '/privacy',
    label: 'Pilot privacy notice',
    description: 'Understand what this website stores and why real patient data is prohibited.',
  },
];

const Resources = () => {
  const [email, setEmail] = useState('');
  const [state, setState] = useState({ status: 'idle', message: '' });

  const subscribe = async (event) => {
    event.preventDefault();
    setState({ status: 'sending', message: '' });

    try {
      const response = await fetch(`${API_URL}/api/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Product update subscriber',
          email,
          organization: 'Not provided',
          message: 'Requested occasional HealthDB pilot updates.',
          interest_type: 'newsletter',
        }),
      });

      if (!response.ok) throw new Error('We could not save your request. Please try again.');
      setEmail('');
      setState({ status: 'done', message: 'Request received.' });
    } catch (error) {
      setState({ status: 'error', message: error.message });
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <section className="py-28 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55 }}
            className="max-w-3xl"
          >
            <p className="text-xs text-emerald-300 uppercase tracking-[0.2em] mb-5">Resources</p>
            <h1 className="text-4xl md:text-6xl font-medium mb-7">Inspect the product before you trust it.</h1>
            <p className="text-lg text-white/50 max-w-2xl leading-relaxed">
              These notes document the prototype, its intended architecture, and its current limits.
              They do not represent certifications, legal approvals, or production readiness.
            </p>
          </motion.div>
        </div>
      </section>

      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-5">
          {resources.map((resource) => (
            <Link key={resource.to} to={resource.to} className="group p-7 border border-white/10 hover:border-white/25 transition-colors">
              <h2 className="text-xl font-medium mb-3 group-hover:text-emerald-300 transition-colors">{resource.label}</h2>
              <p className="text-sm text-white/45 leading-relaxed mb-7">{resource.description}</p>
              <span className="text-sm text-white/45">Open resource →</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-start">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-blue-300 mb-3">Review standard</p>
            <h2 className="text-3xl font-medium mb-5">Three questions for every claim</h2>
            <ol className="space-y-4 text-sm text-white/50">
              <li><span className="text-white/25 mr-3">01</span>Is it implemented in the current code?</li>
              <li><span className="text-white/25 mr-3">02</span>Has it been tested with representative synthetic data?</li>
              <li><span className="text-white/25 mr-3">03</span>Has an independent reviewer validated it?</li>
            </ol>
          </div>
          <div className="border border-white/10 p-7">
            <h2 className="text-xl font-medium mb-3">Receive occasional pilot updates</h2>
            <p className="text-sm text-white/45 mb-6">Only material product-status changes—no claims of availability before they are true.</p>
            {state.status === 'done' ? (
              <p className="text-emerald-300 text-sm" role="status">{state.message}</p>
            ) : (
              <form onSubmit={subscribe} className="space-y-3">
                <label htmlFor="updates-email" className="sr-only">Email address</label>
                <input
                  id="updates-email"
                  type="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  className="w-full bg-transparent border border-white/15 px-4 py-3 text-white placeholder-white/30 focus:border-emerald-400 focus:outline-none"
                />
                {state.status === 'error' && <p className="text-red-300 text-sm" role="alert">{state.message}</p>}
                <button
                  type="submit"
                  disabled={state.status === 'sending'}
                  className="w-full px-5 py-3 bg-white text-black text-sm font-medium disabled:opacity-50"
                >
                  {state.status === 'sending' ? 'Saving…' : 'Request updates'}
                </button>
              </form>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Resources;
