#!/usr/bin/env node
/**
 * Verifies the content checker still detects violations.
 *
 * A checker that passes because its patterns stopped matching is worse than
 * no checker: it reports success while claims regress. This injects
 * known-bad copy and asserts each is caught, then asserts that correctly
 * qualified copy is not.
 *
 * Run: node scripts/test_content_claims.js
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const PROBE = path.join(ROOT, 'src/pages/__claim_probe__.js');

const MUST_CATCH = [
  ["soc2/hipaa", "export const a = 'We are SOC 2 certified and HIPAA compliant.';"],
  ["partner count", "export const b = 'Pre-negotiated DUAs with 50+ institutions.';"],
  ["sirb turnaround", "export const c = 'Our central sIRB delivers approval in 3 weeks.';"],
  ["safe harbor achieved", "export const d = 'Automated Safe Harbor compliance.';"],
  ["all 18 identifiers", "export const e = 'Strips all 18 identifiers.';"],
  ["k-anonymity", "export const f = 'We maintain k >= 5 across all datasets.';"],
  ["date shifting", "export const g = 'Date shifting preserves intervals.';"],
  ["gift cards", "export const h = 'Redeem points for Amazon gift cards.';"],
  ["ehr connected", "export const i = 'Connected to Epic and Cerner.';"],
  ["differential privacy", "export const j = 'We apply differential privacy to queries.';"],
  ["patient count", "export const k = 'Over 12,000 patients contributed.';"],
];

// Qualified on the same line, so they must pass.
const MUST_ALLOW = [
  ["planned sirb", "export const l = 'A central sIRB is planned, not in place.';"],
  ["negated shifting", "export const m = 'Dates are truncated, not shifted by an offset.';"],
  ["no k", "export const n = 'No k-anonymity is computed on any output.';"],
  ["planned gift", "export const o = 'Gift cards are planned; none are offered.';"],
];

function runsClean(source) {
  fs.writeFileSync(PROBE, source + '\n');
  try {
    execSync('node scripts/check_content_claims.js', { cwd: ROOT, stdio: 'pipe' });
    return true;
  } catch {
    return false;
  } finally {
    fs.unlinkSync(PROBE);
  }
}

let failures = 0;
for (const [name, source] of MUST_CATCH) {
  if (runsClean(source)) {
    console.error(`  MISSED  ${name}: the checker did not flag this`);
    failures += 1;
  }
}
for (const [name, source] of MUST_ALLOW) {
  if (!runsClean(source)) {
    console.error(`  FALSE POSITIVE  ${name}: qualified copy was rejected`);
    failures += 1;
  }
}

if (failures) {
  console.error(`\n${failures} checker self-test failure(s).`);
  process.exit(1);
}
console.log(
  `Checker self-test passed: ${MUST_CATCH.length} violations caught, `
  + `${MUST_ALLOW.length} qualified phrasings allowed.`
);
