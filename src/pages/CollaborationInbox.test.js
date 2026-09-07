import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import { MemoryRouter } from 'react-router-dom';
import CollaborationInbox from './CollaborationInbox';
import { apiRequest } from '../lib/api';

jest.mock('../lib/api', () => ({ apiRequest: jest.fn() }));
let container, root;
beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  container = document.createElement('div');
  root = createRoot(container);
});
afterEach(() => { act(() => root.unmount()); jest.resetAllMocks(); sessionStorage.clear(); });
const render = async () => act(async () => { root.render(<MemoryRouter><CollaborationInbox /></MemoryRouter>); });

test('loads authenticated invitations and accepts explicitly', async () => {
  sessionStorage.setItem('token', 'test-token');
  apiRequest.mockResolvedValueOnce([{ id: '1', study_name: 'Synthetic study', role: 'analyst' }])
    .mockResolvedValueOnce([]).mockResolvedValueOnce({ status: 'accepted' })
    .mockResolvedValueOnce([]).mockResolvedValueOnce([]);
  await render();
  const accept = Array.from(container.querySelectorAll('button')).find(button => button.textContent === 'Accept invitation');
  await act(async () => { accept.click(); });
  expect(apiRequest).toHaveBeenCalledWith('/api/researcher/invitations/1/respond?decision=accept', {
    method: 'POST', headers: { Authorization: 'Bearer test-token' },
  });
  expect(container.textContent).toContain('No pending invitations');
});

test('offers retry when loading fails', async () => {
  apiRequest.mockRejectedValue(new Error('Could not connect'));
  await render();
  expect(container.querySelector('[role="alert"]').textContent).toContain('Could not connect');
  expect(container.querySelector('button').disabled).toBe(false);
});
