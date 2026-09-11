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

test('one failing panel does not cost the others', async () => {
  const { loadPanels } = require('./api');
  const { values, failures } = await loadPanels([
    () => Promise.resolve({ json: async () => ['a'] }),
    () => Promise.reject(Object.assign(new Error('Forbidden'), { status: 403 })),
    () => Promise.resolve({ json: async () => ['c'] }),
  ]);
  expect(values).toEqual([['a'], null, ['c']]);
  expect(failures).toHaveLength(1);
  expect(failures[0].index).toBe(1);
});

test('a panel returning unparseable content fails alone', async () => {
  const { loadPanels } = require('./api');
  const { values, failures } = await loadPanels([
    () => Promise.resolve({ json: async () => { throw new Error('not json'); } }),
    () => Promise.resolve({ json: async () => ['b'] }),
  ]);
  expect(values).toEqual([null, ['b']]);
  expect(failures.map(f => f.index)).toEqual([0]);
});

test('already-parsed data is passed through unchanged', async () => {
  const { loadPanels } = require('./api');
  const { values } = await loadPanels([() => Promise.resolve({ total: 3 })]);
  expect(values).toEqual([{ total: 3 }]);
});

test('every panel failing still resolves rather than throwing', async () => {
  const { loadPanels } = require('./api');
  const { values, failures } = await loadPanels([
    () => Promise.reject(new Error('one')),
    () => Promise.reject(new Error('two')),
  ]);
  expect(values).toEqual([null, null]);
  expect(failures).toHaveLength(2);
});
