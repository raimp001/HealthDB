// Proposed planning scaffold only. No participant data or validated diagnostic rules.
export const myelomaPilot = {
  question: 'Among patients treated with a myeloma bispecific antibody, how are suspected tumor-flare or pseudoprogression events characterized and distinguished from other causes?',
  population: 'Define the participating sites, treatment period, eligible bispecific agents and consecutive treated population before abstraction. Capture all eligible treated patients if estimating event frequency; selected case reports alone cannot supply a denominator.',
  exposure: 'Bispecific agent and treatment phase, using a prespecified treatment start as time zero. Sites retain identifiable source records and linkage keys. This draft does not authorize data transfer.',
  outcome: 'Propose a multidisciplinary adjudication process for suspected events, with prespecified categories and follow-up requirements. Review alternative explanations such as true progression, infection and treatment-related inflammation. Do not treat a suspected signal as established causation.',
  analysis: 'Begin with descriptive feasibility and case characterization. Prespecify event windows, follow-up, missing-data handling, ascertainment bias and the exposed denominator. Obtain independent statistical and clinical review before estimating incidence or comparing agents. Suppress disclosive small cells; relative times and rare combinations still require privacy review.',
  impact: 'Produce a reviewed case definition, data dictionary and transparent limitations. Develop aggregate research outputs and, where appropriate, a separately governed pharmacovigilance handoff. No automatic reporting, sponsor disclosure or clinical recommendations.',
  seeking: 'Site investigators, a myeloma clinician, radiology/pathology reviewers, a statistician and patient advisors. Affiliations and study authority must be confirmed separately.',
  variables: [
    { name: 'bispecific_agent', definition: 'Prespecified agent category for the index treatment; record provenance at the site.', type: 'category', source: 'Site medication administration record', units: 'Protocol-defined agent categories', required: true },
    { name: 'treatment_phase', definition: 'Protocol-defined phase when the suspected event occurred.', type: 'category', source: 'Site treatment record', units: 'Prespecified phase categories', required: true },
    { name: 'event_interval', definition: 'Interval from protocol time zero to the suspected event; privacy reviewer determines permitted precision before release.', type: 'number', source: 'Site-derived interval; exact dates remain at site', units: 'Protocol-approved time units', required: true },
    { name: 'event_evidence', definition: 'Structured evidence categories defined by the review panel; no copied clinical narratives or images.', type: 'category', source: 'Site source review', units: 'Protocol-defined evidence categories', required: true },
    { name: 'adjudicated_category', definition: 'Panel-assigned category under the approved study definition, including an indeterminate option.', type: 'category', source: 'Independent adjudication workflow', units: 'Proposed categories require protocol approval', required: true },
    { name: 'follow_up_completeness', definition: 'Whether follow-up sufficient for protocol adjudication is available; do not infer a response from missing observations.', type: 'category', source: 'Site follow-up review', units: 'Protocol-defined completeness categories', required: true },
  ],
  milestones: [
    { title: 'Agree on the question, denominator and draft case definition', owner: 'Clinical and statistical leads', status: 'todo' },
    { title: 'Confirm consent/authorization, governance and each site data pathway', owner: 'Site PI and privacy/IRB teams', status: 'todo' },
    { title: 'Approve compensation, contribution credit and conflicts policy', owner: 'Patient advisors and study governance', status: 'todo' },
    { title: 'Test the dictionary with synthetic cases at two willing sites', owner: 'Site coordinators', status: 'todo' },
    { title: 'Validate extraction, privacy controls and adjudication reproducibility', owner: 'Independent reviewers', status: 'todo' },
    { title: 'Review results and prepare participant-facing findings', owner: 'Analysis team and patient advisors', status: 'todo' },
  ],
};
