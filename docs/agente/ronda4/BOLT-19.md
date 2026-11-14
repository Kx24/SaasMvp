# BOLT-19 — `DEUDA-08`: la portada de un sitio nuevo muestra su titular

## Contexto verificado (2026-11-14)

Hallazgo de `BOLT-11`, fijado por `HeroDefaultsFindingTest` en
`apps/website/tests/test_home_render.py` (líneas 95–137): en `themes/default` y
`themes/servelec` el titular del hero solo aparece si `ClientSettings.enable_gallery` es `True`
**y** la `Section` hero tiene `slot_key='hero'`. Ninguno es el valor por defecto
(`Section.slot_key` default `'empty'`, `apps/website/models.py:106`) y ningún alta los fija, así
que un tenant recién creado muestra una portada sin titular.

Piezas involucradas:

- `templates/themes/default/components/hero.html` y `templates/themes/servelec/components/hero.html`:
  ambos hacen `{% get_section 'hero' as hero_section %}` e incluyen
  `components/media_collection.html` con `items=hero_images mode="slideshow"
  slot_key=hero_section.slot_key`.
- `templates/components/media_collection.html`: solo dibuja algo si
  `mode == "slideshow" and items`. Averigua de dónde sale `hero_images` (tag o contexto) y por
  qué queda vacío con la galería apagada: ahí está la primera mitad del bug.
- Altas que crean la sección hero sin `slot_key`: `provision_tenant`
  (`apps/tenants/management/commands/provision_tenant.py:352`), `process_onboarding`,
  `create_tenant`, `setup_production`, y el `Section.objects.get_or_create(...)` del dashboard en
  `apps/website/views.py:1054`. Ubícalas todas con `grep -rn "section_type" apps --include=*.py`.

## Decisión del dueño (2026-11-14)

Se corrigen **las dos mitades**:

1. **Render:** con `slot_key='hero'`, el titular y el diseño base del hero se muestran aunque
   `enable_gallery` sea `False` (un solo slide con el fondo de la sección o el fondo por defecto
   del tema). `enable_gallery` solo decide si hay imágenes de galería, no si hay portada.
2. **Altas:** todo camino que crea la `Section` hero la crea con `slot_key='hero'`.

`slot_key='empty'` elegido a mano sigue significando "sin overlay": **no** se cambia el default
del modelo y **no** hay migración de datos (cambiaría sitios en producción sin que nadie lo pida).

## Qué hacer

1. Reescribe `HeroDefaultsFindingTest` (renómbrala `HeroDefaultsTest`) con esta matriz, en los
   dos temas donde aplique:
   - galería apagada + `slot_key='hero'` → la home **contiene** `HERO_TITLE` (default y servelec).
   - galería encendida + `slot_key='hero'` → contiene `HERO_TITLE`.
   - `slot_key='empty'` (con y sin galería) → **no** contiene `HERO_TITLE`.
   - Tenant creado con `call_command('provision_tenant', ...)` → su `Section` hero tiene
     `slot_key='hero'` y la home contiene el título de esa sección.
   - El hero del dashboard (`get_or_create` de `views.py:1054`) crea con `slot_key='hero'`: un
     test unitario del default basta si levantar la vista es costoso.
2. Corrige el render y las altas.

## No tocar

El default de `Section.slot_key`; el tema `andesscale`; el diseño del hero (clases, estructura):
solo la condición que decide si se dibuja. Nada de Rancho Cachimba.

## Tests de rojo

`apps.website.tests.test_home_render`

## DoD

- [ ] La matriz de arriba pasa; los casos "galería apagada + hero" fallaban antes.
- [ ] Ningún alta crea la hero con `slot_key='empty'` (lista en el informe qué caminos tocaste).
- [ ] Sin migraciones nuevas. Playwright 7/7.
- [ ] Cierre documental (`DEUDA-08`).
