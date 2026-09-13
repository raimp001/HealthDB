export const GUEST_DRAFT_KEY = 'healthdb.guest-plan.v1';
const availability = ['unknown', 'available', 'derivable', 'unavailable'];
const roles = ['', 'Site data steward', 'Study coordinator', 'Methods reviewer'];
const text = (value, max) => typeof value === 'string' && value.length <= max;
const object = value => value && typeof value === 'object' && !Array.isArray(value);
const review = value => object(value) && text(value.mapping, 1000) && roles.includes(value.owner) && text(value.nextAction, 300) && ['draft', 'reviewed'].includes(value.status) && (value.status !== 'reviewed' || (value.mapping.trim() && value.owner && value.nextAction.trim()));
const timestamp = value => text(value, 40) && Number.isFinite(Date.parse(value));

// Validate before restoring any state. Imported history is always unverified.
export function parseGuestDraft(raw) {
  if (!text(raw, 1000000)) throw new Error('Draft must be under 1 MB.');
  let data;
  try { data = JSON.parse(raw); } catch { throw new Error('Paste valid JSON from a HealthDB guest draft.'); }
  const invalid = () => { throw new Error('This is not a supported HealthDB guest draft. Your current plan has not changed.'); };
  if (!object(data) || data.mode !== 'guest_demo' || data.synthetic_only !== true || (data.schema_version !== undefined && data.schema_version !== 1) || !text(data.title, 160) || !text(data.question, 2000)) invalid();
  if (!Array.isArray(data.variables) || data.variables.length > 100) invalid();
  const ids = new Set(), names = new Set();
  const variables = data.variables.map(v => {
    if (!object(v) || !Number.isSafeInteger(v.id) || v.id < 1 || ids.has(v.id) || !text(v.name, 100) || !v.name.trim() || names.has(v.name.trim().toLowerCase()) || !['a', 'b', 'c'].every(s => availability.includes(v[s]))) invalid();
    ids.add(v.id); names.add(v.name.trim().toLowerCase());
    return { id: v.id, name: v.name.trim(), a: v.a, b: v.b, c: v.c };
  });
  if (!object(data.reviews) || Object.keys(data.reviews).length > 300) invalid();
  const reviews = {};
  for (const [key, value] of Object.entries(data.reviews)) {
    if (!/^\d+:[abc]$/.test(key) || !ids.has(Number(key.split(':')[0])) || !review(value)) invalid();
    reviews[key] = { mapping: value.mapping, owner: value.owner, nextAction: value.nextAction, status: value.status };
  }
  if (!Array.isArray(data.reviewHistory) || data.reviewHistory.length > 1000 || !Array.isArray(data.events) || data.events.length > 1000) invalid();
  const reviewHistory = data.reviewHistory.map((v, i) => {
    if (!review(v) || v.sequence !== i + 1 || !text(v.key, 40) || !/^\d+:[abc]$/.test(v.key) || !text(v.label, 120) || !availability.includes(v.availability) || !text(v.title, 160) || !text(v.question, 2000) || !timestamp(v.at)) invalid();
    return { sequence: v.sequence, key: v.key, label: v.label, mapping: v.mapping, owner: v.owner, nextAction: v.nextAction, status: v.status, availability: v.availability, title: v.title, question: v.question, at: v.at };
  });
  const events = data.events.map((v, i) => {
    if (!object(v) || v.sequence !== i + 1 || v.action !== 'Submitted' || !text(v.description, 300) || !v.description.trim() || !timestamp(v.at)) invalid();
    return { sequence: v.sequence, action: v.action, description: v.description, at: v.at };
  });
  return { title: data.title, question: data.question, variables, reviews, reviewHistory, events };
}

export function readGuestDraft() {
  try {
    const raw = sessionStorage.getItem(GUEST_DRAFT_KEY);
    return raw ? { plan: parseGuestDraft(raw), message: 'Draft restored in this tab. History and reviewer roles remain unverified.' } : {};
  } catch {
    return { message: 'Saved draft could not be restored. You can reopen an exported copy below.' };
  }
}
