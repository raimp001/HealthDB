import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import { MemoryRouter } from 'react-router-dom';
import GuestWorkspace from './GuestWorkspace';

test('guest can declare availability and record work without a server request', async () => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const container = document.createElement('div'); document.body.appendChild(container);
  const root = createRoot(container);
  const originalFetch = window.fetch;
  window.fetch = jest.fn();
  try {
    await act(async () => root.render(<MemoryRouter><GuestWorkspace /></MemoryRouter>));
    const select = container.querySelector('select');
    act(() => { select.value = 'unavailable'; select.dispatchEvent(new Event('change', { bubbles: true })); });
    expect(select.value).toBe('unavailable');
    const form = container.querySelectorAll('form')[1];
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(form.querySelector('input'), 'Reviewed fictional dictionary');
      form.querySelector('input').dispatchEvent(new Event('input', { bubbles: true }));
    });
    act(() => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
    expect(container.querySelector('ol').textContent).toContain('#1 · Submitted · Reviewed fictional dictionary');
    expect(window.fetch).not.toHaveBeenCalled();
  } finally { act(() => root.unmount()); container.remove(); window.fetch = originalFetch; }
});
