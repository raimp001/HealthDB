import { API_URL, apiFetch as fetch, saveSession, signInDestination } from '../lib/api';
import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';

// Use relative URL in production (same origin), fallback to localhost in dev

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();
      saveSession(data);
      navigate(signInDestination(location.state?.from, data.user.user_type), { replace: true });
    } catch (err) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center py-20 px-6">
      <div className="absolute inset-0 gradient-bg opacity-50" />
      <div className="absolute inset-0 grid-pattern" />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Header */}
        <div className="text-center mb-12">
          <Link to="/" className="inline-block text-2xl font-medium text-white mb-8">
            HealthDB
          </Link>
          <h1 className="heading-display text-3xl text-white mb-2">Sign in</h1>
          <p className="text-white/40">Invited pilot accounts only</p>
          <Link to="/explore" className="block mt-5 rounded bg-emerald-300 px-5 py-3 text-black font-medium">Continue as guest — no sign-in</Link>
        </div>

        {/* Form */}
        <div className="border border-white/10 p-8">
          {error && (
            <div role="alert" className="mb-6 p-4 bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="login-email" className="block text-sm text-white/70 mb-2">
                Email
              </label>
              <input
                id="login-email" name="email" autoComplete="username" type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none transition-colors"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label htmlFor="login-password" className="block text-sm text-white/70">
                  Password
                </label>
                {/* No self-service reset exists yet; this is a manual request. */}
                <Link to="/contact" className="text-xs text-white/40 hover:text-white transition-colors">
                  Forgot? Contact us
                </Link>
              </div>
              <input
                id="login-password" name="password" autoComplete="current-password" type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none transition-colors"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-white/10">
            <p className="text-center text-white/40 text-sm">
              Need pilot access?{' '}
              <Link to="/contact?interest=pilot" className="text-white hover:text-[#00d4aa] transition-colors">
                Request an invitation
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
