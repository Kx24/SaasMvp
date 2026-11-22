// DASH-05: el dashboard con login real contra el servidor E2E (#TOOL-01).
//
// Usuario `owner-e2e` del tenant `dash-e2e`: lo crea seed_e2e_tenants (solo con
// DEBUG=True, contraseña de desarrollo). Cubre: login, que las pantallas del
// menú carguen sin errores de consola y a11y (mismas reglas que a11y.spec.js)
// en el inicio y en Secciones.
const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

const ORIGIN = 'http://dash-e2e.localhost:8811';
const OWNER = { username: 'owner-e2e', password: 'e2e-only-owner-pass' };

// Errores de consola que no vienen de nuestro código: el dashboard carga
// fuentes, Alpine y htmx desde CDNs que pueden no estar disponibles sin red.
const IGNORED_CONSOLE = [/Failed to load resource/i, /ERR_(NAME_NOT_RESOLVED|INTERNET_DISCONNECTED|CONNECTION)/i];

async function login(page) {
  // Sin `next` el login vuelve a la home pública.
  await page.goto(`${ORIGIN}/auth/login/?next=/dashboard/`);
  await page.fill('#username', OWNER.username);
  await page.fill('#password', OWNER.password);
  await Promise.all([
    page.waitForURL(/\/dashboard\/?$/),
    page.click('button[type="submit"]'),
  ]);
}

function watchConsole(page) {
  const errors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error' && !IGNORED_CONSOLE.some((re) => re.test(msg.text()))) {
      errors.push(msg.text());
    }
  });
  page.on('pageerror', (err) => errors.push(String(err)));
  return errors;
}

async function axeSummary(page) {
  await page.waitForTimeout(1000);
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
  return results.violations.map((v) => ({
    id: v.id,
    impact: v.impact,
    help: v.help,
    nodes: v.nodes.length,
    targets: v.nodes.slice(0, 3).map((n) => n.target.join(' ')),
  }));
}

test.describe('dashboard', () => {
  test('login con credenciales malas no entra', async ({ page }) => {
    await page.goto(`${ORIGIN}/auth/login/`);
    await page.fill('#username', OWNER.username);
    await page.fill('#password', 'incorrecta');
    await page.click('button[type="submit"]');
    await expect(page).not.toHaveURL(/\/dashboard/);
  });

  test('las pantallas del menú cargan sin errores de consola', async ({ page }) => {
    const errors = watchConsole(page);
    await login(page);

    const links = await page.locator('aside nav a.nav-item').evaluateAll((els) =>
      els.map((a) => ({ label: a.textContent.trim(), href: a.getAttribute('href') })));
    const labels = links.map((l) => l.label);
    // Inicio, Marca, Portada, Secciones, Galería y Mensajes (galería activa en dash-e2e).
    for (const expected of ['Inicio', 'Marca', 'Portada', 'Secciones', 'Galería', 'Mensajes']) {
      expect(labels.some((l) => l.startsWith(expected)), `falta ${expected} en ${labels}`).toBe(true);
    }

    for (const link of links) {
      const response = await page.goto(`${ORIGIN}${link.href}`);
      expect(response.status(), `${link.label} (${link.href})`).toBe(200);
      await expect(page.locator('main')).toBeVisible();
    }
    expect(errors).toEqual([]);
  });

  test('el contador de mensajes sin leer aparece en el menú', async ({ page }) => {
    await login(page);
    await expect(page.locator('aside nav a[href="/dashboard/contacts/"] .badge-primary')).toBeVisible();
  });

  test('a11y: inicio del dashboard sin violaciones WCAG2A/AA', async ({ page }) => {
    await login(page);
    const summary = await axeSummary(page);
    expect(summary, JSON.stringify(summary, null, 2)).toEqual([]);
  });

  test('a11y: pantalla de secciones sin violaciones WCAG2A/AA', async ({ page }) => {
    await login(page);
    await page.goto(`${ORIGIN}/dashboard/sections/`);
    const summary = await axeSummary(page);
    expect(summary, JSON.stringify(summary, null, 2)).toEqual([]);
  });
});
