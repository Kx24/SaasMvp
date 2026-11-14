# BOLT-18 — `CONS-05`: eliminar los flags sin módulo (`enable_blog`, `enable_testimonials`)

## Contexto verificado (2026-11-14)

`ClientSettings` (`apps/tenants/models.py` líneas 335–336) tiene dos flags sin funcionalidad:

- `enable_blog` (default `False`): ningún código lo lee salvo `list_tenants`.
- `enable_testimonials` (default `True`): solo muestra un enlace `#testimonios` en
  `templates/themes/default/components/navbar.html` (bloques en ~línea 56 y ~línea 162). No existe
  modelo ni sección de testimonios.

Usos a limpiar (lista completa según `grep`, verifica que no haya aparecido otro):

- `apps/tenants/models.py:335-336`
- `apps/tenants/admin.py:76` (fila del fieldset: queda solo `enable_contact_form`)
- `apps/tenants/management/commands/list_tenants.py:72-75`
- `templates/themes/default/components/navbar.html` (los dos bloques `{% if ... enable_testimonials %}`)
- `Documentacion/ARQUITECTURA.md:86` (mención `enable_blog/testimon…`)

## Decisión del dueño (2026-11-14)

**Se eliminan los dos.** Testimonios fue parte de la base histórica y nunca se consideró para la
versión final; no se crea módulo (`MOD-03` queda descartada).

## Qué hacer

1. Test nuevo `apps/tenants/tests_flags.py`:
   - `ClientSettings._meta.get_field('enable_blog')` y `('enable_testimonials')` levantan
     `FieldDoesNotExist`.
   - La home de un tenant con `themes/default` no contiene `#testimonios` ni `Testimonios`.
     (Mira `apps/website/tests/test_home_render.py` para armar el tenant y pedir la home.)
   - `call_command('list_tenants')` corre sin error con al menos un tenant creado.
2. Quita los campos del modelo y genera la migración con `makemigrations tenants` (dos
   `RemoveField`; nómbrala `remove_flags_sin_modulo` con `-n`).
3. Limpia admin, `list_tenants`, navbar (borra los bloques completos, enlace incluido) y la línea
   de `ARQUITECTURA.md`.
4. En `Documentacion/KANBAN_PROYECTO.md` borra también la fila `MOD-03` (descartada por la
   decisión de arriba) y anótalo en la línea del histórico.

## No tocar

`enable_gallery`, `enable_contact_form` ni ningún otro flag. Las migraciones antiguas
(`0001`, `0002`) no se editan.

## Tests de rojo

`apps.tenants.tests_flags`

## DoD

- [ ] `grep -rn "enable_blog\|enable_testimonials" apps templates config` solo encuentra
      migraciones.
- [ ] Migración nueva con exactamente dos `RemoveField`; `makemigrations --check` limpio.
- [ ] Suite y Playwright verdes.
- [ ] Cierre documental (`CONS-05` y `MOD-03` fuera del kanban; una línea en el histórico).
