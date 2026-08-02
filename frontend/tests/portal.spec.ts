import { test, expect } from '@playwright/test';
import { CIUDADANO, loginAsCiudadano } from './helpers/auth';

test.describe('Portal ciudadano', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsCiudadano(page);
  });

  test('login como ciudadano redirige a /portal', async ({ page }) => {
    expect(page.url()).toContain('/portal');
  });

  test('portal muestra logo SIRCCD', async ({ page }) => {
    await expect(page.locator('text=SIRCCD').first()).toBeVisible();
  });

  test('portal muestra toggle de idioma', async ({ page }) => {
    await expect(page.locator('button:has-text("ES"), button:has-text("EN")')).toBeVisible();
  });

  test('portal muestra toggle de tema', async ({ page }) => {
    await expect(
      page.locator('[aria-label="Activar modo oscuro"], [aria-label="Activar modo claro"]')
    ).toBeVisible();
  });

  test('portal muestra saludo con nombre del usuario', async ({ page }) => {
    await expect(page.locator('h1')).toContainText(CIUDADANO.firstName);
  });

  test('portal muestra CTA de reportar daño vial', async ({ page }) => {
    await expect(page.locator('text=Reportar un Daño Vial')).toBeVisible();
  });

  test('CTA lleva al formulario de nuevo reporte', async ({ page }) => {
    await page.click('a[href="/dashboard/reports/new"]');
    await page.waitForURL('**/dashboard/reports/new');
    expect(page.url()).toContain('/dashboard/reports/new');
  });

  test('portal muestra seccion Mis Reportes', async ({ page }) => {
    await expect(
      page.locator('h2:has-text("Mis Reportes"), h2:has-text("My Reports")')
    ).toBeVisible();
  });

  test('toggle de idioma cambia ES → EN', async ({ page }) => {
    await page.locator('button:has-text("ES")').click();
    await expect(page.locator('button:has-text("EN")')).toBeVisible();
  });

  test('toggle de tema activa modo oscuro', async ({ page }) => {
    await page.locator('[aria-label="Activar modo oscuro"]').click();
    await expect(page.locator('html')).toHaveClass(/dark/);
  });

  test('logout redirige a /login', async ({ page }) => {
    await page.click('[aria-label="Salir"], [title="Salir"]');
    await page.waitForURL('**/login');
    expect(page.url()).toContain('/login');
  });
});
