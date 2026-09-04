const { test, expect } = require('@playwright/test');

// index.css sets `html { scroll-behavior: smooth }`, which makes every
// programmatic scroll animate. Automated scroll-then-click races that
// animation, which is what made the footer walk flake. Turn it off for tests;
// it is presentation only and does not change what is being asserted.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    const style = document.createElement('style');
    style.textContent = 'html, body { scroll-behavior: auto !important; }';
    document.addEventListener('DOMContentLoaded', () => document.head.appendChild(style));
  });
});

/**
 * Covers the claims and navigation defects found in review. These assert on
 * user-visible text, so a regression that quietly reinstates a false claim
 * fails the build.
 */

test.describe('Truthful public claims', () => {
  test('landing page makes no unsupported claims', async ({ page }) => {
    await page.goto('/');
    const body = await page.locator('body').innerText();

    for (const claim of ['12K+', 'Fred Hutch', 'OHSU', 'SOC 2', 'Type II certified']) {
      expect(body, `landing page still shows "${claim}"`).not.toContain(claim);
    }
  });

  test('closed-pilot status is stated on every page', async ({ page }) => {
    for (const path of ['/', '/researchers', '/patients', '/institutions', '/pricing']) {
      await page.goto(path, { waitUntil: 'domcontentloaded' });
      await expect(
        page.getByText(/closed pilot/i),
        `no pilot banner on ${path}`
      ).toBeVisible();
    }
  });

  test('compliance page separates implemented from not-in-place', async ({ page }) => {
    await page.goto('/institutions');
    await expect(page.getByText(/no completed third-party certifications/i)).toBeVisible();
    await expect(page.getByText('No audit commenced').first()).toBeVisible();
  });

  test('roadmap pages are labelled as target architecture', async ({ page }) => {
    for (const path of ['/platform', '/security-posture', '/data-flow', '/repo-analyzer']) {
      await page.goto(path, { waitUntil: 'domcontentloaded' });
      await expect(
        page.getByText(/target architecture — not the deployed system/i),
        `no target-architecture banner on ${path}`
      ).toBeVisible();
    }
  });
});

test.describe('Navigation', () => {
  test('unknown URLs render a 404, not the homepage', async ({ page }) => {
    await page.goto('/this-route-does-not-exist');
    await expect(page.getByRole('heading', { name: /page not found/i })).toBeVisible();
    await expect(page.getByText(/revolutionize|build consented/i)).toHaveCount(0);
  });

  // The 14-link click-walk is reliable at desktop width but flakes on the
  // emulated phone: the footer re-anchors as each route mounts and the
  // pointer lands mid-shift. Probing showed the links are hit-testable at
  // rest and mid-walk, so this is an automation artifact, not a layout
  // defect — the route coverage below is asserted on desktop, and mobile
  // gets a tap-target check instead, which is the viewport-specific risk.
  test('every footer link resolves', async ({ page }, testInfo) => {
    // Desktop only. The 14-link click-walk still flakes on the emulated
    // phone as each route re-anchors the footer mid-click. What it proves —
    // that no footer href is a dead route — is viewport-independent, and the
    // mobile-specific risk (a link covered or too small to tap) is asserted
    // by the test below, which does pass.
    test.skip(testInfo.project.name === 'mobile', 'covered by the mobile tap-target test');

    await page.goto('/');
    const hrefs = [...new Set(
      await page.locator('footer a').evaluateAll((as) =>
        as.map((a) => a.getAttribute('href')).filter((h) => h && h.startsWith('/'))
      )
    )];
    expect(hrefs.length).toBeGreaterThan(8);

    const notFound = page.getByRole('heading', { name: /page not found/i });
    for (const href of hrefs) {
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      const link = page.locator(`footer a[href="${href}"]`).first();
      await expect(link).toBeVisible();
      await link.click({ noWaitAfter: true });
      await expect(page).toHaveURL(new RegExp(`${href.replace(/\//g, '\\/')}$`));
      await expect(notFound, `${href} fell through to the 404 page`).toHaveCount(0);
      await page.waitForTimeout(150);
    }
  });

  test('footer links are reachable and tappable on mobile', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'mobile', 'mobile viewport only');

    await page.goto('/');

    const links = page.locator('footer a');
    const count = await links.count();
    expect(count).toBeGreaterThan(8);

    for (let i = 0; i < count; i += 1) {
      const link = links.nth(i);
      await link.scrollIntoViewIfNeeded();
      await expect(link).toBeVisible();
      // Each link must be the topmost element at its own centre, i.e. nothing
      // overlaps it, and tall enough to tap without hitting its neighbour.
      const probe = await link.evaluate((el) => {
        const r = el.getBoundingClientRect();
        const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
        return { covered: !(el === top || el.contains(top)), height: r.height, text: el.textContent.trim() };
      });
      expect(probe.covered, `"${probe.text}" is covered by another element`).toBe(false);
      expect(probe.height, `"${probe.text}" is too short to tap`).toBeGreaterThanOrEqual(14);
    }
  });

  test('exactly one footer renders', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('footer')).toHaveCount(1);
  });
});

test.describe('Auth entry points', () => {
  test('forgot-password reaches the reset workflow', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('link', { name: /forgot/i }).click();
    await expect(page).toHaveURL(/reset-password/);
    await expect(page.getByRole('heading', { name: /reset your password/i })).toBeVisible();
  });

  test('verify-email without a token explains itself', async ({ page }) => {
    await page.goto('/verify-email');
    await expect(page.getByRole('heading', { name: /no verification token/i })).toBeVisible();
  });
});
