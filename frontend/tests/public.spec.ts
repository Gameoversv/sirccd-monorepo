import { test, expect } from '@playwright/test';

/**
 * Humo de las superficies públicas. No dependen de datos sembrados, así que
 * fallan solo si el frontend está realmente roto o no arrancó.
 */
test.describe('Rutas públicas', () => {
  test('la raíz redirige a /login sin sesión', async ({ page }) => {
    await page.goto('/');
    await page.waitForURL('**/login');
    expect(page.url()).toContain('/login');
  });

  test('/login renderiza el formulario', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeEnabled();
  });

  // A diferencia de /login, este formulario identifica los campos por id.
  test('/register renderiza el formulario de ciudadano', async ({ page }) => {
    await page.goto('/register');
    await expect(page.locator('#username')).toBeVisible();
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('#confirm_password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('/guia es accesible sin sesión', async ({ page }) => {
    await page.goto('/guia');
    await expect(page).toHaveURL(/\/guia$/);
    await expect(page.locator('h1')).toBeVisible();
  });

  test('login con credenciales inválidas no navega fuera de /login', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'usuario_que_no_existe');
    await page.fill('input[name="password"]', 'password_incorrecta');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
    expect(page.url()).toContain('/login');
  });

  test('el dashboard no es accesible sin sesión', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForURL('**/login');
    expect(page.url()).toContain('/login');
  });
});
