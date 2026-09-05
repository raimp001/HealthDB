export const DASHBOARD_BY_ROLE = {
  patient: '/patient',
  researcher: '/research',
  institution: '/institution',
  admin: '/research',
};

export function clearSession() {
  sessionStorage.removeItem('token');
  sessionStorage.removeItem('user');
  window.dispatchEvent(new Event('healthdb-session'));
}

export function saveUser(user) {
  sessionStorage.setItem('user', JSON.stringify({
    id: user.id, name: user.name, user_type: user.user_type,
  }));
  window.dispatchEvent(new Event('healthdb-session'));
}

export function readStoredUser() {
  try {
    if (!sessionStorage.getItem('token')) return null;
    return JSON.parse(sessionStorage.getItem('user') || 'null');
  } catch {
    return null;
  }
}

export function destinationFor(user, requested) {
  const allowed = {
    patient: ['/patient'],
    researcher: ['/research', '/cohort-builder'],
    institution: ['/institution'],
    admin: ['/research', '/cohort-builder', '/institution'],
  }[user.user_type] || [];
  // Only known local routes may be used as a post-login destination.
  if (typeof requested === 'string' && allowed.includes(requested.split(/[?#]/)[0])) return requested;
  return DASHBOARD_BY_ROLE[user.user_type] || '/';
}
