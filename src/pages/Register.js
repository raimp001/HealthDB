import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Register = () => {
  const [searchParams] = useSearchParams();
  const initialType = searchParams.get('type') || 'researcher';
  
  const [userType, setUserType] = useState(initialType);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [institution, setInstitution] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          user_type: userType,
          institution: userType === 'researcher' ? institution : undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      navigate('/login');
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
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
          <h1 className="heading-display text-3xl text-white mb-2">Create account</h1>
          <p className="text-white/40">Join the platform</p>
        </div>

        {/* Form */}
        <div className="border border-white/10 p-8">
          {/* User Type Toggle */}
          <div className="mb-8">
            <label className="block text-xs uppercase tracking-wider text-white/40 mb-3">
              Account Type
            </label>
            <div className="grid grid-cols-2 gap-px bg-white/10">
              <button
                type="button"
                onClick={() => setUserType('researcher')}
                className={`py-3 text-xs uppercase tracking-wider transition-colors ${
                  userType === 'researcher'
                    ? 'bg-white text-black'
                    : 'bg-black text-white/50 hover:text-white'
                }`}
              >
                Researcher
              </button>
              <button
                type="button"
                onClick={() => setUserType('patient')}
                className={`py-3 text-xs uppercase tracking-wider transition-colors ${
                  userType === 'patient'
                    ? 'bg-white text-black'
                    : 'bg-black text-white/50 hover:text-white'
                }`}
              >
                Patient
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-xs uppercase tracking-wider text-white/40 mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none transition-colors"
                placeholder="you@example.com"
              />
            </div>

            {userType === 'researcher' && (
              <div>
                <label className="block text-xs uppercase tracking-wider text-white/40 mb-2">
                  Institution
                </label>
                <input
                  type="text"
                  value={institution}
                  onChange={(e) => setInstitution(e.target.value)}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none transition-colors"
                  placeholder="Stanford University"
                />
              </div>
            )}

            <div>
              <label className="block text-xs uppercase tracking-wider text-white/40 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none transition-colors"
                placeholder="••••••••"
              />
              <p className="mt-2 text-xs text-white/30">Minimum 8 characters</p>
            </div>

            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                required
                className="mt-1 w-4 h-4 bg-white/5 border border-white/20 rounded-none"
              />
              <label className="text-sm text-white/40">
                I agree to the{' '}
                <a href="#" className="text-white/60 hover:text-white">Terms</a>
                {' '}and{' '}
                <a href="#" className="text-white/60 hover:text-white">Privacy Policy</a>
              </label>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          {/* Benefits */}
          {userType === 'researcher' && (
            <div className="mt-8 pt-8 border-t border-white/10">
              <p className="text-xs uppercase tracking-wider text-white/40 mb-4">Researcher Benefits</p>
              <ul className="space-y-2 text-sm text-white/50">
                <li className="flex items-center gap-2">
                  <span className="w-1 h-1 bg-[#00d4aa] rounded-full"></span>
                  Access curated oncology datasets
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1 h-1 bg-[#00d4aa] rounded-full"></span>
                  Build custom research cohorts
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1 h-1 bg-[#00d4aa] rounded-full"></span>
                  Collaborate across institutions
                </li>
              </ul>
            </div>
          )}

          {userType === 'patient' && (
            <div className="mt-8 pt-8 border-t border-white/10">
              <p className="text-xs uppercase tracking-wider text-white/40 mb-4">Patient Benefits</p>
              <ul className="space-y-2 text-sm text-white/50">
                <li className="flex items-center gap-2">
                  <span className="w-1 h-1 bg-[#00d4aa] rounded-full"></span>
                  Contribute to cancer research
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1 h-1 bg-[#00d4aa] rounded-full"></span>
                  Control your data sharing
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1 h-1 bg-[#00d4aa] rounded-full"></span>
                  Earn rewards for participation
                </li>
              </ul>
            </div>
          )}

          <div className="mt-8 pt-8 border-t border-white/10">
            <p className="text-center text-white/40 text-sm">
              Already have an account?{' '}
              <Link to="/login" className="text-white hover:text-[#00d4aa] transition-colors">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Register;
