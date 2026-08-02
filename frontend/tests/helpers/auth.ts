import { expect, type Page } from '@playwright/test';

/**
 * Credenciales de los usuarios sembrados antes de correr la suite.
 * En CI las crea `.github/workflows/e2e-tests.yml`; en local, ver
 * docs/frontend/TESTING.md.
 */
export const CIUDADANO = {
  username: process.env.E2E_CIUDADANO_USER ?? 'test_ciudadano',
  password: process.env.E2E_CIUDADANO_PASSWORD ?? 'Test1234!',
  firstName: process.env.E2E_CIUDADANO_FIRST_NAME ?? 'Juan',
} as const;

export const ADMIN = {
  username: process.env.E2E_ADMIN_USER ?? 'test_admin',
  // seed_admin exige 12 caracteres como mínimo.
  password: process.env.E2E_ADMIN_PASSWORD ?? 'E2eAdmin1234!',
} as const;

interface Credentials {
  readonly username: string;
  readonly password: string;
}

/** Rellena el formulario de login y espera la ruta destino según el rol. */
export async function login(
  page: Page,
  credentials: Credentials,
  expectedPath: string
): Promise<void> {
  await page.goto('/login');
  await page.fill('input[name="username"], input[type="text"]', credentials.username);
  await page.fill('input[type="password"]', credentials.password);
  await page.click('button[type="submit"]');
  await page.waitForURL(`**${expectedPath}`, { timeout: 15000 });
  expect(page.url()).toContain(expectedPath);
}

export function loginAsCiudadano(page: Page): Promise<void> {
  return login(page, CIUDADANO, '/portal');
}

export function loginAsAdmin(page: Page): Promise<void> {
  return login(page, ADMIN, '/dashboard');
}
