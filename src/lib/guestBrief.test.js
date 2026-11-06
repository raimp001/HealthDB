import { buildGuestBrief, planningChecklist, readGuestDraftFile } from './guestBrief';

const plan = () => ({
  schema_version: 1, mode: 'guest_demo', synthetic_only: true,
  title: 'Fictional outcomes study', question: 'Which fields need assessment?',
  variables: [{ id: 1, name: 'Treatment', a: 'available', b: 'unknown', c: 'unavailable' }],
  reviews: { '1:a': { mapping: 'Local categories', owner: 'Methods reviewer', nextAction: 'Check definitions', status: 'reviewed' } },
  reviewHistory: [], events: [{ sequence: 1, action: 'Submitted', description: 'Defined the variable', at: '2026-11-06T12:00:00Z' }],
});

test('checklist tracks work, including missing and reset reviews, without claiming feasibility', () => {
  const draft = plan();
  expect(planningChecklist(draft).map(step => step.complete)).toEqual([true, false, false]);
  draft.variables[0].b = 'unavailable';
  draft.reviews['1:b'] = { ...draft.reviews['1:a'] };
  draft.reviews['1:c'] = { ...draft.reviews['1:a'] };
  expect(planningChecklist(draft).map(step => step.complete)).toEqual([true, true, true]);
  draft.reviews['1:a'].status = 'draft';
  expect(planningChecklist(draft)[2].complete).toBe(false);
  draft.title = ' '; draft.variables = [];
  expect(planningChecklist(draft).map(step => step.complete)).toEqual([false, false, false]);
});

test('readable brief preserves current mappings, gaps, next actions and contribution history', () => {
  const text = buildGuestBrief(JSON.stringify(plan()));
  expect(text).toContain('Fictional outcomes study');
  expect(text).toContain('Fictional site B: unknown · Needs review');
  expect(text).toContain('Fictional site C: unavailable');
  expect(text).toContain('Mapping: Local categories');
  expect(text).toContain('Next action: Check definitions');
  expect(text).toContain('Defined the variable');
  expect(text).toContain('does not establish study feasibility or approval');
  expect(() => buildGuestBrief('{')).toThrow('valid JSON');
});

test('local file import validates downloaded drafts and rejects invalid, oversized or non-demo files', async () => {
  const raw = JSON.stringify(plan());
  const result = await readGuestDraftFile(new File([raw], 'study.json', { type: 'application/json' }));
  expect(result.raw).toBe(raw);
  expect(result.plan.title).toBe(plan().title);
  await expect(readGuestDraftFile(new File(['{'], 'bad.json'))).rejects.toThrow('valid JSON');
  await expect(readGuestDraftFile(new File([JSON.stringify({ ...plan(), synthetic_only: false })], 'unsafe.json'))).rejects.toThrow('not a supported');
  await expect(readGuestDraftFile({ size: 1000001 })).rejects.toThrow('under 1 MB');
});
