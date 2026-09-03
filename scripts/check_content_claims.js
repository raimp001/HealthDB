#!/usr/bin/env node
/**
 * Rejects unsupported claims in user-facing copy.
 *
 * Each rule below corresponds to something the codebase does not do. A page
 * may still discuss these ideas, but only inside content explicitly marked as
 * roadmap or planned — see ALLOWED_FILES and the per-rule `allowNear` escape,
 * which requires a qualifier on the same line.
 *
 * Run: node scripts/check_content_claims.js
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SEARCH_DIRS = ['src', 'public'];
const EXTENSIONS = new Set(['.js', '.jsx', '.html', '.txt', '.json']);

// Files whose entire purpose is to describe the manifest or the target
// architecture. They state status explicitly, so they are exempt.
const ALLOWED_FILES = new Set([
  'src/data/featureStatus.js',
  'src/components/StatusBadge.js',
  'src/pages/PlatformStatus.js',
  'src/components/TargetArchitectureBanner.js',
  'scripts/check_content_claims.js',
]);

// Words that, on the same line, make an otherwise-forbidden phrase acceptable.
const QUALIFIERS = /\b(planned|not built|not in place|no |none|never|would|could|intends?|intended|roadmap|target|hypothetical|illustrative|does not|do not|cannot|no longer|pending|aspiration)\b/i;

const RULES = [
  { id: 'partner-count', pattern: /\b\d{2,}\+?\s+(institutions|partners|sites|hospitals)\b/i,
    why: 'HealthDB has no institutional partners.' },
  { id: 'patient-count', pattern: /\b\d[\d,]*(?:K|,000)\+?\s+patients\b/i,
    why: 'No patient population figure is supported by the live data.' },
  { id: 'approval-turnaround', pattern: /\b(?:\d+\s*(?:-|–|to)\s*)?\d+\s*(?:weeks?|days?|hours?)\b[^.\n]{0,40}\b(?:approval|irb|dua|agreement|reliance|turnaround)\b/i,
    why: 'No approval timeline is supported; HealthDB runs no IRB.' },
  { id: 'prenegotiated', pattern: /pre-?negotiated/i,
    why: 'No agreement has been negotiated with any institution.' },
  { id: 'central-sirb', pattern: /central\s+sirb|our\s+sirb|healthdb'?s?\s+sirb/i,
    why: 'No single-IRB arrangement exists.' },
  { id: 'certified', pattern: /\b(?:soc\s*2|hitrust|iso\s*27001)\b[^.\n]{0,30}\b(?:certified|compliant|audited)\b/i,
    why: 'No certification has been obtained and no audit has begun.' },
  { id: 'hipaa-compliant', pattern: /\bHIPAA[- ]compliant\b/i,
    why: 'Compliance is an organisational determination, not a software property. '
       + 'Describe the implemented transformations instead.' },
  { id: 'emr-connected', pattern: /\b(?:connected|integrated|supported)\s+(?:to\s+)?(?:epic|cerner|meditech|athenahealth)\b/i,
    why: 'No EHR vendor connection exists.' },
  { id: 'federated-live', pattern: /\bwe(?:'| a)re\s+(?:running|operating)\s+federated\b/i,
    why: 'There is one database and no federation.' },
  { id: 'rewards-money', pattern: /\b(gift\s*card|cash\s*(?:out|value|payment)|medical\s*bill|paid\s+in\s+(?:cash|dollars))\b/i,
    why: 'Rewards have no monetary value and no fulfilment provider exists.' },
];

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else if (EXTENSIONS.has(path.extname(entry.name))) out.push(full);
  }
  return out;
}

const violations = [];
for (const dir of SEARCH_DIRS) {
  const abs = path.join(ROOT, dir);
  if (!fs.existsSync(abs)) continue;
  for (const file of walk(abs)) {
    const rel = path.relative(ROOT, file).split(path.sep).join('/');
    if (ALLOWED_FILES.has(rel)) continue;
    // Tests are not user-facing copy. featureStatus.test.js lists manifest
    // keys such as governance.prenegotiated-dua precisely to assert they stay
    // planned, which the naive pattern reads as the claim itself.
    if (/(^|\/)__tests__\//.test(rel) || /\.(test|spec)\.jsx?$/.test(rel)) continue;
    const lines = fs.readFileSync(file, 'utf8').split('\n');
    lines.forEach((line, i) => {
      for (const rule of RULES) {
        if (!rule.pattern.test(line)) continue;
        if (QUALIFIERS.test(line)) continue; // stated as planned or negated
        violations.push({ rel, line: i + 1, rule, text: line.trim().slice(0, 120) });
      }
    });
  }
}

if (violations.length) {
  console.error(`\nUnsupported claims found (${violations.length}):\n`);
  for (const v of violations) {
    console.error(`  ${v.rel}:${v.line}  [${v.rule.id}]`);
    console.error(`    ${v.text}`);
    console.error(`    why: ${v.rule.why}\n`);
  }
  console.error('Either remove the claim, or state it as planned on the same line,');
  console.error('and make sure src/data/featureStatus.js agrees.\n');
  process.exit(1);
}

console.log(`Content check passed: ${RULES.length} rules, no unsupported claims.`);
