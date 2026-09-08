import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import WorkLedger from './WorkLedger';
import { apiRequest } from '../lib/api';
jest.mock('../lib/api', () => ({ apiRequest: jest.fn() }));
let root, container;
beforeEach(() => { global.IS_REACT_ACT_ENVIRONMENT = true; container = document.createElement('div'); root = createRoot(container); });
afterEach(() => { act(() => root.unmount()); jest.resetAllMocks(); });
const entry = { id: 'e1', title: 'Dictionary review', description: 'Reviewed definitions', evidence_ref: 'Plan 1', minutes: 60, revision: 1, status: 'submitted', mine: false, can_review: true, events: [] };
test('review sends the displayed revision and preserves reason on conflict', async () => {
  apiRequest.mockImplementation((path, opts) => opts.method ? Promise.reject(new Error('Reload before acting')) : Promise.resolve({ items: [entry] }));
  await act(async () => root.render(<WorkLedger studyId="s1" />));
  await act(async () => [...container.querySelectorAll('button')].find(b => b.textContent === 'Accept work').click());
  const reason = container.querySelector('textarea');
  await act(async () => { Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(reason, 'Reviewed against protocol'); reason.dispatchEvent(new Event('input', { bubbles: true })); });
  await act(async () => reason.closest('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  expect(container.textContent).toContain('Reload before acting');
  expect(reason.value).toBe('Reviewed against protocol');
  expect(JSON.parse(apiRequest.mock.calls.at(-1)[1].body).revision).toBe(1);
});
test('contributors cannot see self-approval controls', async () => {
  apiRequest.mockResolvedValue({ items: [{ ...entry, mine: true, can_review: false }] });
  await act(async () => root.render(<WorkLedger studyId="s1" />));
  expect(container.textContent).not.toContain('Accept work');
  expect(container.textContent).toContain('does not approve a payment');
});
