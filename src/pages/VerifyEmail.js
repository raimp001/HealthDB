import React, { useEffect, useState, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';

const API_URL = process.env.NODE_ENV === 'production' ? '' : (process.env.REACT_APP_API_URL || 'http://localhost:8000');

const VerifyEmail = () => {
  const [params] = useSearchParams();
  const token = params.get('token');
  const [state, setState] = useState({ status: token ? 'verifying' : 'missing', message: '' });
  // Tokens are single-use, so React 18's double-invoked effect in StrictMode
  // would burn the token on the first call and fail on the second.
  const attempted = useRef(false);

  useEffect(() => {
    if (!token || attempted.current) return;
    attempted.current = true;

    (async () => {
      try {
        const res = await fetch(`${API_URL}/api/auth/verify-email`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Verification failed');
        setState({ status: 'done', message: data.message });
      } catch (err) {
        setState({ status: 'error', message: err.message });
      }
    })();
  }, [token]);

  const copy = {
    verifying: { title: 'Verifying your address…', tone: 'text-white/40' },
    done: { title: 'Address verified', tone: 'text-emerald-400' },
    error: { title: 'That link did not work', tone: 'text-red-400' },
    missing: { title: 'No verification token', tone: 'text-amber-400' },
  }[state.status];

  return (
    <div className="min-h-screen bg-black flex items-center justify-center py-20 px-6">
      <div className="absolute inset-0 gradient-bg opacity-50" />
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md text-center"
      >
        <h1 className={`text-2xl font-bold mb-3 ${copy.tone}`}>{copy.title}</h1>
        <p className="text-white/40 text-sm mb-8">
          {state.status === 'missing'
            ? 'Open the link from your verification email to continue.'
            : state.message || 'Verification links expire after 48 hours and work once.'}
        </p>
        <div className="flex gap-3 justify-center">
          <Link to="/login" className="px-6 py-3 bg-white text-black text-sm font-medium hover:bg-gray-100 transition-colors">
            Sign in
          </Link>
          <Link to="/contact" className="px-6 py-3 border border-white/20 text-sm hover:bg-white/5 transition-colors">
            Get help
          </Link>
        </div>
      </motion.div>
    </div>
  );
};

export default VerifyEmail;
