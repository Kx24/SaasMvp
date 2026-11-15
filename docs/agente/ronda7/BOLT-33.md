# BOLT-33 — `LEY-01` (1 de 2): páginas de política de privacidad y versión vigente

## Contexto verificado (2026-11-15)

- El aviso del formulario enlaza a `href="#"`: `templates/partials/contact_form.html:162` y
  `templates/andesscale/components/footer.html:195` ("Privacidad"). `contact_form_dynamic.html:232`
  solo imprime `form_config.privacy_text`, sin enlace. Busca el resto con
  `git grep -n 'href="#"' -- templates | grep -i "rivacidad"` y en los footers de todos los temas
  (`templates/themes/*/components/footer.html`, `templates/components/footer.html`).
- No existe ninguna página de política.
- Roles (`Documentacion/SEGURIDAD.md` §3.1): en un **sitio de cliente**, el cliente es el
  responsable y AndesScale su encargado; en el **sitio de la plataforma** (tenant
  `andesscale`), AndesScale es el responsable.
- Datos disponibles para la política: `Client.company_name` / `Client.name`,
  `ClientSettings.contact_email`, `contact_phone`, `address`.
- Las dos políticas (texto legal) **ya están redactadas** en esta carpeta; no las reescribas:
  `docs/agente/ronda7/textos/privacy_tenant.html` y `privacy_platform.html`.

## Decisiones del dueño (2026-11-15)

- Se **guarda la IP** y **no se guarda el user-agent** (el texto de la política ya lo dice).
- Las políticas las revisa un abogado antes del 1-dic; por eso el texto vive en dos archivos
  separados y fáciles de reemplazar.

## Qué hacer

1. Settings (`config/settings/base.py`):
   - `PRIVACY_POLICY_VERSION = '2026-12-01'`
   - `PRIVACY_POLICY_DATE = '1 de diciembre de 2026'`
   - `PLATFORM_TENANT_SLUG = config('PLATFORM_TENANT_SLUG', default='andesscale')`
   (`CONTACT_MAX_RETENTION_DAYS` ya existe de `BOLT-26`; la política lo muestra.)
2. Plantillas (todas nuevas, bajo `templates/legal/`):
   - `privacy_tenant_body.html` = **copia literal** de `docs/agente/ronda7/textos/privacy_tenant.html`.
   - `privacy_platform_body.html` = **copia literal** de `.../privacy_platform.html`.
   - `privacy.html`: página completa. Mira cómo se renderiza cualquier página pública existente
     para extender el layout correcto (`templates/base.html` y los bloques que ya usen las páginas
     sueltas, p. ej. `templates/partials/contact_success.html`, o las de `templates/errors/`);
     título "Política de privacidad", un contenedor centrado y legible con utilidades Tailwind (no
     `style=""`), e incluye el cuerpo que corresponda según `is_platform`.
3. Vista y URL (paquete `apps/website/views/public.py`, y su re-exportación en `views/__init__.py`):
   - `privacy_policy(request)`: si `request.client is None` → `Http404`. Contexto: `company`
     (`company_name` o `name`), `contact_email`, `contact_phone`, `address` (de
     `client.settings`), `retention_days=settings.CONTACT_MAX_RETENTION_DAYS`,
     `version`, `version_date`, `is_platform = (client.slug == settings.PLATFORM_TENANT_SLUG)`.
     Render con `render_tenant_template(request, 'legal/privacy.html', context)` (así un tema
     puede sobreescribirla). Sin decoradores de login. `@never_cache` no; es contenido estático.
   - `path('privacidad/', views.privacy_policy, name='privacy_policy')` en `apps/website/urls.py`,
     **antes** de cualquier patrón comodín. Actualiza el test congelado
     `apps/website/tests/test_views_package.py` (agrega `'privacy_policy'` a `URL_NAMES`, en su
     orden alfabético): es la única edición permitida de ese archivo.
4. Enlaces: reemplaza **todo** `href="#"` de "privacidad" por `{% url 'privacy_policy' %}` en
   `contact_form.html`, en los footers de cada tema y en `contact_form_dynamic.html` (donde solo
   hay texto, deja el texto de `privacy_text` y agrega el enlace "Política de privacidad" a
   continuación). No toques "Términos" (fuera de alcance; repórtalo como hallazgo).
5. `check_tenant_setup`: agrega una verificación que falle (o advierta, siguiendo el patrón del
   comando) cuando `ClientSettings.contact_email` esté vacío, con el mensaje "la política de
   privacidad exige un canal para ejercer derechos". Si el comando no admite el cambio en unas
   15 líneas, no lo hagas y repórtalo.
6. Documentación: en `Documentacion/SEGURIDAD.md` §3.2 actualiza las filas de art. 12 y 14 ter
   (política publicada en `/privacidad/`, con versión) y la de 14 quáter (decisión: se guarda la
   IP y no el user-agent). En el kanban, **acota** `LEY-01` a "captura del consentimiento
   (`BOLT-34`)" y en `LEY-05` agrega "decidido: IP sí, user-agent no".

## Tests (nuevo `apps/website/tests/test_privacy_policy.py`)

- Tenant de cliente (tema `themes/default` y `themes/servelec`): `GET /privacidad/` → 200;
  contiene `company_name`, el correo de contacto, "Agencia de Protección de Datos Personales",
  "30 días corridos", los cinco derechos (acceso, rectificación, supresión, oposición,
  portabilidad), la versión y `CONTACT_MAX_RETENTION_DAYS` días, y **no** contiene "MercadoPago".
- Tenant con `slug == settings.PLATFORM_TENANT_SLUG`: 200 con "MercadoPago" y sin "encargado del
  tratamiento" del texto de cliente.
- `request.client is None` (dominio de sistema): 404.
- Cambiar `override_settings(PRIVACY_POLICY_VERSION='X')` cambia la versión mostrada.
- Estático: ninguna línea de ningún `.html` bajo `templates/` contiene a la vez `href="#"` y
  `rivacidad`.
- Cada footer de tema que mencione "Privacidad" enlaza a `{% url 'privacy_policy' %}`.
- Ningún texto de las políticas contiene `{#` ni `TODO`/`REVISAR` visibles al renderizar.

## No tocar

Modelos y migraciones (es la card siguiente); `FormConfig.privacy_text`; el formulario y su vista;
Rancho Cachimba; el redactado legal de los dos cuerpos.

## Tests de rojo

`apps.website.tests.test_privacy_policy`

## DoD

- [ ] `/privacidad/` responde en cliente y en plataforma con el cuerpo correcto, fecha y versión.
- [ ] Cero `href="#"` de privacidad en `templates/`.
- [ ] `test_views_package` actualizado y verde; suite y Playwright verdes.
- [ ] Cierre documental (según `_CIERRE.md`; `LEY-01` acotada, no borrada). En `revisar_humano`
      del informe: "texto legal pendiente de revisión por abogado (privacy_*.html)".
