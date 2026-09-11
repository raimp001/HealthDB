export const API_URL = (process.env.REACT_APP_API_URL || (process.env.NODE_ENV === 'production'
  ? '' : 'http://localhost:8000')).replace(/\/$/, '');

export const SESSION_EVENT = 'healthdb-session';

export function readSessionUser() {
  try { return JSON.parse(sessionStorage.getItem('user') || 'null'); }
  catch { return null; }
}

export function clearSession() {
  sessionStorage.removeItem('token');
  sessionStorage.removeItem('user');
  window.dispatchEvent(new Event(SESSION_EVENT));
}

export function saveSession(data) {
  sessionStorage.setItem('token', data.access_token);
  sessionStorage.setItem('user', JSON.stringify({
    id: data.user.id, name: data.user.name, user_type: data.user.user_type,
  }));
  window.dispatchEvent(new Event(SESSION_EVENT));
}

export function dashboardForRole(role) {
  return { patient: '/patient', researcher: '/research', institution: '/institution', admin: '/admin' }[role] || '/';
}

export function signInDestination(from, role) {
  const paths = { patient: ['/patient'], institution: ['/institution'],
    researcher: ['/projects', '/research', '/research-readiness', '/collaborations', '/cohort-builder', '/repo-analyzer', '/marketplace'],
    admin: ['/projects', '/admin', '/research', '/research-readiness', '/collaborations', '/institution', '/cohort-builder', '/repo-analyzer', '/marketplace'] };
  if (typeof from === 'string' && paths[role]?.includes(from.split(/[?#]/)[0])) return from;
  return dashboardForRole(role);
}

export async function apiFetch(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  const abort = () => controller.abort();
  if (options.signal?.aborted) controller.abort();
  options.signal?.addEventListener('abort', abort, { once: true });
  try {
    const response = await window.fetch(url, { ...options, signal: controller.signal });
    if (!response.ok) {
      let data;
      try { data = await response.json(); } catch { data = {}; }
      const detail = typeof data.detail === 'string' ? data.detail
        : Array.isArray(data.detail) ? data.detail.map(item => item.msg).join('; ') : '';
      if (response.status === 401 && !url.includes('/api/auth/login')) clearSession();
      const message = response.status >= 500
        ? 'The service is temporarily unavailable. Please try again shortly.'
        : response.status === 429 ? 'Too many requests. Please wait a moment and try again.'
        : detail || `The request failed (${response.status}). Please try again.`;
      const error = new Error(message);
      error.status = response.status;
      throw error;
    }
    return response;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The request timed out. Check whether your action completed before retrying.');
    if (error instanceof TypeError) throw new Error('Could not connect to HealthDB. Check your connection and try again.');
    throw error;
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener('abort', abort);
  }
}

// Load several independent panels, letting each fail on its own.
//
// apiFetch throws on any non-2xx, so `Promise.all` over a dashboard's fetches
// meant one gated, rate-limited or briefly unavailable endpoint rejected the
// batch and blanked the entire page. A screen made of independent panels
// should lose the panel, not the screen.
//
// Returns { values, failures }: `values` is positional with null where a
// request failed, and `failures` carries the errors for anything a caller
// wants to treat as fatal — a dashboard with no profile has no subject, and
// rendering empty panels around nothing would be a lie.
export async function loadPanels(requests) {
  const settled = await Promise.allSettled(requests.map((run) => run()));
  const values = [];
  const failures = [];
  for (const [index, result] of settled.entries()) {
    if (result.status !== 'fulfilled') {
      values.push(null);
      failures.push({ index, error: result.reason });
      continue;
    }
    try {
      const body = result.value;
      // Accept either a Response (from apiFetch) or already-parsed data
      // (from apiRequest), so callers are not forced to pick one.
      values.push(typeof body?.json === 'function' ? await body.json() : body);
    } catch (error) {
      values.push(null);
      failures.push({ index, error });
    }
  }
  return { values, failures };
}


export async function apiRequest(path, options = {}) {
  const response = await apiFetch(`${API_URL}${path}`, options);
  try { return await response.json(); }
  catch { throw new Error('The service returned an unexpected response. Please try again.'); }
}

export async function downloadCsv(url, filename, options = {}) {
  const response = await apiFetch(url, options);
  const blobUrl = URL.createObjectURL(await response.blob());
  const anchor = document.createElement('a');
  anchor.href = blobUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
}
