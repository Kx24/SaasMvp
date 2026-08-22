// #TOOL-01: smoke E2E multi-tenant.
//
// Levanta un servidor Django dedicado (config.settings.e2e, DB SQLite
// descartable en db_e2e.sqlite3, puerto 8811 -- no interfiere con el
// dev server normal) y lo migra/siembra antes de correr los tests.
// npx playwright test hace todo en un solo comando, tal como pide el DoD.
const { defineConfig, devices } = require('@playwright/test');

const BASE_URL = 'http://localhost:8811';

module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list']],

  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command:
      'python manage.py migrate --settings=config.settings.e2e --noinput && ' +
      'python manage.py seed_e2e_tenants --settings=config.settings.e2e && ' +
      'python manage.py runserver 8811 --settings=config.settings.e2e --noreload',
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
