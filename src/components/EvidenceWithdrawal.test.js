import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import EvidenceWithdrawal from './EvidenceWithdrawal';
import { apiRequest } from '../lib/api';
jest.mock('../lib/api', () => ({ apiRequest: jest.fn() }));
let root, container;
beforeEach(() => { global.IS_REACT_ACT_ENVIRONMENT = true; container = document.createElement('div'); root = createRoot(container); });
afterEach(() => { act(() => root.unmount()); jest.resetAllMocks(); });
const click = text => [...container.querySelectorAll('button')].find(b => b.textContent === text).click();
function change(el, value) {
  Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value').set.call(el, value);
  el.dispatchEvent(new Event('input', { bubbles:true }));
  el.dispatchEvent(new Event('change', { bubbles:true }));
}
test('withdrawal preserves reference and reason on conflict', async () => {
  apiRequest.mockRejectedValueOnce(new Error('Evidence changed'));
  await act(async () => root.render(<EvidenceWithdrawal item={{id:'e1',status:'verified'}} canWithdraw onSaved={jest.fn()} />));
  act(() => click('Withdraw evidence and open follow-up'));
  act(() => { change(container.querySelector('input'), 'ADMIN-001'); change(container.querySelector('textarea'), 'Institution paused this scope'); });
  await act(async () => container.querySelector('form').dispatchEvent(new Event('submit', { bubbles:true, cancelable:true })));
  expect(apiRequest).toHaveBeenCalledWith('/api/research-evidence/e1/withdraw', expect.objectContaining({body:JSON.stringify({reference:'ADMIN-001',reason:'Institution paused this scope'})}));
  expect(container.querySelector('textarea').value).toBe('Institution paused this scope');
  expect(container.textContent).toContain('Evidence changed');
});
test('closing requires explicit disposition and independent review permission', async () => {
  await act(async () => root.render(<EvidenceWithdrawal item={{id:'e1',status:'withdrawn',can_close_withdrawal:false}} />));
  expect(container.textContent).toContain('Open withdrawal');
  expect(container.querySelector('button')).toBeNull();
  await act(async () => root.render(<EvidenceWithdrawal item={{id:'e1',status:'withdrawn',can_close_withdrawal:true}} />));
  act(() => click('Record reviewed disposition'));
  expect(container.querySelectorAll('select')).toHaveLength(3);
  for (const select of container.querySelectorAll('select')) { expect(select.required).toBe(true); expect(select.value).toBe(''); }
});
