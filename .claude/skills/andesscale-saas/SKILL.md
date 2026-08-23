---
name: andesscale-saas
description: Trabajo de tenants/temas en AndesScale SaaS — provisionar un tenant nuevo, crear o depurar un template/theme, tocar branding (ClientSettings), o auditar aislamiento multi-tenant. Úsalo cuando la tarea toque apps/tenants/, templates/{tema}/, o el flujo provision_tenant → check_tenant_setup.
---

# AndesScale SaaS — tenants, temas y aislamiento

Referencia operativa para las tres áreas donde este repo ya tuvo bugs reales por
malentender el sistema: resolución de templates, filtrado por tenant, y
provisioning. `CLAUDE.md` (raíz del repo) tiene comandos y gotchas generales —
esto profundiza específicamente en tenants/temas. Ante cualquier duda, el código
manda sobre este documento: `apps/tenants/template_loader.py`,
`apps/tenants/managers.py`, `apps/tenants/middleware.py`.

## 1. Cómo se resuelve un template (el bug más fácil de reintroducir)

`TenantTemplateLoader` (`apps/tenants/template_loader.py`) intercepta cada
`template_name` que pide una vista y prueba, en orden, **solo las rutas que
existen en disco**:

- Tenant `andesscale` (marca propia): `templates/andesscale/{name}` → `templates/{name}`.
- Cualquier otro tenant: `templates/{client.template}/{name}` → `templates/default/{name}` → `templates/{name}`.
- Sin tenant (`request.client is None`, dominio de sistema): solo `templates/{name}`.

`client.template` es `Client.template` (`THEME_CHOICES`: `'themes/default'`,
`'servelec'`, `'ranchocachimba'`) — **no existe** un campo `template` en
`ClientSettings`, aunque el nombre invite a confundirlos. Las vistas nunca arman
esta ruta a mano: llaman `apps.core.template_resolver.render_tenant_template(request, template_path, context)`,
que delega 100% en el loader.

**Antes de escribir un componente nuevo:** revisar si ya existe en 2+ temas
(`servelec`, `themes/default`, `ranchocachimba`, `andesscale`). Si es así,
generalizarlo a `templates/components/` en vez de duplicarlo — contrato
completo y precedente real (`components/media_collection.html`, parámetro
`mode="slideshow"|"grid"` + slots de override por ruta de template) en
`docs/design-system.md`.

**Gotcha real (`#BUG-01`, 2026-08-22):** un comentario Django `{# ... #}` que
cruza un salto de línea **no lo reconoce el parser** (`tag_re` de Django no usa
`re.DOTALL`) — queda como texto literal dentro de `<head>`, el navegador cierra
`<head>` antes de tiempo y rompe el layout completo. Partir siempre un
comentario multilínea en varios comentarios de una sola línea. Hay un test de
regresión (`apps/core/tests/test_template_comments.py`) que escanea
`templates/**/*.html` con el mismo regex de Django — si lo rompés, ese test lo
detecta.

## 2. Filtrado por tenant — nunca asumas que ya está filtrado

`TenantAwareManager` (`apps/tenants/managers.py`) **no filtra automáticamente**.
El auto-filtro basado en `_current_client` existió y se eliminó en `#MED-02`
(2026-08-22): nunca se seteaba en código de request real y era un atributo de
clase compartido entre requests concurrentes de tenants distintos — un riesgo
real, no solo deuda técnica.

```python
# MAL — no está scoped, devuelve datos de todos los tenants
sections = Section.objects.all()

# BIEN
sections = Section.objects.filter(client=request.client)
sections = Section.objects.for_client(request.client)  # equivalente
```

Toda vista de dashboard además necesita `apps.accounts.decorators.tenant_member_required`
(exige `profile.client == request.client`, o superuser) — un `@login_required`
solo no valida pertenencia al tenant del dominio visitado (`#AUD-03`). El login
real del dashboard es `apps/website/auth_views.py::client_login`, montado en
`auth/login/` por `apps/website/auth_urls.py` — hay un segundo `login_view` en
`apps/accounts/views.py` registrado en la misma URL pero nunca se alcanza
(Django resuelve `auth_urls` primero); no confundir uno con otro.

Antes de dar por cerrada una card que toca un modelo con FK a `Client`, agregar
o revisar un caso en `apps/tenants/tests_isolation.py` (aislamiento vía HTTP,
IDOR incluido) — es la suite que reemplazó al viejo comando manual
`test_isolation` (borrado).

## 3. Provisionar y auditar un tenant

```bash
python manage.py provision_tenant <slug> --industry=<rubro> --theme=<theme>
python manage.py check_tenant_setup <slug>      # gate de QA — no modifica nada
python manage.py list_tenants
```

`--industry` controla solo el contenido semilla (colores, textos de
`TEMPLATE_CONFIGS`); `--theme`/`Client.template` controla exclusivamente la
carpeta visual — no confundir los dos ejes. Al crear un `Client`, un signal
(`apps/tenants/signals.py`) crea automáticamente `ClientSettings` +
`ClientEmailSettings` + `FormConfig` (`get_or_create`, idempotente) — no
crearlos a mano.

`check_tenant_setup` es el gate antes de publicar: valida theme, dominio,
config de email y SEO sin tocar nada. Correrlo siempre antes de sacar
`mode_under_construction`. Procedimiento manual completo (DNS, Search Console,
checklist de publicación) en `Documentacion/Procedimiento_Nuevo_Tenant.md`.

## 4. Brand tokens (branding del tenant)

`ClientSettings` expone `primary_color`/`secondary_color`/`accent_color` y
`font_family` (lista curada, `apps/tenants/fonts.py::FONT_CHOICES` — ya no un
`CharField` libre). Se inyectan como CSS custom properties directamente en el
`base.html` de cada tema — no hay un tag `{% tenant_css %}` ni
`{% tenant_custom_css %}` (se retiraron por completo en `#AUD-11` Paso 4, eran
código muerto). Preferir utilidades Tailwind sobre `style=""` inline en
templates nuevos.
