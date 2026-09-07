#!/usr/bin/env node
/**
 * Rewrites the SPA routing block in vercel.json from the app's route table.
 *
 * A catch-all `/(.*)` -> /index.html rewrite makes every unknown URL return
 * HTTP 200 with the app shell, so a typo or a dead link looks like a working
 * page to a crawler, a monitor, or a link checker. Instead each real route is
 * rewritten explicitly; anything else falls through to Vercel's static
 * handling, which has no matching file and returns a genuine 404.
 *
 * The in-app NotFound component still renders for client-side navigation.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const app = fs.readFileSync(path.join(ROOT, 'src/App.js'), 'utf8');

// Every <Route path="..."> except the catch-all.
const routes = [...app.matchAll(/<Route\s+path="([^"*]+)"/g)]
  .map((m) => m[1])
  .filter((p, i, all) => all.indexOf(p) === i);

if (routes.length < 10) {
  console.error(`Only found ${routes.length} routes; refusing to write a broken config.`);
  process.exit(1);
}

const configPath = path.join(ROOT, 'vercel.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

// Preserve the non-SPA rewrites (api, static files) in their original order.
const preserved = (config.rewrites || []).filter(
  (r) => r.source !== '/(.*)' && r.destination !== '/index.html'
);

config.rewrites = [
  ...preserved,
  ...routes.filter((r) => r !== '/').map((r) => ({ source: r, destination: '/index.html' })),
  { source: '/', destination: '/index.html' },
];

fs.writeFileSync(configPath, JSON.stringify(config, null, 2) + '\n');
console.log(`vercel.json: ${routes.length} app routes rewritten; unknown paths now 404`);
