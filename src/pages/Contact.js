import React, { useState } from 'react';
import { motion } from 'framer-motion';

const API_URL = process.env.REACT_APP_API_URL || '';

const INTEREST_TYPES = [
  { value: 'researcher', label: 'I am a researcher looking for data' },
  { value: 'institution', label: 'I represent an institution / site' },
  { value: 'patient', label: 'I am a patient with questions' },
  { value: 'partnership', label: 'Partnership or sponsorship' },
  { value: 'other', label: 'Something else' },
];

const Contact = () => {
  const [form, setForm] = useState({
    name: '',
    email: '',
    organization: '',
    interest_type: 'researcher',
    message: '',
  });
  const [status, setStatus] = useState({ state: 'idle', message: '' });

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ state: 'sending', message: '' });
    try {
      const response = await fetch(`${API_URL}/api/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await response.json();
      if (response.ok) {
        setStatus({ state: 'sent', message: data.message || 'Thanks — we received your message.' });
        setForm({ name: '', email: '', organization: '', interest_type: 'researcher', message: '' });
      } else {
        const detail = typeof data.detail === 'string' ? data.detail : 'Please check the form and try again.';
        setStatus({ state: 'error', message: detail });
      }
    } catch (err) {
      setStatus({ state: 'error', message: 'Could not reach the server. Please try again.' });
    }
  };

  const inputClass =
    'w-full bg-transparent border border-white/10 px-4 py-3 text-white placeholder-white/30 focus:border-emerald-400 focus:outline-none';

  return (
    <div className="min-h-screen bg-black text-white">
      <section className="py-24 px-6">
        <div className="max-w-2xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <p className="text-sm text-emerald-400 uppercase tracking-wider mb-4">Contact</p>
            <h1 className="text-4xl md:text-5xl font-bold mb-6">Get in touch</h1>
            <p className="text-white/60 mb-10">
              Tell us what you're working on. We read every message and typically respond within one
              business day.
            </p>
          </motion.div>

          {status.state === 'sent' ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="border border-emerald-400/30 bg-emerald-400/5 p-8"
            >
              <p className="text-emerald-400 text-lg mb-2">Message received</p>
              <p className="text-white/60 text-sm mb-6">{status.message}</p>
              <button
                onClick={() => setStatus({ state: 'idle', message: '' })}
                className="text-sm text-white/60 hover:text-white underline"
              >
                Send another message
              </button>
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="grid md:grid-cols-2 gap-5">
                <div>
                  <label htmlFor="contact-name" className="block text-xs uppercase tracking-wider text-white/60 mb-2">
                    Name
                  </label>
                  <input
                  id="contact-organization"
                  id="contact-email"
                  id="contact-name"
                    type="text"
                    required
                    value={form.name}
                    onChange={update('name')}
                    placeholder="Jane Doe"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label htmlFor="contact-email" className="block text-xs uppercase tracking-wider text-white/60 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    value={form.email}
                    onChange={update('email')}
                    placeholder="you@example.com"
                    className={inputClass}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="contact-organization" className="block text-xs uppercase tracking-wider text-white/60 mb-2">
                  Organization
                </label>
                <input
                  type="text"
                  required
                  value={form.organization}
                  onChange={update('organization')}
                  placeholder="University, hospital, company, or 'Independent'"
                  className={inputClass}
                />
              </div>

              <div>
                <label htmlFor="contact-interest" className="block text-xs uppercase tracking-wider text-white/60 mb-2">
                  What brings you here?
                </label>
                <select value={form.interest_type}
                  id="contact-interest" onChange={update('interest_type')} className={inputClass}>
                  {INTEREST_TYPES.map((opt) => (
                    <option key={opt.value} value={opt.value} className="bg-black">
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="contact-message" className="block text-xs uppercase tracking-wider text-white/60 mb-2">
                  Message
                </label>
                <textarea
                  id="contact-message"
                  required
                  rows={6}
                  value={form.message}
                  onChange={update('message')}
                  placeholder="Describe your study, your data needs, or your question."
                  className={inputClass}
                />
              </div>

              {status.state === 'error' && (
                <p className="text-red-400 text-sm">{status.message}</p>
              )}

              <button
                type="submit"
                disabled={status.state === 'sending'}
                className="px-8 py-3 bg-emerald-500 text-black font-medium hover:bg-emerald-400 transition-colors disabled:opacity-50"
              >
                {status.state === 'sending' ? 'Sending…' : 'Send message'}
              </button>

              <p className="text-white/50 text-xs leading-relaxed">
                Please don't include patient identifiers or protected health information in this
                form. It is a general enquiry channel, not a clinical data pathway.
              </p>
            </form>
          )}
        </div>
      </section>
    </div>
  );
};

export default Contact;
