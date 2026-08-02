import { defineConfig, devices } from '@playwright/test';

const isCI = !!process.env.CI;

// Puerto 3001 por defecto para no chocar con `npm run dev` (3000).
const BASE_URL = process.env.E2E_BASE_URL ?? 'http://localhost:3001';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  expect: { timeout: 8000 },
  // En CI un fallo aislado suele ser arranque lento del stack, no una regresión.
  retries: isCI ? 2 : 0,
  workers: isCI ? 1 : undefined,
  // Si el stack no levantó bien, fallan los 22 tests y con reintentos eso son
  // ~15 min de espera inútil. Se corta pronto y se mira el reporte.
  maxFailures: isCI ? 5 : undefined,
  forbidOnly: isCI,
  reporter: isCI
    ? [['list'], ['html', { open: 'never' }], ['github']]
    : [['list']],
  use: {
    baseURL: BASE_URL,
    headless: true,
    screenshot: 'only-on-failure',
    video: isCI ? 'retain-on-failure' : 'off',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
