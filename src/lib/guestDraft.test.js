import { parseGuestDraft } from './guestDraft';

const draft = () => ({ mode: 'guest_demo', synthetic_only: true, title: 'Fictional study', question: 'Example question', variables: [{ id: 1, name: 'Response', a: 'available', b: 'unknown', c: 'derivable' }], reviews: {}, reviewHistory: [], events: [] });

test('previous exports round-trip and unexpected fields are not restored', () => {
  const data = draft(); data.unexpected = 'ignored';
  expect(parseGuestDraft(JSON.stringify(data))).toEqual({ title: data.title, question: data.question, variables: data.variables, reviews: {}, reviewHistory: [], events: [] });
});

test.each([
  data => { data.synthetic_only = false; },
  data => { data.variables[0].a = 'verified'; },
  data => { data.variables.push({ ...data.variables[0] }); },
  data => { data.reviews['99:a'] = { mapping: '', owner: '', nextAction: '', status: 'draft' }; },
  data => { data.reviews['1:a'] = { mapping: '', owner: '', nextAction: '', status: 'reviewed' }; },
  data => { data.events = [{ sequence: 3, action: 'Submitted', description: 'Work', at: 'bad' }]; },
  data => { data.schema_version = 999; },
])('rejects malformed drafts without restoring partial data', mutate => {
  const data = draft(); mutate(data);
  expect(() => parseGuestDraft(JSON.stringify(data))).toThrow();
});

test('rejects oversized and invalid JSON', () => {
  expect(() => parseGuestDraft('a'.repeat(1000001))).toThrow('under 1 MB');
  expect(() => parseGuestDraft('{')).toThrow('valid JSON');
});
