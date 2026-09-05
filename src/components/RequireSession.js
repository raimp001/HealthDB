import React, { useEffect, useState } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { apiRequest } from '../lib/api';
import { clearSession, destinationFor, saveUser } from '../lib/session';

export default function RequireSession({ roles, children }) {
  const location = useLocation();
  const token = sessionStorage.getItem('token');
  const [state, setState] = useState({ loading: true });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!token) return;
    let active = true;
    setState({ loading: true });
    apiRequest('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then(user => {
        if (!active) return;
        saveUser(user);
        setState({ user });
      })
      .catch(error => {
        if (!active) return;
        if ([401, 403, 404].includes(error.status)) {
          clearSession();
          setState({ expired: true });
        } else {
          setState({ error: error.message });
        }
      });
    return () => { active = false; };
  }, [token, attempt, location.pathname]);

  if (!token || state.expired) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search, expired: state.expired }} />;
  }
  if (state.loading) return <div role="status" className="px-6 py-24 text-center text-white/70">Checking your session…</div>;
  if (state.error) return (
    <div role="alert" className="max-w-lg mx-auto px-6 py-24 text-center">
      <h1 className="text-2xl text-white mb-4">Unable to open your workspace</h1>
      <p className="text-white/70 mb-6">{state.error}</p>
      <button onClick={() => setAttempt(value => value + 1)} className="px-6 py-3 bg-white text-black">Try again</button>
      <Link to="/contact" className="block mt-6 text-emerald-400">Contact support</Link>
    </div>
  );
  if (!roles.includes(state.user.user_type)) return <Navigate to={destinationFor(state.user)} replace />;
  return children;
}
