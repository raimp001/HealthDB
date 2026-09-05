export const API_URL = (process.env.REACT_APP_API_URL ||
  (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000')).replace(/\/$/, '');

export async function apiRequest(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(`${API_URL}${path}`, { ...options, signal: controller.signal });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = data?.detail;
      const message = response.status >= 500
        ? 'The service is temporarily unavailable. Please try again shortly.'
        : typeof detail === 'string' ? detail
          : Array.isArray(detail) ? detail.map(item => item.msg).join('. ')
            : 'The request could not be completed. Please try again.';
      const error = new Error(message);
      error.status = response.status;
      throw error;
    }
    if (data === null) throw new Error('The service returned an unexpected response. Please try again.');
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The request timed out. Please try again.');
    if (error instanceof TypeError) throw new Error('Could not connect. Check your connection and try again.');
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
