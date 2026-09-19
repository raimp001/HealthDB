/**
 * When an upload refuses part of someone's file, the screen has to show them
 * which part.
 *
 * The response message says entries were "not stored ... details below". If
 * the modal closes on success, there is no below, and the person is told
 * something went wrong about their own medical history with no way to find
 * out what. These tests hold that promise to the contributor.
 */
process.env.REACT_APP_ENABLE_SYNTHETIC_FHIR_UPLOADS = 'true';

const React = require('react');
const { createRoot } = require('react-dom/client');
const { act } = require('react-dom/test-utils');
const { MemoryRouter } = require('react-router-dom');

jest.mock('../lib/api', () => ({
  API_URL: '',
  apiFetch: jest.fn(),
  loadPanels: jest.requireActual('../lib/api').loadPanels,
  readSessionUser: () => ({ user_type: 'patient' }),
}));
jest.mock('react-hot-toast', () => ({ __esModule: true, default: jest.fn() }));

// framer-motion's exit animations never settle under jsdom, so the outgoing
// panel stays mounted and the test reads the previous tab. Rendering plain
// elements keeps these tests about what the page says, not how it moves.
jest.mock('framer-motion', () => {
  const ReactLib = require('react');
  const strip = ({ children, ...props }) => {
    ['initial', 'animate', 'exit', 'transition', 'variants', 'whileHover',
     'whileTap', 'whileInView', 'viewport', 'layout', 'layoutId']
      .forEach((key) => delete props[key]);
    return [children, props];
  };
  const motion = new Proxy({}, {
    get: (_, tag) => ({ children, ...rest }) => {
      const [kids, props] = strip({ children, ...rest });
      return ReactLib.createElement(typeof tag === 'string' ? tag : 'div', props, kids);
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
const PatientPortal = require('./PatientPortal').default;

let root, container;

/**
 * Enough of the portal to reach the import modal — an active research consent
 * — plus whatever the upload endpoint should answer.
 *
 * The portal imports apiFetch under the name `fetch`, so the upload goes
 * through the same mock as every panel.
 */
function mockApi(uploadBody) {
  apiFetch.mockImplementation((url) => {
    const body =
      url.includes('/api/patient/connections/fhir') ? uploadBody
      : url.includes('/api/patient/profile') ? { points_balance: 0, engagement_level: 'new' }
      : url.includes('/api/patient/data-summary') ? { total_records: 0 }
      : url.includes('/api/patient/contribution') ? { stages: [], summary: 'x' }
      : url.includes('/api/patient/consents')
        ? [{ id: 'c1', status: 'active', consent_type: 'research_data_sharing' }]
      : [];
    return Promise.resolve({ ok: true, json: () => Promise.resolve(body) });
  });
}

function findByText(selector, text) {
  return [...container.querySelectorAll(selector)]
    .find((node) => node.textContent.includes(text));
}

async function openModalAndUpload() {
  await act(async () => {
    root.render(React.createElement(MemoryRouter, null,
      React.createElement(PatientPortal)));
  });
  await act(async () => { await Promise.resolve(); });

  // The import lives on the records tab.
  const toData = findByText('button', 'Test Data');
  expect(toData).toBeTruthy();
  await act(async () => {
    toData.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });

  await act(async () => { await Promise.resolve(); });
  const open = findByText('button', 'Import Test Bundle');
  expect(open).toBeTruthy();
  await act(async () => {
    open.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });

  const input = container.querySelector('input[type="file"]');
  expect(input).toBeTruthy();

  // jsdom's File has no text(); the handler only needs text() and name.
  const file = { name: 'bundle.json', text: () => Promise.resolve('{}') };
  Object.defineProperty(input, 'files', { value: [file], configurable: true });
  await act(async () => {
    input.dispatchEvent(new Event('change', { bubbles: true }));
  });
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

test('a refused entry is named on screen, not just counted in a toast', async () => {
  mockApi({
    success: true,
    records_imported: 1,
    records_rejected: 1,
    message: '1 entry was not stored because the values could not be true; details below.',
    rejections: [{
      category: 'diagnosis',
      type: 'condition',
      year: 1782,
      reason: 'The year on this entry (1782) is earlier than this platform can treat as a real clinical date.',
    }],
  });
  await openModalAndUpload();

  expect(container.textContent).toContain('1782');
  expect(container.textContent).toContain('One entry was not stored');
  // And it says the rest went through, so nobody assumes the upload failed.
  expect(container.textContent).toContain('The rest of your file was imported');
});

test('a clean upload closes the modal and says nothing about rejections', async () => {
  mockApi({
    success: true,
    records_imported: 2,
    records_rejected: 0,
    message: 'Successfully imported 2 synthetic test records.',
    rejections: [],
  });
  await openModalAndUpload();

  // The upload really ran — openModalAndUpload asserts the modal was open and
  // this proves the response was handled — and then the modal closed.
  expect(require('react-hot-toast').default)
    .toHaveBeenCalledWith('Successfully imported 2 synthetic test records.');
  expect(container.querySelector('input[type="file"]')).toBeNull();
  expect(container.textContent).not.toContain('was not stored');
});
