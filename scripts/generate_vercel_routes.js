#!/usr/bin/env node
/**
 * Rewrites the SPA routing block in vercel.json from the app's route table.
 *
 * A catch-all `/(.*)` -> /index.html rewrite makes every unknown URL return
 * HTTP 200 with the app shell, so a typo or a dead link looks like a working
 * page to a crawler or a monitor. Instead each real route is rewritten
 * explicitly; anything else falls through to Vercel's static handling, which
 * has no matching file and returns a genuine 404.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const meta = fs.readFileSync(path.join(ROOT, 'src/components/PageMeta.js'), 'utf8');
const body = meta.slice(meta.indexOf('export const ROUTE_META'), meta.indexOf('/** Public, indexable'));

const routes = [...body.matchAll(/'(\/[^']*)':\s*\{/g)].map((m) => m[1]);
if (routes.length < 10) {
  console.error(`Only found ${routes.length} routes; refusing to write a broken config.`);
  process.exit(1);
}

const configPath = path.join(ROOT, 'vercel.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

config.rewrites = [
  { source: '/api/(.*)', destination: '/api/main.py' },
  ...routes.filter((r) => r !== '/').map((r) => ({ source: r, destination: '/index.html' })),
  { source: '/', destination: '/index.html' },
];

fs.writeFileSync(configPath, JSON.stringify(config, null, 2) + '\n');
console.log(`vercel.json rewrites written: ${routes.length} app routes, unknown paths now 404`);
