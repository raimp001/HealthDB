import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import { MemoryRouter } from 'react-router-dom';
import ResearchProjects from './ResearchProjects';
import { apiRequest } from '../lib/api';
jest.mock('../lib/api', () => ({ apiRequest: jest.fn(), readSessionUser: () => ({ user_type: 'researcher' }) }));
let root, container;
const report = { id: 's1', name: 'Study one', revision: 1, listed: false, can_edit: true, plan: { question: 'Original question', population: '', exposure: '', outcome: '', analysis: '', impact: '', seeking: '', variables: [], milestones: [] } };
beforeEach(() => { global.IS_REACT_ACT_ENVIRONMENT = true; container = document.createElement('div'); root = createRoot(container); });
afterEach(() => { act(() => root.unmount()); jest.resetAllMocks(); });
function mocks(data = report) {
  apiRequest.mockImplementation((path, options) => {
    if (options?.method === 'PUT') return Promise.reject(new Error('The plan changed. Reload before saving.'));
    if (path === '/api/workspace/projects/s1') return Promise.resolve(data);
    if (path === '/api/workspace/opportunities') return Promise.resolve({ items: [], has_more: false });
    return Promise.resolve([]);
  });
}
test('conflicting save preserves user edits and blocks stale downloads', async () => {
  mocks();
  await act(async () => { root.render(<MemoryRouter initialEntries={['/projects?study=s1']}><ResearchProjects /></MemoryRouter>); });
  const question = [...container.querySelectorAll('textarea')][0];
  await act(async () => { Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(question, 'Revised research question'); question.dispatchEvent(new Event('input', { bubbles: true })); });
  const save = [...container.querySelectorAll('button')].find(b => b.textContent === 'Save plan');
  await act(async () => { save.closest('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
  expect(container.textContent).toContain('The plan changed');
  expect(question.value).toBe('Revised research question');
  expect([...container.querySelectorAll('button')].find(b => b.textContent === 'Download plan JSON').disabled).toBe(true);
});
test('accepted collaborators see a read-only plan and discussion', async () => {
  mocks({ ...report, can_edit: false });
  await act(async () => { root.render(<MemoryRouter initialEntries={['/projects?study=s1']}><ResearchProjects /></MemoryRouter>); });
  expect(container.querySelector('fieldset').disabled).toBe(true);
  expect(container.textContent).not.toContain('Save plan');
  expect(container.textContent).toContain('Post update');
});
