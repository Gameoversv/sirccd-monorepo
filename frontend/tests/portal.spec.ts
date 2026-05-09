import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:3001';
const CIUDADANO = { username: 'test_ciudadano', password: 'Test1234!' };

async function loginAsCiudadano(page: any) {
  await page.goto(`${BASE}/login`);
  await page.fill('input[name="username"], input[type="text"]', CIUDADANO.username);
  await page.fill('input[type="password"]', CIUDADANO.password);
  await page.click('button[type="submit"]');
  await page.waitForURL(`${BASE}/portal`, { timeout: 10000 });
}

test.describe('Portal ciudadano', () => {
  test('login como ciudadano redirige a /portal', async ({ page }) => {
    await loginAsCiudadano(page);
    expect(page.url()).toBe(`${BASE}/portal`);
  });

  test('portal muestra logo SIRCCD', async ({ page }) => {
    await loginAsCiudadano(page);
    await expect(page.locator('text=SIRCCD').first()).toBeVisible();
  });

  test('portal muestra toggle de idioma', async ({ page }) => {
    await loginAsCiudadano(page);
    await expect(page.locator('button:has-text("ES"), button:has-text("EN")')).toBeVisible();
  });

  test('portal muestra toggle de tema', async ({ page }) => {
    await loginAsCiudadano(page);
    await expect(
      page.locator('[aria-label="Activar modo oscuro"], [aria-label="Activar modo claro"]')
    ).toBeVisible();
  });

  test('portal muestra saludo con nombre del usuario', async ({ page }) => {
    await loginAsCiudadano(page);
    await expect(page.locator('h1')).toContainText('Juan');
  });

  test('portal muestra CTA de reportar daño vial', async ({ page }) => {
    await loginAsCiudadano(page);
    await expect(page.locator('text=Reportar un Daño Vial')).toBeVisible();
  });

  test('CTA lleva al formulario de nuevo reporte', async ({ page }) => {
    await loginAsCiudadano(page);
    await page.click('a[href="/dashboard/reports/new"]');
    await page.waitForURL(`**/dashboard/reports/new`, { timeout: 8000 });
    expect(page.url()).toContain('/dashboard/reports/new');
  });

  test('portal muestra seccion Mis Reportes', async ({ page }) => {
    await loginAsCiudadano(page);
    await expect(
      page.locator('h2:has-text("Mis Reportes"), h2:has-text("My Reports")')
    ).toBeVisible();
  });

  test('toggle de idioma cambia ES → EN', async ({ page }) => {
    await loginAsCiudadano(page);
    await page.locator('button:has-text("ES")').click();
    await expect(page.locator('button:has-text("EN")')).toBeVisible({ timeout: 3000 });
  });

  test('toggle de tema activa modo oscuro', async ({ page }) => {
    await loginAsCiudadano(page);
    await page.locator('[aria-label="Activar modo oscuro"]').click();
    const htmlClass = await page.evaluate(() => document.documentElement.className);
    expect(htmlClass).toContain('dark');
  });

  test('logout redirige a /login', async ({ page }) => {
    await loginAsCiudadano(page);
    await page.click('[aria-label="Salir"], [title="Salir"]');
    await page.waitForURL(`${BASE}/login`, { timeout: 5000 });
    expect(page.url()).toContain('/login');
  });
});
