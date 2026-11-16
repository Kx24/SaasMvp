# BOLT-61 — `COMP-01` (parte 5 de 7): componente `footer` compartido

> Sigue el **Contrato común de las cards `COMP-01`** que va al final de este mensaje (sección de
> cierre). Esta card depende de `COMP-02` (`BOLT-56`): el árbol de temas ya está ordenado; usa
> las rutas que existan hoy, no las de este texto si cambiaron.

## Contexto verificado (2026-11-15, rutas previas a `COMP-02`)

`templates/components/footer.html` (32, ya compartido en parte), `templates/andesscale/components/footer.html` (201), `templates/themes/servelec/components/footer.html` (118) y `templates/themes/default/components/footer.html` (**vacío**). El footer enlaza a `/privacidad/` (`LEY-01`): debe seguir en todos los temas. Los enlaces "Términos" y "Cookies" de andesscale apuntan a `#` (hallazgo de `BOLT-33`): no los inventes; quítalos o déjalos como están y repórtalo.

## Qué hacer

1. Compara las variantes y separa lo común de lo propio de cada tema (estructura, textos por
   defecto, clases, efectos).
2. Implementa `templates/components/footer.html` con parámetros y slots según el contrato; deja
   los archivos de tema como envoltorios finos o bórralos.
3. Fixture de HTML por tema **antes** del cambio y test de equivalencia después.
4. Documenta el componente (parámetros y slots) en `docs/design-system.md`.

## Tests de rojo

`apps.core.tests.test_component_footer` (archivo nuevo con ese nombre exacto). Debe incluir un
test estructural que falle contra el código original: existe `templates/components/footer.html`,
los archivos de tema de `footer` no superan las 15 líneas (son envoltorios) y ninguno repite el
marcado del compartido. Además, el test de equivalencia de HTML por tema.

## No tocar

Vistas, modelos y templatetags salvo que el componente lo exija (justifícalo). Otros componentes.
Rancho Cachimba.

## DoD

- [ ] Un solo `footer` compartido; temas con envoltorio fino o sin archivo.
- [ ] HTML equivalente por tema (fixture), tokens, a11y y Playwright verdes.
- [ ] Cierre documental: `COMP-01` **parcial** (anota en la fila qué componentes faltan).
