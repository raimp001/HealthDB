import { apiRequest } from './api';

afterEach(() => { jest.restoreAllMocks(); });

test('preserves authentication errors for session recovery', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: 'Token expired' }) });
  await expect(apiRequest('/api/auth/me')).rejects.toMatchObject({ message: 'Token expired', status: 401 });
});

test('does not describe an outage as invalid credentials or expose server details', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({ detail: 'private database address' }) });
  await expect(apiRequest('/api/auth/login')).rejects.toThrow('The service is temporarily unavailable');
});

test('shows validation messages instead of object strings', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: [{ msg: 'Invalid email' }] }) });
  await expect(apiRequest('/api/auth/register')).rejects.toThrow('Invalid email');
});

test('detects HTML returned in place of an API response', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => { throw new SyntaxError(); } });
  await expect(apiRequest('/api/auth/me')).rejects.toThrow('unexpected response');
});
