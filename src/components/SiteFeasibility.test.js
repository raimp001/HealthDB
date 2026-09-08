import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import SiteFeasibility from './SiteFeasibility';
import { apiRequest } from '../lib/api';
jest.mock('../lib/api', () => ({ apiRequest: jest.fn() }));
let root, container;
const data = { plan_revision: 1, variables: [{ name: 'stage', definition: 'Stage at diagnosis' }], declarations: [] };
beforeEach(() => { global.IS_REACT_ACT_ENVIRONMENT = true; container = document.createElement('div'); root = createRoot(container); });
afterEach(() => { act(() => root.unmount()); jest.resetAllMocks(); });
test('save conflict preserves the declaration draft', async () => {
  apiRequest.mockImplementation((path, options) => options?.method === 'PUT' ? Promise.reject(new Error('Reload before saving')) : Promise.resolve(data));
  await act(async () => root.render(<SiteFeasibility studyId="s1" planRevision={1} planDirty={false} />));
  const site = container.querySelector('input');
  await act(async () => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(site, 'Pilot site'); site.dispatchEvent(new Event('input', { bubbles: true })); });
  await act(async () => container.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  expect(container.textContent).toContain('Reload before saving');
  expect(site.value).toBe('Pilot site');
});
test('unsaved or changed plan disables mapping edits', async () => {
  apiRequest.mockResolvedValue(data);
  await act(async () => root.render(<SiteFeasibility studyId="s1" planRevision={1} planDirty />));
  expect(container.querySelector('fieldset').disabled).toBe(true);
  await act(async () => root.render(<SiteFeasibility studyId="s1" planRevision={2} planDirty={false} />));
  expect(container.querySelector('fieldset').disabled).toBe(true);
  expect(container.textContent).toContain('check every mapping');
});
