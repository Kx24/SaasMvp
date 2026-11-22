# BOLT-62 — `COMP-01` (parte 6 de 7): componente `navbar` compartido

> Sigue el **Contrato común de las cards `COMP-01`** que va al final de este mensaje (sección de
> cierre). Esta card depende de `COMP-02` (`BOLT-56`): el árbol de temas ya está ordenado; usa
> las rutas que existan hoy, no las de este texto si cambiaron.

## Contexto verificado (2026-11-15, rutas previas a `COMP-02`)

`templates/components/navbar.html` (137) y `navbar_cta.html` (25) ya compartidos; `templates/andesscale/components/navbar.html` (110), `templates/themes/default/components/navbar.html` (213) y `templates/themes/servelec/components/navbar.html` (276). Incluye menú móvil y estado activo: pruébalo en Playwright a 375 px de ancho.

## Qué hacer

1. Compara las variantes y separa lo común de lo propio de cada tema (estructura, textos por
   defecto, clases, efectos).
2. Implementa `templates/components/navbar.html` con parámetros y slots según el contrato; deja
   los archivos de tema como envoltorios finos o bórralos.
3. Fixture de HTML por tema **antes** del cambio y test de equivalencia después.
4. Documenta el componente (parámetros y slots) en `docs/design-system.md`.

## Tests de rojo

`apps.core.tests.test_component_navbar` (archivo nuevo con ese nombre exacto). Debe incluir un
test estructural que falle contra el código original: existe `templates/components/navbar.html`,
los archivos de tema de `navbar` no superan las 15 líneas (son envoltorios) y ninguno repite el
marcado del compartido. Además, el test de equivalencia de HTML por tema.

## No tocar

Vistas, modelos y templatetags salvo que el componente lo exija (justifícalo). Otros componentes.
Rancho Cachimba.

## DoD

- [ ] Un solo `navbar` compartido; temas con envoltorio fino o sin archivo.
- [ ] HTML equivalente por tema (fixture), tokens, a11y y Playwright verdes.
- [ ] Cierre documental: `COMP-01` **parcial** (anota en la fila qué componentes faltan).
