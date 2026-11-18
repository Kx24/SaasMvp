# BOLT-66 — `DEUDA-12`: residuos de las rondas 10 y 11 (parte verificable)

## Contexto verificado (2026-11-18)

La fila del kanban listaba más cosas de las que existen; esto es lo que sí está en el código:

- `templates/components/slots/footer_default.html:30`: `© 2024 {{ client.settings.company_name }}`
  con el año fijo. Los footers `servelec` y `stripe` ya usan `{% now "Y" %}`.
- `apps/orders/views_onboarding.py:84-86`: si el plan no declara temas, el fallback es
  `available_themes = ['default']`, un slug que **no** está en `Client.THEME_CHOICES` (los valores
  reales son `themes/default`, `themes/servelec`, `themes/andesscale`, ver `apps/tenants/models.py`
  ~línea 50). El cliente quedaría con `template='default'`.
- `themes/andesscale` ya está en `theme_labels` de `ClientOnboardingForm`
  (`apps/orders/forms.py:177`) y por tanto se ofrece **solo si** `Plan.available_themes` lo lista.
- `Documentacion/ARQUITECTURA.md:118` nombra `hero_ctas_base`, que ya no existe (hoy:
  `components/hero_ctas.html` + slots). `Documentacion/AUDITORIA_PLATAFORMA_2026-11.md:20` también
  es un diagnóstico de fecha: **no se edita**.
- `templates/themes/default/components/hero_overlay.html` y
  `templates/themes/servelec/components/hero_overlay.html`: ninguna referencia directa en
  `templates/` ni en `apps/` salvo el slot `components/slots/hero_overlay.html`
  (`website_tags.py:23`). **Verifica a mano antes de borrar**: busca también el nombre
  `hero_overlay` construido dinámicamente (`tenant_include`, `render_tenant_template`,
  concatenaciones). Solo se borran si de verdad nadie los resuelve.
- No hay nada que arreglar en `static/css/input.css` ni en `test_contact_submit.py` /
  `test_navbar_cta.py` respecto de `themes/electricidad`: no los toques. (Las menciones restantes
  de "electricidad" son el rubro de `provision_tenant`, comentarios de fixtures y migraciones
  históricas: tampoco.)

## Qué hacer

1. `footer_default.html`: `© {% now "Y" %}` en vez de `© 2024`.
2. `views_onboarding.py`: fallback `['themes/default']`.
3. `ARQUITECTURA.md` línea ~118: sustituye `hero_ctas_base` por la realidad actual (lee
   `templates/components/hero_ctas.html` y `slots/` para describirla en una frase).
4. Los dos `hero_overlay.html`: bórralos solo si confirmaste que no los usa nadie; si dudas,
   déjalos y anótalo en `revisar_humano`.

## Tests de rojo

`apps.core.tests.test_deuda12_residuos` (archivo nuevo con ese nombre exacto). Casos:
(a) el footer default renderizado contiene el año actual (`date.today().year`) y no `2024`;
(b) el onboarding de un plan con `available_themes=[]` ofrece `themes/default` como única opción y
su valor está en `Client.THEME_CHOICES` (ejercita la vista `views_onboarding` o, si es demasiado
costoso montarla, un test unitario de la rama que arma `available_themes`: descríbelo en el
informe); (c) con un plan sin `themes/andesscale` en `available_themes`, las opciones del
formulario no incluyen `themes/andesscale` (guardia de regresión; puede pasar en rojo: es
esperado).

## No tocar

`CLAUDE.md` (ya actualizado a mano en el commit de planificación), `AUDITORIA_PLATAFORMA_2026-11.md`,
`static/css/input.css`, las fixtures de `apps/core/tests/fixtures/`, `DEUDA-11` (`max_pages`), el
contenido del footer `servelec`/`stripe`.

## DoD

- [ ] El footer default muestra el año actual.
- [ ] Un plan sin temas ya no deja `template='default'` (slug inválido) en el cliente.
- [ ] Cierre documental (`DEUDA-12`): borra la fila; si dejaste los `hero_overlay.html`, crea una
      fila nueva `DEUDA-13` con ese pendiente.
