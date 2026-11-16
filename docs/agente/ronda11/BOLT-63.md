# BOLT-63 — `COMP-01` (parte 7 de 7): componente `hero_ctas` compartido

> Sigue el **Contrato común de las cards `COMP-01`** que va al final de este mensaje (sección de
> cierre). Esta card depende de `COMP-02` (`BOLT-56`): el árbol de temas ya está ordenado; usa
> las rutas que existan hoy, no las de este texto si cambiaron.

## Contexto verificado (2026-11-15, rutas previas a `COMP-02`)

`templates/components/hero_ctas_base.html` (41, base compartida), `templates/themes/default/components/hero_ctas.html` (8) y `templates/themes/servelec/components/hero_ctas.html` (6), más `hero_overlay_theme.html` (10 líneas en cada tema) y el slot `templates/components/slots/hero_overlay.html`. Esta card cierra `COMP-01`: unifica `hero_ctas` y `hero_overlay_theme` y verifica que no quede ningún componente duplicado entre temas sin justificar (lista los que queden y por qué).

## Qué hacer

1. Compara las variantes y separa lo común de lo propio de cada tema (estructura, textos por
   defecto, clases, efectos).
2. Implementa `templates/components/hero_ctas.html` con parámetros y slots según el contrato; deja
   los archivos de tema como envoltorios finos o bórralos.
3. Fixture de HTML por tema **antes** del cambio y test de equivalencia después.
4. Documenta el componente (parámetros y slots) en `docs/design-system.md`.

## Tests de rojo

`apps.core.tests.test_component_hero_ctas` (archivo nuevo con ese nombre exacto). Debe incluir un
test estructural que falle contra el código original: existe `templates/components/hero_ctas.html`,
los archivos de tema de `hero_ctas` no superan las 15 líneas (son envoltorios) y ninguno repite el
marcado del compartido. Además, el test de equivalencia de HTML por tema.

## No tocar

Vistas, modelos y templatetags salvo que el componente lo exija (justifícalo). Otros componentes.
Rancho Cachimba.

## DoD

- [ ] Un solo `hero_ctas` compartido; temas con envoltorio fino o sin archivo.
- [ ] HTML equivalente por tema (fixture), tokens, a11y y Playwright verdes.
- [ ] Cierre documental: `COMP-01` cerrada (fila borrada).
