const { defineConfig, devices } = require('@playwright/test');

const fs = require('fs');

/**
 * Serves the production build and drives it with the Chromium already
 * present in this image. The installed @playwright/test expects a different
 * browser revision than the one on disk, so point at the binary directly
 * rather than downloading a second copy. Falls back to Playwright's own
 * resolution wherever that binary is absent (e.g. CI).
 */
const LOCAL_CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const launchOptions = fs.existsSync(LOCAL_CHROME)
  ? { executablePath: LOCAL_CHROME }
  : {};
module.exports = defineConfig({
  testDir: './e2e',
  // Several specs walk every page in a loop; a single 30s budget is tight
  // for that on a cold static server.
  timeout: 120_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'list' : [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
    reducedMotion: 'reduce',
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], launchOptions } },
    { name: 'mobile', use: { ...devices['Pixel 5'], launchOptions } },
  ],
  webServer: process.env.E2E_BASE_URL ? undefined : {
    command: 'npx serve -s build -l 3000',
    url: 'http://127.0.0.1:3000',
    // Always start a fresh server. Reusing one left over from an earlier
    // run serves a stale build, which reported contrast failures that had
    // already been fixed on disk.
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
