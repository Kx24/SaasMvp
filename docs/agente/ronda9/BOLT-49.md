# BOLT-49 — `LEY-02` (parte 1 de 2): canal y registro de solicitudes de derechos

> **Decisión del dueño (2026-11-15):** formulario público enlazado desde `/privacidad/` y registro
> de solicitudes en el admin. Esta card **puede crear una migración** (modelo nuevo).

## Contexto verificado (2026-11-15)

- Ley 21.719, art. 4 a 11: el titular puede pedir acceso, rectificación, supresión, oposición,
  portabilidad y bloqueo temporal. Plazo de respuesta: 30 días corridos. El responsable debe
  poder demostrar qué se pidió y qué se respondió.
- `/privacidad/` (`apps/website/views/public.py::privacy_policy`, `templates/legal/privacy.html`)
  ya publica la política por tenant y la de la plataforma (`PLATFORM_TENANT_SLUG`); hoy dice que
  los derechos se ejercen por correo.
- Piezas reutilizables: `apps/core/rate_limit.py` (límite por IP que ya usa `contact_submit`),
  honeypot del formulario de contacto, `TenantAdminMixin` (`apps/accounts/mixins.py`),
  `EmailService` / despacho por tenant con `transaction.on_commit`.

## Qué hacer

1. **Modelo** `DataSubjectRequest` en `apps/website/models.py`: `client` (FK, el tenant ante el
   que se ejerce el derecho), `request_type` (acceso, rectificación, supresión, oposición,
   portabilidad, bloqueo), `name`, `email`, `detail` (texto), `status` (`received`,
   `in_progress`, `resolved`, `rejected`), `received_at`, `due_at` (= recibido + 30 días
   corridos, calculado al guardar), `resolved_at`, `response_notes`, `ip_address`. Manager
   tenant-aware como el resto. Sin user-agent.
2. **Formulario público** en `/privacidad/solicitud/` (GET muestra, POST registra), con la
   plantilla resuelta por `render_tenant_template` y estilos Tailwind del tema. Campos: tipo,
   nombre, correo, detalle. Protecciones: CSRF, el mismo rate limit por IP y honeypot que
   `contact_submit`. Respuesta de éxito idéntica siempre (no revela si el correo existe en la
   base). `SYSTEM_DOMAIN` sin tenant → 404.
3. **Avisos por correo**, dentro de `transaction.on_commit` (función local, no lambda): acuse de
   recibo al solicitante con el plazo (fecha `due_at`) y aviso al contacto del tenant
   (`contact_email` de sus settings; en el tenant de la plataforma, al correo de la plataforma).
   URLs con `EmailService._site_url(client)`; nada hardcodeado.
4. **Admin** (`/superadmin/`): `DataSubjectRequestAdmin` con `TenantAdminMixin`, lista con tipo,
   correo, estado, `due_at` y una columna "vence en N días / vencida"; filtro por estado. Al
   pasar a `resolved`/`rejected` se exige `response_notes` y se sella `resolved_at`.
5. **Política:** en ambos cuerpos legales, la sección de derechos enlaza al formulario
   (`{% url %}`) además del correo. No cambies `PRIVACY_POLICY_VERSION`.
6. **Dashboard:** en el inicio del dashboard, un aviso visible solo para roles con
   `view_contacts` cuando hay solicitudes abiertas ("Tienes N solicitudes de datos personales;
   la más próxima vence el …"). La gestión se hace en el admin; no construyas pantallas nuevas.

## Tests de rojo

`apps.website.tests.test_data_subject_requests` (archivo nuevo con ese nombre exacto). Casos:
POST válido crea la solicitud del tenant correcto con `due_at` a 30 días; honeypot y rate limit;
dos tenants no ven solicitudes ajenas (admin y aviso del dashboard); los dos correos salen tras
el commit y ninguno si la transacción falla; resolver sin `response_notes` es rechazado; un
`viewer` no ve el aviso; `localhost` sin tenant → 404.

## No tocar

`ContactSubmission` y su flujo. La exportación y supresión de datos (es la card siguiente).
`PRIVACY_POLICY_VERSION`.

## DoD

- [ ] Una persona puede ejercer sus derechos desde `/privacidad/` y queda registro con plazo.
- [ ] Aislamiento por tenant probado; suite de aislamiento verde.
- [ ] Playwright y a11y verdes (la card agrega una página pública).
- [ ] Cierre documental: `LEY-02` **parcial**; `SEGURIDAD.md` §3 actualizado.
- [ ] En `revisar_humano`: textos visibles al público, cambio en los cuerpos legales, y que la
      identidad del solicitante no se verifica en el formulario (la respuesta va al correo
      indicado).
