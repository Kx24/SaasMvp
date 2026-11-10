// #DS-03: accesibilidad AA (WCAG 2.1 A + AA) -- argumento comercial real
// con colegios/municipalidades (uno de los públicos de Rancho Cachimba).
//
// Corre axe-core contra las páginas reales servidas por Django (mismo
// servidor E2E de #TOOL-01, no un mock) para los 2 temas que existen en
// develop (servelec, andesscale) más el login (compartido por todos los
// tenants). ranchocachimba no existe en esta branch (ver smoke.spec.js).
const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

const PORT = 8811;

const PAGES = [
  { name: 'servelec home', host: 'servelec-e2e.localhost', path: '/' },
  { name: 'andesscale home', host: 'andesscale.localhost', path: '/' },
  { name: 'login (compartido)', host: 'servelec-e2e.localhost', path: '/auth/login/' },
];

for (const target of PAGES) {
  test(`a11y: ${target.name} sin violaciones WCAG2A/AA`, async ({ page }) => {
    await page.goto(`http://${target.host}:${PORT}${target.path}`);
    // Varios temas usan .fade-up (opacity 0->1, 0.6s) en casi toda sección;
    // sin esperar, axe mide el contraste a mitad de la transición y reporta
    // decenas de falsos positivos que no existen en la página asentada.
    await page.waitForTimeout(1000);

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    const summary = results.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      help: v.help,
      nodes: v.nodes.length,
      targets: v.nodes.slice(0, 3).map((n) => n.target.join(' ')),
    }));

    expect(summary, JSON.stringify(summary, null, 2)).toEqual([]);
  });
}
