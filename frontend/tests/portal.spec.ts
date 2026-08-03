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
    // Por aria-label: "ES"/"EN" como substring matchea también las tarjetas de
    // reporte ("Oeste", "Avenida").
    await expect(
      page.getByRole('button', { name: /^(Switch to English|Cambiar a espanol)$/ })
    ).toBeVisible();
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

  test('CTA lleva al formulario de nuevo reporte del portal', async ({ page }) => {
    // Hay varios accesos al formulario (CTA, nav lateral, tabs): basta uno.
    await page.locator('a[href="/portal/nuevo"]').first().click();
    await page.waitForURL('**/portal/nuevo');
    expect(page.url()).toContain('/portal/nuevo');
  });

  test('ciudadano no puede entrar al panel administrativo', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForURL('**/portal');
    expect(page.url()).toContain('/portal');
  });

  test('portal muestra seccion Mis Reportes', async ({ page }) => {
    // Anclado: `has-text` es substring, y con reportes en pantalla también
    // aparece el mapa "Ubicaciones de mis reportes".
    await expect(
      page.getByRole('heading', { name: /^(Mis Reportes|My Reports)$/ })
    ).toBeVisible();
  });

  test('toggle de idioma cambia ES → EN', async ({ page }) => {
    // Por aria-label y no por texto: `:has-text("EN")` es case-insensitive y
    // matchea cualquier tarjeta de reporte que diga "Avenida".
    await page.getByRole('button', { name: 'Switch to English' }).click();
    await expect(page.getByRole('button', { name: 'Cambiar a espanol' })).toBeVisible();
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
