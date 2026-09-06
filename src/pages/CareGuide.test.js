import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import { MemoryRouter } from 'react-router-dom';
import CareGuide, { planText } from './CareGuide';
import catalog from '../data/careGuides.json';

test('checklists stay separate by topic and can be completely cleared', () => {
  const element = document.createElement('div');
  document.body.appendChild(element);
  const root = createRoot(element);
  act(() => root.render(<MemoryRouter><CareGuide /></MemoryRouter>));
  const button = text => [...element.querySelectorAll('button')].find(b => b.textContent === text);
  act(() => element.querySelector('input').click());
  expect(element.querySelector('progress').value).toBe(1);
  act(() => button('Blood pressure screening').click());
  expect(element.querySelector('progress').value).toBe(0);
  act(() => button('Breast cancer screening').click());
  expect(element.querySelector('input').checked).toBe(true);
  act(() => button('Clear all progress').click());
  expect(element.querySelector('progress').value).toBe(0);
  expect(element.textContent).not.toContain('Your checklist is complete');
  act(() => root.unmount());
  element.remove();
});

test('export keeps clinical boundaries and sources with self-reported progress', () => {
  const text = planText(catalog.guides[0], [0]);
  expect(text).toContain('not a personalized recommendation');
  expect(text).toContain(catalog.guides[0].source);
  expect(text).toContain('[x] Discuss');
  expect(text).toContain('[ ] Contact');
  expect(text).toContain('not a clinical record');
  expect(text).toContain('HealthDB does not monitor symptoms or results');
});
