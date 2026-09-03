const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

/**
 * Automated accessibility checks.
 *
 * axe catches roughly a third of WCAG issues, so a pass here is a floor, not
 * a certification. The dialog and keyboard specs below cover behaviour axe
 * cannot see.
 */

const PUBLIC_PAGES = ['/', '/patients', '/researchers', '/institutions',
                      '/status', '/pricing', '/about', '/contact', '/resources'];

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    const style = document.createElement('style');
    style.textContent = 'html, body { scroll-behavior: auto !important; }';
    document.addEventListener('DOMContentLoaded', () => document.head.appendChild(style));
  });
});

test.describe('axe', () => {
  for (const path of PUBLIC_PAGES) {
    test(`${path} has no serious or critical violations`, async ({ page }) => {
      await page.goto(path, { waitUntil: 'domcontentloaded' });
      const { violations } = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      const blocking = violations.filter(
        (v) => v.impact === 'serious' || v.impact === 'critical'
      );
      const summary = blocking.map(
        (v) => `${v.id} (${v.impact}, ${v.nodes.length}x): ${v.help}`
      );
      expect(summary, `accessibility violations on ${path}`).toEqual([]);
    });
  }
});

test.describe('Colour contrast', () => {
  test('body text meets WCAG AA against the page background', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    const { violations } = await new AxeBuilder({ page })
      .withRules(['color-contrast'])
      .analyze();
    const nodes = violations.flatMap((v) => v.nodes.map((n) => n.html.slice(0, 100)));
    expect(nodes, 'elements below the 4.5:1 contrast threshold').toEqual([]);
  });
});

test.describe('Article dialog', () => {
  const openDialog = async (page) => {
    await page.goto('/resources', { waitUntil: 'domcontentloaded' });
    await page.locator('button[aria-haspopup="dialog"]').first().click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    return dialog;
  };

  test('cards are reachable and operable by keyboard', async ({ page }) => {
    await page.goto('/resources', { waitUntil: 'domcontentloaded' });
    const card = page.locator('button[aria-haspopup="dialog"]').first();
    await card.focus();
    await expect(card).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('dialog')).toBeVisible();
  });

  test('exposes dialog semantics and an accessible name', async ({ page }) => {
    const dialog = await openDialog(page);
    await expect(dialog).toHaveAttribute('aria-modal', 'true');
    const labelledBy = await dialog.getAttribute('aria-labelledby');
    expect(labelledBy, 'dialog has no accessible name').toBeTruthy();
    await expect(page.locator(`#${labelledBy}`)).toBeVisible();
    await expect(page.getByRole('button', { name: /close article/i })).toBeVisible();
  });

  test('moves focus into the dialog on open', async ({ page }) => {
    await openDialog(page);
    const inside = await page.evaluate(() => {
      const d = document.querySelector('[role="dialog"]');
      return d ? d.contains(document.activeElement) : false;
    });
    expect(inside, 'focus stayed outside the open dialog').toBe(true);
  });

  test('traps focus while open', async ({ page }) => {
    await openDialog(page);
    for (let i = 0; i < 25; i += 1) await page.keyboard.press('Tab');
    const inside = await page.evaluate(() => {
      const d = document.querySelector('[role="dialog"]');
      return d ? d.contains(document.activeElement) : false;
    });
    expect(inside, 'focus escaped the dialog while tabbing').toBe(true);
  });

  test('closes on Escape and restores focus to the opener', async ({ page }) => {
    await page.goto('/resources', { waitUntil: 'domcontentloaded' });
    const card = page.locator('button[aria-haspopup="dialog"]').first();
    await card.click();
    await expect(page.getByRole('dialog')).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toHaveCount(0);
    await expect(card, 'focus was not returned to the element that opened the dialog')
      .toBeFocused();
  });

  test('locks background scrolling while open', async ({ page }) => {
    await openDialog(page);
    expect(await page.evaluate(() => document.body.style.overflow)).toBe('hidden');
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toHaveCount(0);
    expect(await page.evaluate(() => document.body.style.overflow)).not.toBe('hidden');
  });
});
