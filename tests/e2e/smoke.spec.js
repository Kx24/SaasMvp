// #TOOL-01: smoke E2E multi-tenant.
//
// Cubre los 3 tenants que pide el kanban -- home 200, hero visible,
// navbar/footer, y el mecanismo de contacto real de cada uno (difiere
// por tema, no es el mismo formulario en los 3):
//   - andesscale: formulario multi-step (fetch/AJAX, components/contact_multistep.html)
//   - servelec:   formulario simple (POST clásico, partials/contact_form.html)
//   - ranchocachimba: sin formulario todavía (#RC-07) -- el contacto es WhatsApp
//
// Cada tenant navega directo a su propio subdominio *.localhost (resuelve
// a 127.0.0.1 por RFC 6761, sin tocar /etc/hosts) para que
// TenantMiddleware lo resuelva contra db_e2e.sqlite3 (sembrada por
// apps/tenants/management/commands/seed_e2e_tenants.py). Un override del
// header Host (extraHTTPHeaders) no funciona: Chromium lo rechaza con
// ERR_INVALID_ARGUMENT.
const { test, expect } = require('@playwright/test');

const PORT = 8811;

const TENANTS = [
  { slug: 'andesscale', host: 'andesscale.localhost', contactFlow: 'multistep' },
  { slug: 'servelec-e2e', host: 'servelec-e2e.localhost', contactFlow: 'simple' },
  { slug: 'ranchocachimba-e2e', host: 'ranchocachimba-e2e.localhost', contactFlow: 'whatsapp' },
];

for (const tenant of TENANTS) {
  test.describe(`smoke: ${tenant.slug}`, () => {
    test.use({
      baseURL: `http://${tenant.host}:${PORT}`,
    });

    test('home responde 200 y muestra hero, navbar y footer', async ({ page }) => {
      const response = await page.goto('/');

      expect(response.status()).toBe(200);
      await expect(page.locator('#hero')).toBeVisible();
      await expect(page.locator('nav').first()).toBeVisible();
      await expect(page.locator('footer')).toBeVisible();
    });

    if (tenant.contactFlow === 'simple') {
      test('formulario de contacto envía (POST clásico, servelec/themes-default)', async ({ page }) => {
        await page.goto('/');

        const section = page.locator('#contacto');
        await section.locator('input[name="name"]').fill('Playwright E2E');
        await section.locator('input[name="email"]').fill('e2e@playwright.test');
        await section.locator('textarea[name="message"]').fill(
          'Mensaje de prueba enviado por la suite Playwright de #TOOL-01.'
        );

        await Promise.all([
          page.waitForURL('**/'),
          section.locator('button[type="submit"]').click(),
        ]);

        // Post/Redirect/Get clásico: vuelve a home con un mensaje flash.
        expect(new URL(page.url()).pathname).toBe('/');
      });
    }

    if (tenant.contactFlow === 'multistep') {
      test('formulario multi-step envía (fetch/AJAX, andesscale)', async ({ page }) => {
        await page.goto('/');

        const section = page.locator('#contacto');
        await section.getByText('Consulta general', { exact: false }).click();

        await section.locator('#ms-name').fill('Playwright E2E');
        await section.locator('#ms-email').fill('e2e@playwright.test');
        await section.getByRole('button', { name: 'Continuar' }).click();

        await section.locator('#ms-message').fill(
          'Mensaje de prueba enviado por la suite Playwright de #TOOL-01.'
        );

        const [response] = await Promise.all([
          page.waitForResponse((res) => res.url().includes('/contact/submit/')),
          section.getByRole('button', { name: 'Enviar mensaje' }).click(),
        ]);

        expect(response.status()).toBe(200);
        await expect(section.getByText('¡Listo!')).toBeVisible();
      });
    }

    if (tenant.contactFlow === 'whatsapp') {
      test('contacto vía WhatsApp disponible (sin formulario todavía, #RC-07)', async ({ page }) => {
        await page.goto('/');

        const whatsappLink = page.locator('#contacto a[href*="wa.me"]');
        await expect(whatsappLink).toBeVisible();
        await expect(whatsappLink).toHaveAttribute('href', /wa\.me\/\d+/);
      });
    }
  });
}
