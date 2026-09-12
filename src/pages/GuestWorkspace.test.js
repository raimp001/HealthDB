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
    const remove = container.querySelector('[aria-label="Remove Treatment class"]');
    act(() => remove.click());
    expect(container.querySelectorAll('tbody tr')).toHaveLength(1);
    const preview = Array.from(container.querySelectorAll('button')).find(button => button.textContent === 'Preview draft');
    act(() => preview.click());
    const exported = JSON.parse(container.querySelector('#guest-draft textarea').value);
    expect(exported.variables.map(item => item.name)).toEqual(['Response category']);
    expect(exported.events[0].description).toBe('Reviewed fictional dictionary');
    expect(exported.synthetic_only).toBe(true);
    const mapping = container.querySelector('details textarea');
    const owner = container.querySelector('details select');
    const nextAction = container.querySelector('details input');
    const reviewButton = container.querySelector('details button');
    expect(reviewButton.disabled).toBe(true);
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(mapping, 'Map local response codes to the shared categories');
      mapping.dispatchEvent(new Event('input', { bubbles: true }));
    });
    act(() => { owner.value = 'Methods reviewer'; owner.dispatchEvent(new Event('change', { bubbles: true })); });
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(nextAction, 'Validate missing categories');
      nextAction.dispatchEvent(new Event('input', { bubbles: true }));
    });
    act(() => reviewButton.click());
    expect(container.querySelector('details summary').textContent).toContain('Demo reviewed');
    const availability = container.querySelector('tbody select');
    act(() => { availability.value = 'unknown'; availability.dispatchEvent(new Event('change', { bubbles: true })); });
    expect(container.querySelector('details summary').textContent).toContain('Needs review');
    const revised = JSON.parse(container.querySelector('#guest-draft textarea').value);
    expect(revised.reviewHistory).toHaveLength(1);
    expect(revised.reviewHistory[0].mapping).toContain('local response codes');
    expect(revised.variables[0].c).toBe('unavailable');
    expect(revised.reviews['2:a'].status).toBe('draft');
    expect(container.querySelector('[aria-label="Availability summary"]').textContent).toContain('Need assessment1');
    expect(window.fetch).not.toHaveBeenCalled();
  } finally { act(() => root.unmount()); container.remove(); window.fetch = originalFetch; }
});
