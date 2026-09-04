#!/usr/bin/env node
/**
 * Reads a Playwright JSON report and fails loudly on any unexpected outcome.
 *
 * Exists because a truncated `line` report and a pipeline exit code from the
 * wrong command combined to make a run with 23 failures look like a clean
 * pass. This asserts on the structured result instead: every declared test is
 * accounted for, and nothing is unexpected or interrupted.
 *
 * Usage: npx playwright test --reporter=json > pw.json && node scripts/check_e2e_results.js pw.json
 */
const fs = require('fs');

const file = process.argv[2] || 'pw.json';
if (!fs.existsSync(file)) {
  console.error(`No report at ${file}. Did the Playwright run write JSON?`);
  process.exit(1);
}

let report;
try {
  report = JSON.parse(fs.readFileSync(file, 'utf8'));
} catch (err) {
  // A truncated report means the run died mid-flight. Treating that as
  // "nothing to check" is how a broken run passes silently.
  console.error(`Could not parse ${file}: ${err.message}`);
  console.error('The run was interrupted or the reporter did not finish. Treating as failure.');
  process.exit(1);
}
const counts = {};
const failures = [];

(function walk(suites) {
  for (const suite of suites || []) {
    for (const spec of suite.specs || []) {
      for (const test of spec.tests || []) {
        const status = test.status || 'unknown';
        counts[status] = (counts[status] || 0) + 1;
        if (status !== 'expected' && status !== 'skipped') {
          failures.push(`[${test.projectName}] ${spec.title} (${status})`);
        }
      }
    }
    walk(suite.suites);
  }
})(report.suites);

const total = Object.values(counts).reduce((a, b) => a + b, 0);
console.log('Playwright outcomes:', counts, `total: ${total}`);

if (total === 0) {
  console.error('No tests ran. A suite that collects nothing must not pass.');
  process.exit(1);
}
if (failures.length) {
  console.error(`\n${failures.length} unexpected outcome(s):`);
  failures.forEach((f) => console.error(`  ${f}`));
  process.exit(1);
}
console.log(`All ${counts.expected || 0} tests passed (${counts.skipped || 0} skipped).`);
