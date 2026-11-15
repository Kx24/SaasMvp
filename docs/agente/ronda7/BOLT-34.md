# BOLT-34 — `LEY-01` (2 de 2): captura y prueba del consentimiento; fuera el user-agent

## Contexto verificado (2026-11-15)

Depende de `BOLT-33` (ya aplicada): existen `settings.PRIVACY_POLICY_VERSION` y la URL
`privacy_policy`.

- **Contacto:** `ContactForm` (`apps/website/forms.py`, ~línea 126) → `contact_submit`
  (`apps/website/views/public.py:60`) crea el `ContactSubmission` (línea ~136) con
  `ip_address=get_client_ip(request)` y `user_agent=...` (línea ~151). Modelo en
  `apps/website/models.py:301` (`ip_address` línea ~363, `user_agent` línea 364). Hay formularios
  en `templates/partials/contact_form.html` (POST clásico), `contact_form_dynamic.html` y el
  formulario multi-paso de `andesscale` (envía por fetch). Encuéntralos todos con
  `git grep -n "contact/submit\\|contact_submit" -- templates apps/*/templates`.
- **Compra:** `checkout_process` (`apps/orders/views.py`, ~línea 90) recibe JSON
  (`token`, `payment_method_id`, `installments`, `email`, `plan_slug`, `payer_name`) y crea la
  `Order` con `ip_address` y `user_agent` (líneas ~150–151). Modelo `Order` en
  `apps/orders/models.py` (`ip_address` ~446, `user_agent` ~452). Formulario en
  `apps/orders/templates/orders/checkout.html` (JS que arma el JSON, ~línea 379).
- `user_agent` aparece además en: `apps/website/admin.py:268,283` y `apps/orders/admin.py:228`.
- Tests e2e que envían formularios: `tests/e2e/smoke.spec.js` (formulario multi-paso de andesscale y
  formulario clásico de servelec).

## Decisiones del dueño (2026-11-15)

- Se **guarda la IP** (prueba del consentimiento) y se **elimina el user-agent** del modelo y de
  la captura, tanto en `ContactSubmission` como en `Order`. Los user-agent ya guardados se pierden
  con la migración (es lo que se quiere).
- El consentimiento se captura con un **checkbox no pre-marcado**, obligatorio, en el formulario
  de contacto (todas sus variantes) y en el checkout.
- El **onboarding** (después de pagar) no lleva checkbox: los datos del sitio se tratan por la
  ejecución del contrato (art. 13 c), y la política lo informa. Muestra solo un aviso con el enlace
  a `{% url 'privacy_policy' %}` junto al botón de enviar.
- Registros anteriores a esta card quedan con `consent_at = NULL` (no se rellenan).

## Qué hacer

1. **Modelos** (una migración por app, nombres `consent_y_sin_user_agent`):
   - `ContactSubmission` y `Order`: `consent_at = DateTimeField(null=True, blank=True)` y
     `consent_policy_version = CharField(max_length=20, blank=True)`; `RemoveField('user_agent')`.
2. **Formulario de contacto:** `accept_privacy = forms.BooleanField(required=True)` en
   `ContactForm`, con mensaje de error claro en español. En `contact_submit`, si el formulario es
   válido, guarda `consent_at=timezone.now()` y
   `consent_policy_version=settings.PRIVACY_POLICY_VERSION`; quita `user_agent`. Respeta las dos
   formas de respuesta existentes (JSON para el formulario multi-paso, redirección para el clásico):
   ante falta de consentimiento, error de validación igual que cualquier otro campo. El honeypot,
   el rate limit y el flujo de spam no cambian.
3. **Templates del contacto:** en cada formulario agrega el checkbox
   `<input type="checkbox" name="accept_privacy" required ...>` **sin `checked`**, con etiqueta
   "He leído y acepto la <a href="{% url 'privacy_policy' %}">política de privacidad</a>" y el
   estilo Tailwind del formulario (accesible: `id`/`for`, foco visible, mismo contraste que el
   resto). Reemplaza la nota "Al enviar este formulario, aceptas…" de `contact_form.html`.
   En el formulario multi-paso, el checkbox va en el último paso y el JS debe enviarlo.
