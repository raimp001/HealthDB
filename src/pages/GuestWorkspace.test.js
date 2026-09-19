import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import { MemoryRouter } from 'react-router-dom';
import GuestWorkspace from './GuestWorkspace';
import { GUEST_DRAFT_KEY } from '../lib/guestDraft';
import { SAVED_PLANS_KEY } from '../lib/savedGuestPlans';

beforeEach(() => {
  sessionStorage.clear(); localStorage.clear();
  let id = 0;
  Object.defineProperty(window, 'crypto', { configurable: true, value: { randomUUID: () => `test-copy-${++id}` } });
});

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
    act(() => reviewButton.click());
    const question = container.querySelector('section textarea');
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(question, 'A revised synthetic question');
      question.dispatchEvent(new Event('input', { bubbles: true }));
    });
    expect(container.querySelector('details summary').textContent).toContain('Needs review');
    expect(JSON.parse(sessionStorage.getItem(GUEST_DRAFT_KEY)).question).toBe('A revised synthetic question');
    expect(container.querySelector('[aria-label="Availability summary"]').textContent).toContain('Need assessment1');
    expect(window.fetch).not.toHaveBeenCalled();
  } finally { act(() => root.unmount()); container.remove(); window.fetch = originalFetch; }
});

test('navigation restores work and draft reopening is validated before replacement', async () => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const container = document.createElement('div'); document.body.appendChild(container);
  const root = createRoot(container);
  const render = () => root.render(<MemoryRouter><GuestWorkspace /></MemoryRouter>);
  const button = name => Array.from(container.querySelectorAll('button')).find(b => b.textContent === name);
  const fillImport = value => act(() => {
    const field = container.querySelector('#guest-import');
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(field, value);
    field.dispatchEvent(new Event('input', { bubbles: true }));
  });
  try {
    await act(async () => render());
    act(() => container.querySelector('[aria-label="Remove Treatment class"]').click());
    act(() => root.render(null));
    await act(async () => render());
    expect(container.querySelectorAll('tbody tr')).toHaveLength(1);
    const saved = sessionStorage.getItem(GUEST_DRAFT_KEY);
    fillImport('{'); act(() => button('Check draft').click());
    expect(container.querySelector('[role="alert"]').textContent).toContain('valid JSON');
    expect(sessionStorage.getItem(GUEST_DRAFT_KEY)).toBe(saved);
    const imported = JSON.parse(saved); imported.title = 'Reopened synthetic study';
    fillImport(JSON.stringify(imported)); act(() => button('Check draft').click());
    expect(JSON.parse(sessionStorage.getItem(GUEST_DRAFT_KEY)).title).not.toBe(imported.title);
    act(() => button('Replace current plan with this draft').click());
    expect(JSON.parse(sessionStorage.getItem(GUEST_DRAFT_KEY)).title).toBe(imported.title);
  } finally { act(() => root.unmount()); container.remove(); }
});

test('explicit device save retains the complete plan across a new tab session and reopening requires confirmation', async () => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const container = document.createElement('div'); document.body.appendChild(container);
  const root = createRoot(container);
  const render = () => root.render(<MemoryRouter><GuestWorkspace /></MemoryRouter>);
  const button = name => Array.from(container.querySelectorAll('button')).find(b => b.textContent === name);
  const review = { mapping: 'Synthetic categories', owner: 'Methods reviewer', nextAction: 'Check missing values', status: 'reviewed' };
  const saved = { schema_version: 1, mode: 'guest_demo', synthetic_only: true, title: 'Return visit study', question: 'Synthetic question', variables: [{ id: 1, name: 'Response', a: 'available', b: 'unknown', c: 'derivable' }], reviews: { '1:a': review }, reviewHistory: [{ ...review, sequence: 1, key: '1:a', label: 'Response — site A', availability: 'available', title: 'Return visit study', question: 'Synthetic question', at: '2026-09-19T12:00:00Z' }], events: [{ sequence: 1, action: 'Submitted', description: 'Defined categories', at: '2026-09-19T12:00:00Z' }] };
  sessionStorage.setItem(GUEST_DRAFT_KEY, JSON.stringify(saved));
  try {
    await act(async () => render());
    expect(localStorage.getItem(SAVED_PLANS_KEY)).toBeNull();
    act(() => button('Save a copy on this device').click());
    expect(container.textContent).toContain('Copy saved on this device');
    act(() => root.render(null)); sessionStorage.clear();
    await act(async () => render());
    const initial = sessionStorage.getItem(GUEST_DRAFT_KEY);
    expect(JSON.parse(initial).title).not.toBe(saved.title);
    act(() => button('Preview and reopen').click());
    expect(container.querySelector('[aria-label="Saved copy preview"]').textContent).toContain('1 variables · 1 review snapshots · 1 contributions');
    expect(sessionStorage.getItem(GUEST_DRAFT_KEY)).toBe(initial);
    act(() => button('Cancel reopening').click());
    expect(sessionStorage.getItem(GUEST_DRAFT_KEY)).toBe(initial);
    act(() => button('Preview and reopen').click());
    act(() => button('Replace open plan with saved copy').click());
    expect(JSON.parse(sessionStorage.getItem(GUEST_DRAFT_KEY))).toEqual(saved);
    act(() => button('Remove copy').click());
    expect(JSON.parse(localStorage.getItem(SAVED_PLANS_KEY)).plans).toHaveLength(1);
    act(() => button('Confirm removal').click());
    expect(JSON.parse(localStorage.getItem(SAVED_PLANS_KEY)).plans).toHaveLength(0);
    expect(JSON.parse(sessionStorage.getItem(GUEST_DRAFT_KEY))).toEqual(saved);
  } finally { act(() => root.unmount()); container.remove(); }
});

test('blocked device storage shows a recovery action and keeps the current plan editable', async () => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const container = document.createElement('div'); document.body.appendChild(container);
  const root = createRoot(container);
  try {
    await act(async () => root.render(<MemoryRouter><GuestWorkspace /></MemoryRouter>));
    const saved = sessionStorage.getItem(GUEST_DRAFT_KEY);
    const set = jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('QuotaExceededError'); });
    try { act(() => Array.from(container.querySelectorAll('button')).find(b => b.textContent === 'Save a copy on this device').click()); }
    finally { set.mockRestore(); }
    expect(container.querySelector('[role="alert"]').textContent).toContain('Download or copy your draft instead');
    expect(sessionStorage.getItem(GUEST_DRAFT_KEY)).toBe(saved);
    expect(localStorage.getItem(SAVED_PLANS_KEY)).toBeNull();
  } finally { act(() => root.unmount()); container.remove(); }
});
