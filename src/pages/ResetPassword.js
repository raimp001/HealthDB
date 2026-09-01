import React, { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

const API_URL = process.env.NODE_ENV === 'production' ? '' : (process.env.REACT_APP_API_URL || 'http://localhost:8000');

/**
 * Two states in one route: without a token we request a reset link, with one
 * (?token=…) we set the new password.
 */
const ResetPassword = () => {
  const [params] = useSearchParams();
  const token = params.get('token');
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [state, setState] = useState({ status: 'idle', message: '' });

  const requestLink = async (e) => {
    e.preventDefault();
    setState({ status: 'sending', message: '' });
    try {
      const res = await fetch(`${API_URL}/api/auth/request-password-reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Request failed');
      setState({ status: 'sent', message: data.message });
    } catch (err) {
      setState({ status: 'error', message: err.message });
    }
  };

  const submitNewPassword = async (e) => {
    e.preventDefault();
    if (password !== confirm) {
      setState({ status: 'error', message: 'The two passwords do not match.' });
      return;
    }
    setState({ status: 'sending', message: '' });
    try {
      const res = await fetch(`${API_URL}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Reset failed');
      setState({ status: 'done', message: data.message });
      setTimeout(() => navigate('/login'), 1800);
    } catch (err) {
      setState({ status: 'error', message: err.message });
    }
  };

  const field = 'w-full px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none transition-colors';

  return (
    <div className="min-h-screen bg-black flex items-center justify-center py-20 px-6">
      <div className="absolute inset-0 gradient-bg opacity-50" />
      <div className="absolute inset-0 grid-pattern" />
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md"
      >
        <h1 className="text-2xl font-bold mb-2">
          {token ? 'Choose a new password' : 'Reset your password'}
        </h1>
        <p className="text-white/40 text-sm mb-8">
          {token
            ? 'Reset links expire 30 minutes after they are issued and work once.'
            : 'Enter your address and we will send a reset link.'}
        </p>

        {state.status === 'done' || state.status === 'sent' ? (
          <div className="border border-emerald-400/30 bg-emerald-400/5 p-6">
            <p className="text-emerald-400 text-sm">{state.message}</p>
            <Link to="/login" className="text-white/50 hover:text-white text-sm underline mt-4 inline-block">
              Back to sign in
            </Link>
          </div>
        ) : (
          <form onSubmit={token ? submitNewPassword : requestLink} className="space-y-5">
            {token ? (
              <>
                <div>
                  <label htmlFor="new-password" className="block text-xs uppercase tracking-wider text-white/40 mb-2">
                    New password
                  </label>
                  <input
                    id="new-password" type="password" required autoComplete="new-password"
                    value={password} onChange={(e) => setPassword(e.target.value)} className={field}
                  />
                  <p className="text-xs text-white/30 mt-2">
                    At least 12 characters, with upper and lower case, a number and a symbol.
                  </p>
                </div>
                <div>
                  <label htmlFor="confirm-password" className="block text-xs uppercase tracking-wider text-white/40 mb-2">
                    Confirm password
                  </label>
                  <input
                    id="confirm-password" type="password" required autoComplete="new-password"
                    value={confirm} onChange={(e) => setConfirm(e.target.value)} className={field}
                  />
                </div>
              </>
            ) : (
              <div>
                <label htmlFor="email" className="block text-xs uppercase tracking-wider text-white/40 mb-2">
                  Email
                </label>
                <input
                  id="email" type="email" required autoComplete="email"
                  value={email} onChange={(e) => setEmail(e.target.value)} className={field}
                />
              </div>
            )}

            {state.status === 'error' && (
              <p role="alert" className="text-red-400 text-sm">{state.message}</p>
            )}

            <button
              type="submit"
              disabled={state.status === 'sending'}
              className="w-full py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {state.status === 'sending' ? 'Working…' : token ? 'Set new password' : 'Send reset link'}
            </button>
          </form>
        )}

        <p className="text-white/30 text-sm mt-8">
          Remembered it? <Link to="/login" className="text-white/60 hover:text-white underline">Sign in</Link>
        </p>
      </motion.div>
    </div>
  );
};

export default ResetPassword;
