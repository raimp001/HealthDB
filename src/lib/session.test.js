import { destinationFor, readStoredUser, saveUser, clearSession } from './session';

afterEach(() => sessionStorage.clear());

test('returns a researcher to the requested cohort workflow', () => {
  expect(destinationFor({ user_type: 'researcher' }, '/cohort-builder?study=one')).toBe('/cohort-builder?study=one');
});

test.each(['https://example.com', '//example.com', '/patient', '/cohort-builder-other'])(
  'rejects external and unauthorized destinations: %s', path => {
    expect(destinationFor({ user_type: 'researcher' }, path)).toBe('/research');
  }
);

test('handles malformed storage and removes session data on sign out', () => {
  sessionStorage.setItem('token', 'test');
  sessionStorage.setItem('user', '{invalid');
  expect(readStoredUser()).toBeNull();
  saveUser({ id: 'one', user_type: 'patient', name: 'Test', email: 'private@example.com' });
  expect(readStoredUser()).toEqual({ id: 'one', user_type: 'patient', name: 'Test' });
  clearSession();
  expect(readStoredUser()).toBeNull();
  expect(sessionStorage.getItem('token')).toBeNull();
});
