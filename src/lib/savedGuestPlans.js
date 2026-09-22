import { parseGuestDraft } from './guestDraft';

export const SAVED_PLANS_KEY = 'healthdb.saved-guest-plans.v1';
export const MAX_SAVED_PLANS = 10;

export function readSavedPlans() {
  const raw = localStorage.getItem(SAVED_PLANS_KEY);
  if (!raw) return [];
  const data = JSON.parse(raw);
  if (data.version !== 1 || !Array.isArray(data.plans) || data.plans.length > MAX_SAVED_PLANS) throw new Error('Unsupported saved plans');
  const ids = new Set();
  return data.plans.map(item => {
    if (!item || typeof item.id !== 'string' || !item.id || item.id.length > 100 || ids.has(item.id) || typeof item.savedAt !== 'string' || !Number.isFinite(Date.parse(item.savedAt))) throw new Error('Invalid saved plan');
    ids.add(item.id);
    const plan = parseGuestDraft(item.draft);
    return { id: item.id, savedAt: item.savedAt, draft: item.draft, plan };
  });
}

function writePlans(plans) {
  localStorage.setItem(SAVED_PLANS_KEY, JSON.stringify({ version: 1, plans: plans.map(({ id, savedAt, draft }) => ({ id, savedAt, draft })) }));
  return plans;
}

export function savePlanCopy(draft) {
  const plan = parseGuestDraft(draft);
  // Re-read before each mutation so an older tab preserves newer saved copies.
  const plans = readSavedPlans();
  if (plans.length >= MAX_SAVED_PLANS) throw new Error('You have 10 saved copies. Download and remove an older copy before saving another.');
  const copy = { id: crypto.randomUUID(), savedAt: new Date().toISOString(), draft, plan };
  return writePlans([copy, ...plans]);
}

export function removePlanCopy(id) {
  return writePlans(readSavedPlans().filter(plan => plan.id !== id));
}
