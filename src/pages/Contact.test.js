import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import { MemoryRouter } from 'react-router-dom';
import Contact from './Contact';
import { apiFetch } from '../lib/api';

jest.mock('../lib/api', () => ({ API_URL: '', apiFetch: jest.fn() }));
let root, container;
beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => { act(() => root.unmount()); container.remove(); jest.resetAllMocks(); });

test('failed submission keeps the draft and explains the actual failure', async () => {
  apiFetch.mockRejectedValueOnce(new Error('Too many requests. Please wait a moment and try again.'));
  await act(async () => root.render(<MemoryRouter><Contact /></MemoryRouter>));
  const message = container.querySelector('textarea');
  act(() => {
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(message, 'Synthetic pilot evaluation request');
    message.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await act(async () => container.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  expect(container.querySelector('[role="alert"]').textContent).toContain('Too many requests');
  expect(message.value).toBe('Synthetic pilot evaluation request');
  expect(container.querySelector('button').disabled).toBe(false);
});
