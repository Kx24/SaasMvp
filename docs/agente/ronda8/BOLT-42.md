# BOLT-42 — `COMP-03`: el botón de enviar no se queda en "Enviando..."

## Contexto verificado (2026-11-15)

- En los formularios de contacto el botón marca el estado de envío en el clic:
  `templates/themes/electricidad/components/contact.html` usa
  `<button type="submit" :disabled="submitting" @click="submitting = true">`. Si el navegador
  bloquea el envío por validación HTML5 (ahora es frecuente: el checkbox de consentimiento de
  `LEY-01` es `required`), el botón queda deshabilitado en "Enviando..." y el usuario no puede
  reintentar sin recargar. Hallado en el ensayo de despliegue (`OPS-07`).
- Hay cuatro formularios con texto "Enviando...": `templates/components/contact_multistep.html`,
  `templates/partials/contact_form.html`, `templates/partials/contact_form_dynamic.html` y
  `templates/themes/electricidad/components/contact.html`. Cada uno maneja el estado a su manera
  (Alpine, JS propio o htmx): revisa los cuatro.

## Qué hacer

1. En cada formulario, el estado "enviando" se activa cuando el envío **realmente ocurre**
   (evento `submit` del formulario, que solo dispara si la validación pasa; o el evento de htmx
   equivalente), no en el clic del botón.
2. Si el envío falla (respuesta 400/500 o error de red en los que usan `fetch`/htmx), el botón
   vuelve a su estado normal y el usuario puede reintentar.
3. No cambies textos, clases de estilo ni el HTML del consentimiento.

## Tests

- Test de plantilla (render): ninguno de los cuatro archivos contiene `@click="submitting = true"`
  ni un equivalente que cambie el estado en el clic; el estado se liga al `submit`.
- Test e2e de Playwright en `tests/e2e/` (sigue el patrón de los existentes): en la home de un
  tenant con formulario de contacto, pulsar enviar con el consentimiento sin marcar deja el botón
  **habilitado** y sin el texto "Enviando...".

## Tests de rojo

`apps.website.tests.test_contact_button` (archivo nuevo con ese nombre exacto: el orquestador confirma el rojo con esa etiqueta).

## No tocar

La vista `contact_submit` ni la validación del servidor. Rancho Cachimba.

## DoD

- [ ] Los cuatro formularios activan "Enviando..." solo en un envío real y se recuperan de un
      error.
- [ ] Playwright y a11y verdes.
- [ ] Cierre documental (`COMP-03`).
