# BOLT-60 — `COMP-01` (parte 4 de 7): componente `contact` compartido

> Sigue el **Contrato común de las cards `COMP-01`** que va al final de este mensaje (sección de
> cierre). Esta card depende de `COMP-02` (`BOLT-56`): el árbol de temas ya está ordenado; usa
> las rutas que existan hoy, no las de este texto si cambiaron.

## Contexto verificado (2026-11-15, rutas previas a `COMP-02`)

`templates/andesscale/components/contact.html` (80), `templates/themes/servelec/components/contact.html` (104), `templates/themes/default/components/contact.html` (**vacío**) y el compartido `templates/components/contact_multistep.html` (402). Los formularios reales viven en `templates/partials/contact_form*.html`; el checkbox de consentimiento (`LEY-01`) y el arreglo del botón (`COMP-03`) deben quedar intactos. Si `BOLT-53` ya condiciona el formulario a `is_enabled(client, 'contact')`, consérvalo.

## Qué hacer

1. Compara las variantes y separa lo común de lo propio de cada tema (estructura, textos por
   defecto, clases, efectos).
2. Implementa `templates/components/contact.html` con parámetros y slots según el contrato; deja
   los archivos de tema como envoltorios finos o bórralos.
3. Fixture de HTML por tema **antes** del cambio y test de equivalencia después.
4. Documenta el componente (parámetros y slots) en `docs/design-system.md`.

## Tests de rojo

`apps.core.tests.test_component_contact` (archivo nuevo con ese nombre exacto). Debe incluir un
test estructural que falle contra el código original: existe `templates/components/contact.html`,
los archivos de tema de `contact` no superan las 15 líneas (son envoltorios) y ninguno repite el
marcado del compartido. Además, el test de equivalencia de HTML por tema.

## No tocar

Vistas, modelos y templatetags salvo que el componente lo exija (justifícalo). Otros componentes.
Rancho Cachimba.

## DoD

- [ ] Un solo `contact` compartido; temas con envoltorio fino o sin archivo.
- [ ] HTML equivalente por tema (fixture), tokens, a11y y Playwright verdes.
- [ ] Cierre documental: `COMP-01` **parcial** (anota en la fila qué componentes faltan).
