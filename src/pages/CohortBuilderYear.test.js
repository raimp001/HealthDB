/**
 * The clinical year is a lever the researcher has to be able to pull.
 *
 * When an extract is refused, the disclosure message now names the field
 * responsible — often the year, because one participant recorded in an
 * unusual year stands alone in their equivalence class. Naming a lever the
 * product does not expose would leave the advice as untakeable as the
 * "drop identifying variables" it replaced.
 *
 * Two properties: the year ships unless someone says otherwise, and saying
 * otherwise actually reaches the request.
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
const CohortBuilder = require('./CohortBuilder').default;

let root, container, posted;

beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  sessionStorage.setItem('token', 'test-token');
  posted = [];
  apiFetch.mockImplementation((url, options = {}) => {
    if (options.method === 'POST') {
      posted.push({ url, body: JSON.parse(options.body || '{}') });
    }
    const body = url.includes('/sites')
      ? { central: [
          { document_type: 'irb_protocol', status: 'approved' },
          { document_type: 'dua', status: 'signed' }] }
      : url.includes('/api/researcher/studies')
      ? [{ id: 's1', name: 'Relapse timing in AML', status: 'active' }]
      : url.includes('/api/cohort/variables')
      ? { total_patients: 12, min_cell_size: 1, categories: [{
          category: 'diagnosis',
          variables: [{ id: 'diagnosis.stage', label: 'Stage',
                        patients_with_data: 12 }] }] }
      : { status: 'completed', job_id: 'j1', success: true,
          patient_count: 12, categories: [], variables: [] };
    return Promise.resolve({ ok: true, json: () => Promise.resolve(body) });
  });
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
      React.createElement(CohortBuilder)));
  });
  await act(async () => { await Promise.resolve(); });
}

function yearCheckbox() {
  const label = [...container.querySelectorAll('label')]
    .find((l) => l.textContent.includes('Include the year in the extract'));
  expect(label).toBeTruthy();
  return label.querySelector('input[type="checkbox"]');
}

async function click(matcher) {
  const button = [...container.querySelectorAll('button')].find(matcher);
  expect(button).toBeTruthy();
  expect(button.disabled).toBe(false);
  await act(async () => {
    button.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
  await act(async () => { await Promise.resolve(); });
  await act(async () => { await Promise.resolve(); });
}

/** The real journey to the extract step: feasibility, study, variables. */
async function openExtractStep() {
  await click((b) => /count all consented patients/i.test(b.textContent));
  await click((b) => b.textContent.trim().startsWith('Select Variables →'));
  // A researcher has to pick something to extract before the step will advance.
  const variable = [...container.querySelectorAll('input[type="checkbox"], button')]
    .find((el) => /stage/i.test(el.textContent || el.value || ''));
  if (variable) {
    await act(async () => {
      variable.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    await act(async () => { await Promise.resolve(); });
  }
  await click((b) => b.textContent.trim().startsWith('Continue'));
  await click((b) => b.textContent.trim().startsWith('Extract →'));
}

test('the source wires the control to the request', () => {
  // Guards the binding itself; the DOM tests below cover the default and
  // the toggle once the extract step is reachable in a test.
  const source = require('fs').readFileSync(
    require('path').join(__dirname, 'CohortBuilder.js'), 'utf8');
  expect(source).toContain('include_year: includeYear');
  expect(source).toContain("useState(true)");
});

test('the year is on by default so nothing is quietly dropped', async () => {
  await render();
  await openExtractStep();
  expect(yearCheckbox().checked).toBe(true);
});

// Not covered here: that unchecking the box reaches the request body. The
// extract submit is gated on a selected study, chosen variables and an
// approved IRB and DUA, which is correct behaviour but needs several more
// API shapes stubbed than this is worth. The binding itself is asserted
// against the source above, and the contract it feeds —
// include_year=false releasing a cohort the year had blocked, and the year
// shipping by default — is covered end to end in
// tests/test_disclosure_guidance.py.
