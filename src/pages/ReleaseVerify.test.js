/**
 * A digest printed beside a release is a claim until someone can re-derive it.
 *
 * These hold one line in particular: "cannot be checked" must render as its
 * own answer, never as a tick. A release whose file is no longer stored is not
 * a verified release, and showing it as one would make the check worse than
 * absent — it would launder an unknown into a reassurance.
 */
const React = require('react');
const { createRoot } = require('react-dom/client');
const { act } = require('react-dom/test-utils');
const { MemoryRouter } = require('react-router-dom');

jest.mock('../lib/api', () => ({
  API_URL: '',
  apiFetch: jest.fn(),
  loadPanels: jest.requireActual('../lib/api').loadPanels,
  readSessionUser: () => ({ user_type: 'researcher' }),
}));
jest.mock('react-hot-toast', () => ({ __esModule: true, default: jest.fn() }));
jest.mock('framer-motion', () => {
  const ReactLib = require('react');
  const motion = new Proxy({}, {
    get: (_, tag) => ({ children, ...rest }) => {
      ['initial', 'animate', 'exit', 'transition', 'variants', 'whileHover',
       'whileTap', 'whileInView', 'viewport', 'layout', 'layoutId']
        .forEach((key) => delete rest[key]);
      return ReactLib.createElement(typeof tag === 'string' ? tag : 'div', rest, children);
    },
  });
  return {
    motion,
    AnimatePresence: ({ children }) => ReactLib.createElement(ReactLib.Fragment, null, children),
    useInView: () => true,
    useScroll: () => ({ scrollYProgress: { on: () => {} } }),
    useTransform: () => 0,
  };
});

const { apiFetch } = require('../lib/api');
const ResearcherDashboard = require('./ResearcherDashboard').default;

const OBLIGATION = {
  id: 'rel-1',
  study_name: 'Relapse timing in AML',
  released_at: '2026-09-01T00:00:00Z',
  withdrawal_required_at: '2026-09-15T00:00:00Z',
  content_digest: 'abc123def456abc123def456',
  action_required: 'Destroy your local copy of this extract and confirm in writing.',
};

let root, container;

function mockApi(verifyBody) {
  apiFetch.mockImplementation((url) => {
    if (url.includes('/verify')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(verifyBody) });
    }
    const body = url.includes('/api/researcher/release-obligations') ? [OBLIGATION] : [];
    return Promise.resolve({ ok: true, json: () => Promise.resolve(body) });
  });
}

beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  sessionStorage.setItem('token', 'test-token');
  container = document.createElement('div');
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  sessionStorage.clear();
  jest.resetAllMocks();
});

async function renderAndCheck() {
  await act(async () => {
    root.render(React.createElement(MemoryRouter, null,
      React.createElement(ResearcherDashboard)));
  });
  await act(async () => { await Promise.resolve(); });

  const button = [...container.querySelectorAll('button')]
    .find((b) => b.textContent.includes('Check this extract'));
  expect(button).toBeTruthy();
  await act(async () => {
    button.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
  await act(async () => { await Promise.resolve(); });
  await act(async () => { await Promise.resolve(); });
}

test('a verified release says so', async () => {
  mockApi({
    state: 'verified', verified: true,
    explanation: 'The stored extract still hashes to the digest recorded when it was released.',
  });
  await renderAndCheck();
  expect(container.textContent).toContain('still hashes to the digest');
});

test('a mismatch is not softened', async () => {
  mockApi({
    state: 'mismatch', verified: false,
    explanation: 'The stored extract no longer hashes to the digest recorded when it was released. Any finding citing this release cites bytes that have changed.',
  });
  await renderAndCheck();
  expect(container.textContent).toContain('no longer hashes to the digest');
  expect(container.textContent).toContain('bytes that have changed');
});

test('an unverifiable release does not render as verified', async () => {
  mockApi({
    state: 'unverifiable', verified: false,
    explanation: 'The extract is no longer stored, so this release cannot be checked against its digest. That is not a pass: nobody can confirm the data behind a finding citing it.',
  });
  await renderAndCheck();
  expect(container.textContent).toContain('cannot be checked');
  expect(container.textContent).toContain('That is not a pass');
  expect(container.textContent).not.toContain('still hashes');
});

test('nothing is claimed before the check is run', async () => {
  mockApi({ state: 'verified', verified: true,
            explanation: 'VERDICT-THAT-MUST-NOT-APPEAR-UNASKED' });
  await act(async () => {
    root.render(React.createElement(MemoryRouter, null,
      React.createElement(ResearcherDashboard)));
  });
  await act(async () => { await Promise.resolve(); });
  expect(container.textContent).toContain('Check this extract');
  expect(container.textContent).not.toContain('VERDICT-THAT-MUST-NOT-APPEAR-UNASKED');
});