4. **Checkout:** el JSON de `checkout_process` exige `accept_privacy: true`; si falta, responde
   400 con `{'success': False, 'error': 'Debes aceptar la política de privacidad', 'code':
   'MISSING_CONSENT'}` **antes** de tocar el plan o MercadoPago. Al crear la `Order`, guarda
   `consent_at`/`consent_policy_version`; quita `user_agent`. En `checkout.html` agrega el
   checkbox (no pre-marcado, enlace a la política de la plataforma) y que el JS lo incluya en el
   JSON y no permita enviar sin marcarlo.
5. **Onboarding:** aviso con enlace a la política en `orders/onboarding.html` (sin checkbox).
6. **Admin:** quita `user_agent` de ambos admins; muestra `consent_at` y `consent_policy_version`
   como solo lectura en `ContactSubmission` y `Order`.
7. **Tests existentes:** actualiza los que envían el formulario de contacto o el checkout para
   incluir el consentimiento (`tests/e2e/smoke.spec.js` incluido: marcar el checkbox en los dos
   formularios) y los que mencionen `user_agent`. No debilites ninguna aserción.
8. Documentación: `Documentacion/SEGURIDAD.md` §3.2 art. 12 → implementado; kanban: **borra** la fila
   `LEY-01` y deja una línea en el histórico; en `LEY-05` ya consta la decisión de `BOLT-33`.

## Tests

- `apps/website/tests/test_contact_consent.py`:
  - POST sin `accept_privacy` → no se crea `ContactSubmission`, la respuesta es un error de
    validación (en JSON y en POST clásico).
  - POST con `accept_privacy` → se crea con `consent_at` cercano a ahora,
    `consent_policy_version == settings.PRIVACY_POLICY_VERSION` (probar con `override_settings`) e
    `ip_address` guardada.
  - `ContactSubmission` no tiene el campo `user_agent` (`FieldDoesNotExist`) y su admin no lo lista.
  - El HTML renderizado de cada formulario de contacto (clásico, dinámico y multi-paso) contiene
    `type="checkbox" name="accept_privacy"` **sin** `checked`, y un enlace a `/privacidad/`.
  - Honeypot y rate limit siguen funcionando (los tests existentes lo cubren; no los edites salvo
    para agregar el consentimiento).
- `apps/orders/tests/test_checkout_consent.py`:
  - Sin `accept_privacy` → 400 `MISSING_CONSENT`, no se crea `Order` y no se llama a MercadoPago
    (mock sin llamadas).
  - Con `accept_privacy: true` → `Order.consent_at` y `consent_policy_version` guardados,
    `ip_address` presente; `Order` sin campo `user_agent`.
  - El HTML de `checkout.html` incluye el checkbox sin `checked`.

## No tocar

El texto de las políticas y su vista (`BOLT-33`); `FormConfig`; la lógica de MercadoPago; el
rate limit; Rancho Cachimba. Cuidado con `orders/urls.py`: no reordenar (el patrón
`<slug:plan_slug>/` va al final).

## Tests de rojo

`apps.website.tests.test_contact_consent` y `apps.orders.tests.test_checkout_consent`
(la cola corre ambos).

## DoD

- [ ] Sin consentimiento no se guarda ningún mensaje ni se cobra; con consentimiento queda
      fecha, versión e IP.
- [ ] `user_agent` no existe en modelos, vistas, admins ni templates (`git grep user_agent` solo
      encuentra migraciones y este spec).
- [ ] Migraciones `consent_y_sin_user_agent` en `website` y `orders`; `makemigrations --check` limpio.
- [ ] Suite y Playwright verdes con el checkbox en los formularios.
- [ ] Cierre documental (`LEY-01` borrada). En `revisar_humano`: las dos migraciones (borran
      datos), el flujo de checkout y que el onboarding no lleva checkbox por decisión.
