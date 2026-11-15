# BOLT-17 — `SEC-17`: comentarios `<!-- DEBUG -->` fuera del HTML público

## Contexto verificado (2026-11-14)

El HTML público de los sitios expone datos internos en comentarios:

- `templates/components/media_collection.html` líneas 23–28: un comentario con `mode`, cantidad de
  items y `slot_key`, seguido de un bloque `{% if mode == "slideshow" and items %}` /
  `{% else %}` / `{% endif %}` que **solo** emite dos comentarios DEBUG. El `{% if %}` real del
  componente empieza justo después (línea 31) y no se toca.
- `templates/themes/servelec/components/hero.html` líneas 6–8: tres comentarios con el `str()` de
  la sección (incluye el nombre del cliente), el largo de `hero_images` y la URL de fondo.

## Decisión

Se **eliminan** (no se envuelven en `{% if debug %}`): no aportan nada que el log del loader no dé.

## Qué hacer

1. Test nuevo `apps/website/tests/test_no_debug_html.py`:
   - Un test estático que recorre `templates/**/*.html` y falla si algún archivo contiene
     `<!-- DEBUG` (mensaje con la lista de archivos y líneas). Usa `settings.BASE_DIR`.
   - Un test de render por tema (`themes/default` y `themes/servelec`) que pide la home de un
     tenant con una `Section` hero y afirma que la respuesta no contiene `DEBUG`. Reutiliza
     `_HomeRenderMixin` de `apps/website/tests/test_home_render.py` (impórtalo, no lo copies).
2. Borra las 6 líneas DEBUG y el bloque `if/else/endif` muerto de `media_collection.html`.

## No tocar

El resto de ambos templates; ningún otro componente.

## Tests de rojo

`apps.website.tests.test_no_debug_html` — falla contra el código original porque los comentarios
existen.

## DoD

- [ ] `grep -rn "<!-- DEBUG" templates/` no devuelve nada.
- [ ] El test estático y los de render pasan; fallaban antes.
- [ ] Playwright sigue 7/7 (se tocan templates).
- [ ] Cierre documental según `_CIERRE.md` (card maestra `SEC-17`, tabla `SEC`).
