import { MAX_SAVED_PLANS, SAVED_PLANS_KEY, readSavedPlans, removePlanCopy, savePlanCopy } from './savedGuestPlans';

const draft = JSON.stringify({ schema_version: 1, mode: 'guest_demo', synthetic_only: true, title: 'Fictional study', question: 'Example question', variables: [], reviews: {}, reviewHistory: [], events: [] });
beforeEach(() => {
  localStorage.clear();
  let id = 0;
  Object.defineProperty(window, 'crypto', { configurable: true, value: { randomUUID: () => `test-copy-${++id}` } });
});

test('saved copies survive the tab session and mutations preserve other copies', () => {
  const first = savePlanCopy(draft)[0];
  sessionStorage.clear();
  expect(readSavedPlans()[0].plan.title).toBe('Fictional study');
  const second = savePlanCopy(draft)[0];
  expect(second.id).not.toBe(first.id);
  expect(removePlanCopy(first.id).map(item => item.id)).toEqual([second.id]);
  expect(readSavedPlans()).toHaveLength(1);
});

test('corrupted storage and invalid drafts are never overwritten by a save or removal', () => {
  localStorage.setItem(SAVED_PLANS_KEY, '{');
  expect(() => savePlanCopy(draft)).toThrow();
  expect(() => removePlanCopy('missing')).toThrow();
  expect(localStorage.getItem(SAVED_PLANS_KEY)).toBe('{');
  localStorage.clear(); savePlanCopy(draft);
  const previous = localStorage.getItem(SAVED_PLANS_KEY);
  expect(() => savePlanCopy('{')).toThrow();
  expect(localStorage.getItem(SAVED_PLANS_KEY)).toBe(previous);
});

test('capacity and quota failures preserve existing copies', () => {
  for (let i = 0; i < MAX_SAVED_PLANS; i++) savePlanCopy(draft);
  const previous = localStorage.getItem(SAVED_PLANS_KEY);
  expect(() => savePlanCopy(draft)).toThrow('10 saved copies');
  expect(localStorage.getItem(SAVED_PLANS_KEY)).toBe(previous);
  removePlanCopy(readSavedPlans()[0].id);
  const remaining = localStorage.getItem(SAVED_PLANS_KEY);
  const set = jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('QuotaExceededError'); });
  try { expect(() => savePlanCopy(draft)).toThrow('QuotaExceededError'); }
  finally { set.mockRestore(); }
  expect(localStorage.getItem(SAVED_PLANS_KEY)).toBe(remaining);
});
