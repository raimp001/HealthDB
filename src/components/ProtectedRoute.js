import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { API_URL, apiFetch, dashboardForRole, SESSION_EVENT } from '../lib/api';

export default function ProtectedRoute({ roles, children }) {
  const location = useLocation();
  const [sessionVersion, setSessionVersion] = useState(0);
  const [session, setSession] = useState({ loading: true });
  const token = sessionStorage.getItem('token');

  useEffect(() => {
    const changed = () => setSessionVersion(version => version + 1);
    window.addEventListener(SESSION_EVENT, changed);
    return () => window.removeEventListener(SESSION_EVENT, changed);
  }, []);

  useEffect(() => {
    let current = true;
    setSession({ loading: true });
    if (!token) return () => { current = false; };
    apiFetch(`${API_URL}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(response => response.json())
      .then(user => {
        if (!current) return;
        sessionStorage.setItem('user', JSON.stringify({ id: user.id, name: user.name, user_type: user.user_type }));
        setSession({ user, loading: false });
      })
      .catch(error => { if (current) setSession({ error: error.message, loading: false }); });
    return () => { current = false; };
  }, [token, sessionVersion]);

  if (!token) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  if (session.loading) return <div role="status" className="max-w-xl mx-auto py-24 px-6 text-white/70">Checking your session…</div>;
  if (session.error) return (
    <div role="alert" className="max-w-xl mx-auto py-24 px-6 text-white">
      <h1 className="text-2xl mb-4">We couldn’t open your workspace</h1>
      <p className="text-white/70 mb-6">{session.error}</p>
      <button className="bg-emerald-400 text-black px-5 py-3" onClick={() => setSessionVersion(version => version + 1)}>Try again</button>
    </div>
  );
  const adminWorkspace = session.user.user_type === 'admin' && roles?.some(role => ['researcher', 'institution'].includes(role));
  if (roles && !roles.includes(session.user.user_type) && !adminWorkspace) return <Navigate to={dashboardForRole(session.user.user_type)} replace />;
  return children;
}
