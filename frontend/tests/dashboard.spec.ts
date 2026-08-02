import { test, expect } from '@playwright/test';
import { loginAsAdmin } from './helpers/auth';

/**
 * Humo del dashboard operativo. Requiere el usuario admin sembrado
 * (`python -m scripts.seed_admin` en el backend).
 */
test.describe('Dashboard operativo', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('login como admin aterriza en /dashboard', async ({ page }) => {
    expect(page.url()).toContain('/dashboard');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('la navegación lleva a incidentes', async ({ page }) => {
    await page.click('a[href="/dashboard/incidents"]');
    await page.waitForURL('**/dashboard/incidents');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('la navegación lleva a reportes', async ({ page }) => {
    await page.click('a[href="/dashboard/reports"]');
    await page.waitForURL('**/dashboard/reports');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('admin ve la gestión de usuarios', async ({ page }) => {
    await page.goto('/dashboard/users');
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('table, [role="table"]')).toBeVisible();
  });

  test('admin ve los ajustes de priorización', async ({ page }) => {
    await page.goto('/dashboard/settings');
    await expect(page.locator('h1')).toBeVisible();
  });
});
