import { parseGuestDraft } from './guestDraft';

const sites = ['a', 'b', 'c'];

export function planningChecklist(plan) {
  const declarations = plan.variables.length * sites.length;
  const assessed = plan.variables.reduce((count, variable) => count + sites.filter(site => variable[site] !== 'unknown').length, 0);
  const reviewed = plan.variables.reduce((count, variable) => count + sites.filter(site => plan.reviews[`${variable.id}:${site}`]?.status === 'reviewed').length, 0);
  return [
    { id: 'guest-plan', label: 'Define the question', detail: plan.title.trim() && plan.question.trim() ? 'Title and question recorded' : 'Add a title and research question', complete: Boolean(plan.title.trim() && plan.question.trim()) },
    { id: 'guest-mapping', label: 'Assess availability', detail: `${assessed} of ${declarations} declarations assessed`, complete: declarations > 0 && assessed === declarations },
    { id: 'mapping-review', label: 'Review the mappings', detail: `${reviewed} of ${declarations} demo reviews recorded`, complete: declarations > 0 && reviewed === declarations },
  ];
}

// A plain-text brief is portable and does not interpret imported text as HTML.
export function buildGuestBrief(raw) {
  const plan = parseGuestDraft(raw);
  const lines = [
    'HEALTHDB — SYNTHETIC STUDY PLANNING BRIEF',
    'Fictional planning content only. Not clinical evidence or institutional approval.',
    'Local, unverified draft. No patient records, verified identities, or live site commitments.',
    '', 'STUDY TITLE', plan.title || '(Untitled study)', '', 'RESEARCH QUESTION', plan.question || '(Not yet defined)',
    '', 'PLANNING CHECKLIST',
    ...planningChecklist(plan).map(step => `${step.complete ? '[x]' : '[ ]'} ${step.label}: ${step.detail}`),
    'Checklist completion does not establish study feasibility or approval.',
    '', 'VARIABLE AVAILABILITY AND NEXT ACTIONS',
  ];
  if (!plan.variables.length) lines.push('No variables defined.');
  for (const variable of plan.variables) {
    lines.push('', variable.name);
    for (const site of sites) {
      const review = plan.reviews[`${variable.id}:${site}`];
      lines.push(`  Fictional site ${site.toUpperCase()}: ${variable[site]} · ${review?.status === 'reviewed' ? 'Demo reviewed (unverified)' : 'Needs review'}`);
      if (review?.mapping) lines.push(`    Mapping: ${review.mapping}`);
      if (review?.owner) lines.push(`    Example owner role: ${review.owner}`);
      lines.push(`    Next action: ${review?.nextAction || 'Assign a mapping review and next action.'}`);
    }
  }
  lines.push('', 'EXAMPLE CONTRIBUTIONS');
  if (!plan.events.length) lines.push('No demo contributions recorded.');
  for (const event of plan.events) lines.push(`${event.sequence}. ${event.description} (${event.at})`);
  lines.push('', `${plan.reviewHistory.length} historical review snapshots are retained in the separate JSON draft.`,
    'This brief shows current mappings. Download the JSON draft to reopen the full plan in HealthDB.', '');
  return lines.join('\n');
}

export function readGuestDraftFile(file) {
  if (!file || file.size > 1000000) return Promise.reject(new Error('Choose a HealthDB JSON draft under 1 MB.'));
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('Could not read that file. Try again or paste the draft JSON below.'));
    reader.onload = () => {
      try {
        const raw = String(reader.result);
        resolve({ raw, plan: parseGuestDraft(raw) });
      } catch (error) { reject(error); }
    };
    reader.readAsText(file);
  });
}
