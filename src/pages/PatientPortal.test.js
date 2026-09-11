import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import { MemoryRouter } from 'react-router-dom';
import PatientPortal from './PatientPortal';
import { apiFetch } from '../lib/api';

// The portal loads thirteen independent panels. It used to load them under
// Promise.all, and apiFetch throws on any non-2xx, so a single gated or
// briefly unavailable endpoint rejected the batch and the whole page rendered
// as an error. Someone who had simply not signed one optional consent lost
// their consents, their records, their releases and their contribution record
// along with it.
//
// These hold the line: one panel failing must cost that panel and nothing else.

// loadPanels is the real implementation on purpose: these tests are about
// how the portal composes with it, not about a stand-in that might behave
// differently from the code that ships.
jest.mock('../lib/api', () => ({
  API_URL: '',
  apiFetch: jest.fn(),
  loadPanels: jest.requireActual('../lib/api').loadPanels,
  readSessionUser: () => ({ user_type: 'patient' }),
}));
jest.mock('react-hot-toast', () => ({ __esModule: true, default: jest.fn() }));

let root, container;

const PROFILE = { points_balance: 0, engagement_level: 'new' };

function respond(body) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(body) });
}

/** Every endpoint answers, except the paths listed in `failing`. */
function mockApi({ failing = [], overrides = {} } = {}) {
  apiFetch.mockImplementation((url) => {
    const path = url.replace('', '');
    if (failing.some((fragment) => path.includes(fragment))) {
      const error = new Error('Sign the Clinical Trial Matching consent first');
      error.status = 403;
      return Promise.reject(error);
    }
    for (const [fragment, body] of Object.entries(overrides)) {
      if (path.includes(fragment)) return respond(body);
    }
    if (path.includes('/api/patient/profile')) return respond(PROFILE);
    if (path.includes('/api/patient/data-summary')) return respond({ total_records: 0 });
    if (path.includes('/api/patient/contribution')) return respond({ stages: [], summary: 'x' });
    return respond([]);
  });
}

async function render() {
  await act(async () => {
    root.render(<MemoryRouter><PatientPortal /></MemoryRouter>);
  });
  // Let the settled promises flush.
  await act(async () => { await Promise.resolve(); });
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

test('one gated panel does not take down the portal', async () => {
  mockApi({ failing: ['/api/studies/available'] });
  await render();
  expect(container.textContent).toContain('Your Dashboard');
  expect(container.textContent).not.toContain('Sign the Clinical Trial Matching consent first');
});

test('a panel that fails costs only that panel', async () => {
  mockApi({
    failing: ['/api/studies/available'],
    overrides: { '/api/patient/consents': [{ id: 'c1', status: 'active', consent_type: 'research_data_sharing' }] },
  });
  await render();
  // The rest of the portal still rendered, including data from other panels.
  expect(container.textContent).toContain('Your Dashboard');
});

test('several panels failing still leaves the portal standing', async () => {
  mockApi({
    failing: ['/api/studies/available', '/api/patient/study-results',
              '/api/patient/data-releases', '/api/patient/reconsent'],
  });
  await render();
  expect(container.textContent).toContain('Your Dashboard');
});

test('a missing profile is the one failure that is fatal', async () => {
  // Without it there is no person whose portal this is, and rendering empty
  // panels around nothing would be a lie.
  mockApi({ failing: ['/api/patient/profile'] });
  await render();
  expect(container.textContent).not.toContain('Your Dashboard');
});

test('the re-consent question is shown when a study has changed', async () => {
  mockApi({
    overrides: {
      '/api/patient/reconsent': [{
        study_id: 's1',
        study_name: 'Remission duration in AML',
        changes: ['What the study is trying to find out has changed.'],
        current_purpose: 'A different question',
        current_eligibility: '',
        note: 'Your records are not being used for this study while the question is open.',
      }],
    },
  });
  await render();
  expect(container.textContent).toContain('A study you joined has changed');
  expect(container.textContent).toContain('Remission duration in AML');
  expect(container.textContent).toContain('Stay in this study');
  expect(container.textContent).toContain('Leave this study');
});

test('there is no answer that defers the question', async () => {
  mockApi({
    overrides: {
      '/api/patient/reconsent': [{
        study_id: 's1', study_name: 'S', changes: ['x'],
        current_purpose: '', current_eligibility: '', note: 'n',
      }],
    },
  });
  await render();
  const prompt = container.querySelector('[data-testid="reconsent-prompt"]');
  const labels = [...prompt.querySelectorAll('button')].map((b) => b.textContent);
  expect(labels).toEqual(['Stay in this study', 'Leave this study']);
});

test('no question is shown when nothing has changed', async () => {
  mockApi();
  await render();
  expect(container.querySelector('[data-testid="reconsent-prompt"]')).toBeNull();
});
