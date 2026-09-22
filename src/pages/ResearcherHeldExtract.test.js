/**
 * What a researcher is told when their extract is held.
 *
 * They did everything right — approvals current, cohort pinned, disclosure
 * risk cleared — and the file still does not arrive. If the screen shows a
 * raw status and no explanation, that reads as the platform obstructing
 * them, and a researcher who reads it that way looks for another route to
 * the data. So the status has to be a phrase a person would say, the
 * explanation has to be present, and neither may name what it collided with.
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

const HELD_MESSAGE =
  'This extract is held for disclosure review before it can be released. ' +
  'Releases are compared against earlier ones, because two files that differ ' +
  'by only a few subjects can identify those people to anyone holding both. ' +
  'A reviewer will decide and you will see the outcome here. Nothing is wrong ' +
  'with your study or your approvals, and there is nothing for you to correct.';

const HELD_JOB = {
  id: 'j1',
  job_name: 'extract_relapse_timing_20260919',
  status: 'held_for_review',
  patient_count: 14,
  variable_count: 1,
  output_format: 'csv',
  download_url: null,
  error_message: HELD_MESSAGE,
  created_at: '2026-09-19T00:00:00Z',
};

let root, container;

function mockApi(jobs) {
  apiFetch.mockImplementation((url) => {
    const body =
      url.includes('/api/extraction/jobs') ? jobs
      : url.includes('/api/researcher/studies') ? [{
          id: 's1', name: 'Relapse timing in AML', status: 'active', mine: true,
        }]
      : [];
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

async function render() {
  await act(async () => {
    root.render(React.createElement(MemoryRouter, null,
      React.createElement(ResearcherDashboard)));
  });
  await act(async () => { await Promise.resolve(); });
}

/** Reach the study's extraction list, which is where jobs are shown. */
async function openStudyExtracts() {
  const tab = [...container.querySelectorAll('button')]
    .find((b) => b.textContent.includes('Regulatory Status'));
  expect(tab).toBeTruthy();
  await act(async () => {
    tab.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
  await act(async () => { await Promise.resolve(); });

  const study = [...container.querySelectorAll('button')]
    .find((b) => b.textContent.includes('Relapse timing in AML'));
  expect(study).toBeTruthy();
  await act(async () => {
    study.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
  await act(async () => { await Promise.resolve(); });
  await act(async () => { await Promise.resolve(); });
}

test('a held job shows its explanation and a status a person would say', async () => {
  mockApi([HELD_JOB]);
  await render();
  await openStudyExtracts();

  expect(container.textContent).toContain('Under review');
  expect(container.textContent).not.toContain('held_for_review');
  expect(container.textContent).toContain('held for disclosure review');
  expect(container.textContent).toContain('nothing for you to correct');
});

test('what a held job shows names no other cohort', async () => {
  mockApi([HELD_JOB]);
  await render();
  await openStudyExtracts();

  const shown = container.textContent.slice(
    container.textContent.indexOf('held for disclosure review'));
  const explanation = shown.slice(0, HELD_MESSAGE.length);
  for (const digit of '0123456789') {
    expect(explanation).not.toContain(digit);
  }
});

test('a held job offers no download', async () => {
  mockApi([HELD_JOB]);
  await render();
  await openStudyExtracts();
  expect(container.textContent).not.toContain('Download CSV');
});

test('a completed job still offers its download', async () => {
  mockApi([{ ...HELD_JOB, status: 'completed', error_message: null,
             download_url: '/api/extraction/jobs/j1/download' }]);
  await render();
  await openStudyExtracts();
  expect(container.textContent).toContain('Download CSV');
});
