# BOLT-56 — `COMP-02`: ordenar el árbol de temas

> **Decisión del dueño (2026-11-15):** `themes/electricidad` se **archiva** (no entra a
> `THEME_CHOICES`). Esta card puede crear una migración **solo de datos** si mover `andesscale`
> lo exige.

## Contexto verificado (2026-11-15)

- `templates/themes/` tiene `default`, `servelec` y `electricidad`. `Client.THEME_CHOICES`
  (`apps/tenants/models.py:49`) solo ofrece `themes/default` y `themes/servelec`.
- `templates/themes/electricidad/` contiene solo `components/` (`contact.html`,
  `contact_success.html`, `footer.html`, `navbar.html`): no tiene `base.html` ni `landing/`.
  Lo referencian `apps/core/tests/test_theme_token_contract.py:33`,
  `apps/tenants/management/commands/setup_dev_env.py:55` (`template='electricidad'`) y
  comentarios. `provision_tenant --industry=electricidad` es **otra cosa** (contenido semilla por
  rubro): no se toca.
- `templates/andesscale/` (tema de la plataforma) vive fuera de `themes/`.
  `apps/tenants/template_loader.py:57` tiene un caso especial escrito a mano:
  `if tenant and tenant.slug == 'andesscale'` → busca en `templates/andesscale/`.
  `settings.PLATFORM_TENANT_SLUG` existe desde `LEY-01`.
- Carpetas sueltas: `templates_library/` en la raíz (`electricidad`, `servicios_profesionales`),
  `templates/tenants/admin`, `templates/landing/home.html`, y varios componentes de
  `themes/default` vacíos (0 líneas: `about.html`, `contact.html`, `footer.html`).

## Qué hacer

1. **Archivar `themes/electricidad`:** antes, con `git grep`, confirma que ningún `home.html`,
   vista o plantilla viva lo incluye. Si algo en uso depende de un archivo suyo, muévelo a donde
   corresponda (`templates/components/` o el tema que lo usa) en vez de borrarlo. Luego borra la
   carpeta (el historial de git es el archivo), quítala de `test_theme_token_contract.py` y
   corrige `setup_dev_env.py` para que use un tema real.
2. **`andesscale` dentro de `themes/`:** mueve `templates/andesscale/` a
   `templates/themes/andesscale/` con `git mv`. El loader deja de comparar con el literal
   `'andesscale'`: resuelve el tema de la plataforma por `settings.PLATFORM_TENANT_SLUG` o, mejor,
   por `Client.template` si agregas `('themes/andesscale', 'Plataforma (AndesScale)')` a
   `THEME_CHOICES`. Si eliges `Client.template`, incluye una **migración de datos** reversible que
   ponga ese valor al tenant cuyo slug es `PLATFORM_TENANT_SLUG` (si existe) y conserva en el
   loader un fallback por slug para que una base sin migrar siga abriendo. Actualiza toda
   referencia a `andesscale/…` en plantillas (`{% include %}`, `{% extends %}`), vistas y tests.
3. **Carpetas sueltas:** `templates_library/`, `templates/tenants/` y `templates/landing/`:
   bórralas solo si `git grep` y el loader confirman que nada las usa (ojo: `templates/landing/`
   puede ser el fallback global de `landing/home.html`; si lo es, se queda y se documenta).
   Componentes vacíos de `themes/default`: bórralos si nada los incluye; si algo los incluye, se
   quedan (los resolverá `COMP-01`).
4. Actualiza `docs/design-system.md`, `Documentacion/ARQUITECTURA.md` y el docstring del loader
   con el árbol real. `CLAUDE.md` no se toca: reporta las líneas que quedaron desfasadas.

## Tests de rojo

`apps.tenants.tests_theme_tree` (archivo nuevo con ese nombre exacto). Casos: no existe
`templates/themes/electricidad` ni `templates/andesscale`; toda carpeta de `templates/themes/`
con `base.html` figura en `THEME_CHOICES` y viceversa; el loader no contiene el literal
`'andesscale'`; la home del tenant de la plataforma y la de un tenant de cada tema renderizan
200; el HTML de la home de la plataforma es **idéntico** (normalizando espacios) al de antes del
movimiento (fixture generada antes de mover).

## No tocar

`templates/themes/ranchocachimba/` (no existe en esta rama). El contenido semilla por rubro de
`provision_tenant`. El aspecto de ningún sitio.

## DoD

- [ ] Árbol: `templates/themes/{default,servelec,andesscale}` + `templates/components/`; sin
      carpetas muertas.
- [ ] Render por tema, Playwright y a11y verdes; `makemigrations --check` limpio.
- [ ] Cierre documental (`COMP-02`).
- [ ] En `revisar_humano`: si hay migración de datos, que debe ensayarse en una rama de Neon; la
      lista de carpetas borradas; y revisar la home de la plataforma en el navegador.
