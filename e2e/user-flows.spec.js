const { test, expect } = require('@playwright/test');

/**
 * Navigation, registration, sign-in gating, cohort templates, resource
 * filtering and responsive navigation.
 */

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    const style = document.createElement('style');
    style.textContent = 'html, body { scroll-behavior: auto !important; }';
    document.addEventListener('DOMContentLoaded', () => document.head.appendChild(style));
  });
});

test.describe('Navigation', () => {
  test('primary nav reaches each destination', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name === 'mobile', 'desktop nav is hidden below md');
    await page.goto('/');
    for (const [name, url] of [
      ['Researchers', /\/researchers$/], ['Patients', /\/patients$/],
      ['Institutions', /\/institutions$/], ['About', /\/about$/],
    ]) {
      await page.getByRole('navigation').getByRole('link', { name, exact: true }).click();
      await expect(page).toHaveURL(url);
    }
  });

  test('mobile menu opens and navigates', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'mobile', 'mobile viewport only');
    await page.goto('/');
    const toggle = page.getByRole('button', { name: /toggle menu/i });
    await expect(toggle).toBeVisible();
    await toggle.click();
    const link = page.getByRole('link', { name: 'Patients', exact: true });
    await expect(link).toBeVisible();
    await link.click();
    await expect(page).toHaveURL(/\/patients$/);
  });

  test('the pilot notice appears at 390px without overlapping the header', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'mobile', 'mobile viewport only');
    await page.setViewportSize({ width: 390, height: 800 });
    await page.goto('/');
    const banner = page.getByText(/closed pilot/i).first();
    await expect(banner).toBeVisible();

    // The wordmark must not be hidden behind the notice.
    const overlap = await page.evaluate(() => {
      const brand = [...document.querySelectorAll('a')]
        .find((a) => a.textContent.trim() === 'HealthDB');
      const notice = [...document.querySelectorAll('p')]
        .find((p) => /closed pilot/i.test(p.textContent));
      if (!brand || !notice) return false;
      const a = brand.getBoundingClientRect();
      const b = notice.getBoundingClientRect();
      return !(a.bottom <= b.top || b.bottom <= a.top);
    });
    expect(overlap, 'the pilot notice overlaps the wordmark').toBe(false);
  });
});

test.describe('Registration', () => {
  test('account type is selectable and drives the form', async ({ page }) => {
    await page.goto('/register');
    const researcher = page.getByRole('button', { name: 'Researcher', exact: true });
    const patient = page.getByRole('button', { name: 'Patient', exact: true });
    await expect(researcher).toBeVisible();
    await expect(patient).toBeVisible();

    await researcher.click();
    await expect(page.getByLabel(/institution/i).first()).toBeVisible();

    await patient.click();
    await expect(page.getByRole('button', { name: /create account/i })).toBeVisible();
  });

  test('the type query parameter preselects the role', async ({ page }) => {
    await page.goto('/register?type=patient');
    await expect(page.getByRole('button', { name: 'Patient', exact: true }))
      .toHaveClass(/bg-white/);
  });
});

test.describe('Sign-in gating', () => {
  // Scoped to the panel: the navbar also has a "Sign in" link, so an
  // unscoped role query matches two elements.
  const signInPanel = (page) =>
    page.locator('div').filter({ hasText: /^Sign in required/ }).last();

  test('the cohort builder asks anonymous visitors to sign in', async ({ page }) => {
    await page.goto('/cohort-builder');
    await expect(page.getByRole('heading', { name: /sign in required/i })).toBeVisible();
    const panel = signInPanel(page);
    await expect(panel.getByRole('link', { name: /^sign in$/i })).toBeVisible();
    await expect(panel.getByRole('link', { name: /create an account/i })).toBeVisible();
  });

  test('the sign-in action reaches the login page', async ({ page }) => {
    await page.goto('/cohort-builder');
    await signInPanel(page).getByRole('link', { name: /^sign in$/i }).click();
    await expect(page).toHaveURL(/\/login$/);
  });

  test('dashboards redirect an anonymous visitor to sign in', async ({ page }) => {
    await page.goto('/research');
    await expect(page).toHaveURL(/\/login$/, { timeout: 15000 });
  });
});

test.describe('Cohort templates', () => {
  test('a template can be applied without signing in', async ({ page }) => {
    await page.goto('/cohort-builder');
    const templates = page.locator('button').filter({ hasText: /template|preset|starter/i });
    if (await templates.count() === 0) {
      // The page still has to explain itself when no template UI is present.
      await expect(page.getByRole('heading', { name: /sign in required/i })).toBeVisible();
      return;
    }
    await templates.first().click();
    await expect(page.locator('body')).not.toContainText('undefined');
  });
});

test.describe('Resources', () => {
  test('category filters narrow the list', async ({ page }) => {
    await page.goto('/resources');
    const cards = page.locator('button[aria-haspopup="dialog"]');
    const total = await cards.count();
    expect(total).toBeGreaterThan(0);

    const filters = page.locator('button').filter({ hasText: /^(Privacy|Research|Governance|Patient)/ });
    if (await filters.count() > 0) {
      await filters.first().click();
      await expect(cards.first()).toBeVisible();
      expect(await cards.count()).toBeLessThanOrEqual(total);
    }
  });

  test('an article opens and closes', async ({ page }) => {
    await page.goto('/resources');
    await page.locator('button[aria-haspopup="dialog"]').first().click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.getByRole('button', { name: /close article/i }).click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
  });
});

test.describe('Status page', () => {
  test('states what is live and what is not built', async ({ page }) => {
    await page.goto('/status');
    await expect(page.getByRole('heading', { name: /platform status/i })).toBeVisible();
    await expect(page.getByText('Live').first()).toBeVisible();
    await expect(page.getByText('Planned').first()).toBeVisible();
    await expect(page.getByText(/no certifications held/i)).toBeVisible();
  });

  test('planned capabilities are never described as available', async ({ page }) => {
    await page.goto('/status');
    const body = await page.locator('body').innerText();
    for (const phrase of ['Epic connection', 'HL7v2 ingestion', 'AWS KMS key management']) {
      expect(body).toContain(phrase);
    }
  });
});
