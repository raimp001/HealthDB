import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import { MemoryRouter } from 'react-router-dom';
import ResearchReadiness from './ResearchReadiness';
import { apiRequest } from '../lib/api';
jest.mock('../lib/api', () => ({ apiRequest: jest.fn() }));
let root, container;
beforeEach(() => { global.IS_REACT_ACT_ENVIRONMENT = true; container = document.createElement('div'); root = createRoot(container); });
afterEach(() => { act(() => root.unmount()); jest.resetAllMocks(); });
test('admin can review evidence without seeing owner submission form', async () => {
  const report = { notice: 'Live data disabled', evidence_complete: false, complete_scopes: [], requirements: [], can_review: true, can_submit: false,
    evidence: [{ id: 'e1', category: 'data_license', status: 'submitted', reference: 'REF', scope: 'dataset-v1', expires_at: '2099-01-01T00:00:00Z', sha256: 'a'.repeat(64), review_history: [] }] };
  apiRequest.mockResolvedValueOnce(report).mockResolvedValueOnce({status:'verified'}).mockResolvedValueOnce({...report, evidence:[]});
  await act(async () => { root.render(<MemoryRouter initialEntries={['/research-readiness?study=s1']}><ResearchReadiness /></MemoryRouter>); });
  await act(async () => { container.querySelector('form').dispatchEvent(new Event('submit', { bubbles:true, cancelable:true })); });
  expect(container.textContent).toContain('Live data disabled');
  expect(container.textContent).not.toContain('Submit an evidence reference');
  const verify = [...container.querySelectorAll('button')].find(b => b.textContent === 'Verify reviewed evidence');
  await act(async () => { verify.click(); });
  expect(apiRequest).toHaveBeenCalledWith('/api/research-evidence/e1/review', expect.objectContaining({method:'POST', body:'{"decision":"verified"}'}));
});
