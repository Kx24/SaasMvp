# Seguridad y protección de datos — AndesScale SaaS

> **Chequeo del 2026-11-12** sobre `develop`. Solo lectura de código y escáneres locales (`bandit`, `check --deploy`, greps). **No** incluye pruebas de penetración, revisión del dashboard real de Render/Neon/Cloudinary/Cloudflare ni auditoría de dependencias con `pip-audit` (no está instalado; es parte de `SEC-10`).
> Las cards citadas viven en [`KANBAN_PROYECTO.md`](KANBAN_PROYECTO.md). La parte legal **no es asesoría jurídica**: validar con un abogado antes de publicar políticas o firmar contratos.

## 1. Controles vigentes (verificados)

| Área | Control | Evidencia |
|---|---|---|
| Transporte | HTTPS forzado, HSTS 1 año con subdominios y preload | `config/settings/production.py` (`SECURE_SSL_REDIRECT`, `SECURE_HSTS_*`) |
| Cookies | `Secure`, `HttpOnly` en sesión, `SameSite=Lax`, sin dominio compartido entre tenants; sesión de 2 h que expira al cerrar el navegador | `production.py`, `base.py` |
| Cabeceras | CSP y Permissions-Policy (excepto `/checkout/`, ver `SEC-09`), `X-Frame-Options: DENY`, `nosniff` | `config/settings/security_headers.py` |
| Hosts | `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` derivados de una sola lista de dominios | `production.py` |
| Configuración | `DEBUG=False` fijo; arranque falla sin `SECRET_KEY` ni credenciales SMTP; `manage.py check --deploy` sin hallazgos reales | `production.py`, tests en `apps/core/tests/test_production_settings.py` |
| Aislamiento | Dashboard exige pertenencia al tenant; login cruzado rechazado; suite de aislamiento por HTTP (IDOR incluido) | `apps/accounts/decorators.py`, `apps/tenants/tests_isolation.py`, `apps/website/tests/` |
| Pagos | Webhook MercadoPago con firma HMAC, falla cerrado; nunca confía en el payload (re-consulta el pago) | `apps/orders/services/mercadopago_service.py`, `apps/orders/tests/test_webhooks.py` |
| Abuso | Rate limit en login (IP+usuario+tenant), checkout y contacto; honeypot en el formulario; IP tomada del proxy confiable | `apps/core/rate_limit.py` |
| Secretos | `.env` fuera de git y de su historial; sin claves reales trackeadas; superusuario sin contraseña por defecto | `Inventario_Secretos.md`, `setup_production` |
| Código | `bandit -ll`: **0 High**, 21 Medium (ver `SEC-14`) | Corrida del 2026-11-12 |
| Atajos de desarrollo | `?tenant=<slug>` solo funciona con `DEBUG=True` | `apps/tenants/middleware.py::_detect_tenant` |

## 2. Hallazgos abiertos

| Card | Prioridad | Hallazgo | Evidencia | Riesgo |
|---|---|---|---|---|
| `SEC-05` | P0 | El Django Admin no limita por tenant en `OrderAdmin`, `PaymentLogAdmin`, `ClientEmailSettingsAdmin`, `ClientSettingsAdmin`, `FormConfigAdmin`, `DomainAdmin`, `SEOConfigAdmin`, `UserProfileAdmin`. Además `/superadmin/nuevo/` y `/tenants/` solo piden `is_staff` | `apps/orders/admin.py`, `apps/tenants/admin.py`, `apps/tenants/views.py:16,91`; el patrón correcto existe en `apps/accounts/mixins.py::TenantAdminMixin` | Un usuario staff no-superuser vería RUT, pagos y credenciales de todos los clientes. Hoy depende de que no exista ninguna cuenta así (verificar en producción) |
| `SEC-06` | P0 | `smtp_password` y `api_key` de `ClientEmailSettings` en texto plano | `apps/tenants/models.py:504,521`; no hay librería de cifrado instalada | Una fuga de la base o del admin expone el correo de los clientes |
| `SEC-07` | P0 | ~20 líneas de log escriben emails; el login de `apps/accounts` distingue "email inexistente" de "contraseña incorrecta" | `apps/accounts/views.py`, `apps/orders/views.py`, `views_onboarding.py`, `services/email_service.py`, `services/mercadopago_service.py` | Datos personales en logs de Render + enumeración de usuarios |
| `SEC-10` | P0 | `Django==5.2.6`, `gunicorn==21.2.0`, `djangorestframework==3.15.1` (sin uso) y herramientas de desarrollo (`ipython`, `django-extensions`…) en el `requirements.txt` de producción; Render usa Python 3.11.0 y el entorno local 3.13 | `requirements.txt`, `render.yaml:40` | Vulnerabilidades conocidas sin parchear (confirmar con `pip-audit`), más superficie de la necesaria, diferencias entre local y producción |
| `SEC-08` | P1 | Dos implementaciones de login bajo `/auth/`; la de `apps/accounts` es inalcanzable, sin tests y llama métodos de `UserProfile` que hay que verificar | `config/urls.py:19,40`, `apps/accounts/views.py` | Código de autenticación sin mantener |
| `SEC-11` | P1 | Las subidas del dashboard no validan tipo ni tamaño en el servidor: `validate_image_file` / `validate_video_file` existen pero nadie los llama | `apps/core/cloudinary_utils.py:638,667`; grep sin usos | Archivos arbitrarios hacia Cloudinary, consumo de cuota |
| `SEC-12` | P1 | No hay integración continua: el gate (suite, aislamiento, lint) solo corre a mano | No existe `.github/workflows/` | Una regresión de aislamiento puede llegar a `main` |
| `SEC-13` | P1 | `/superadmin/` sin segundo factor y fuera del rate limiter propio | `config/urls.py:16`; `RateLimiter` solo en `client_login` | Fuerza bruta contra la cuenta con más privilegios |
| `SEC-09` | P2 (bloqueada) | `/checkout/` excluido de la CSP | `security_headers.py` | Requiere sandbox real de MercadoPago |
| `SEC-14` | P2 | 21 avisos Medium de bandit por `mark_safe`; el JSON-LD de `seo_tags.py` no escapa `</`; `{{ section.content\|safe }}` en parciales legados | `apps/website/templatetags/cloudinary_tags.py`, `apps/tenants/templatetags/seo_tags.py:154`, `templates/partials/section_display.html` | XSS almacenado si un cliente escribe HTML en un campo que termina sin escapar |
| `DASH-04` | P2 | Roles `owner`/`admin`/`editor` sin efecto | `can_edit: True` fijo en `apps/website/views.py` | Sin mínimo privilegio dentro de un tenant |
| `OPS-05` | P3 | Rate limiter sobre cache en memoria del proceso | `apps/core/rate_limit.py` | Se reinicia en cada deploy y no se comparte entre procesos |
| `SEC-15` | P2 | No hay runbook de incidentes ni política de rotación de secretos | — | Respuesta improvisada ante una brecha |
| `DB-02` | P1 | Sin backup con restore probado | — | Pérdida de datos irrecuperable |

## 3. Ley 21.719 (protección de datos personales) — rige desde el 1-dic-2026

**Rol de AndesScale:** *responsable* de los datos de sus propios compradores y usuarios (`Order`, `PaymentLog`, `User`/`UserProfile`); *encargado* de los leads que cada cliente recibe en su sitio (`ContactSubmission`), por cuenta de ese cliente.

| Dato personal | Modelo | Obligación | Estado | Card |
|---|---|---|---|---|
| Nombre, email, teléfono, mensaje, IP de quien escribe por el formulario | `website.ContactSubmission` | Consentimiento informado, política de privacidad visible | El aviso enlaza a `href="#"`; sin checkbox ni registro del consentimiento | `LEY-01` |
| Email, nombre, RUT, dirección, IP del comprador | `orders.Order` | Base de licitud, información al titular | Sin aceptación de términos en el onboarding | `LEY-01` |
| Todos los anteriores | — | Derechos de acceso, rectificación, supresión, oposición, portabilidad y bloqueo | Nada implementado (sin exportación, sin bloqueo, borrado físico) | `LEY-02` |
| Leads, pagos, correos encolados | `ContactSubmission`, `PaymentLog`, `EmailOutbox` | Conservar solo lo necesario | Purga solo de contactos y con un bug (depende de `digest_enabled`) | `LEY-03` |
| Todo (Neon, Render, Cloudinary, Zoho fuera de Chile) | — | Transferencia internacional con garantías, contratos con encargados | Sin DPA documentados | `LEY-04` |
| Todo | — | Registro de actividades de tratamiento y definición de roles | No existe | `LEY-05` |
| Todo | — | Detectar, registrar y notificar brechas de seguridad | No existe | `LEY-06` |
| Leads de cada cliente | `ContactSubmission` | Contrato de encargo con cada cliente | No existe (se une a `BIZ-03`) | `LEY-07` |
| Credenciales y datos en logs | `ClientEmailSettings`, logs | Medidas de seguridad apropiadas | Ver `SEC-06`, `SEC-07` | — |

`LEY-00`: `Informe_Cumplimiento_Ley21719.md` (citado en `MASTER_PLAN` §1.4) no está en el repo; ubicarlo antes de redactar la política.

## 4. Cómo repetir el chequeo

```bash
python -m bandit -r apps config -x "*/tests/*,*/tests*.py,*/migrations/*" -ll -q
python -m pip_audit -r requirements.txt            # tras SEC-10 (pip install pip-audit)
python manage.py check --deploy --settings=config.settings.production   # con SECRET_KEY, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
python manage.py test apps.tenants.tests_isolation apps.website.tests
python manage.py test apps -v 1
git ls-files | grep -iE "\.env$|\.pem$|\.key$|\.sqlite3$"                # debe salir vacío
```
Greps útiles: `csrf_exempt` (solo los 2 webhooks), `mark_safe` y `|safe`, `logger.*email`, `class .*Admin` sin `TenantAdminMixin`.

## 5. Checklist por release (`develop` → `main`)

- [ ] Suite completa y suite de aislamiento en verde; `makemigrations --check` limpio.
- [ ] `bandit -ll` sin High nuevos; `pip-audit` sin vulnerabilidades conocidas.
- [ ] Toda vista nueva del dashboard usa `tenant_member_required` y filtra por `request.client`; todo `ModelAdmin` nuevo con datos de clientes usa `TenantAdminMixin`.
- [ ] Ninguna variable nueva con secretos fuera de `Inventario_Secretos.md`; nada de datos personales en logs.
- [ ] Formularios nuevos que capturan datos personales: consentimiento y enlace a la política.
- [ ] Smoke test post-deploy: login por tenant, login cruzado rechazado, formulario de contacto.

## 6. Próxima revisión

Repetir este chequeo al cerrar la Fase 1 del plan (antes del 1-dic-2026) y en cada release. Pendiente fuera del repo: cuentas staff reales en producción, 2FA en Render/Neon/Cloudinary/Cloudflare/Zoho/GitHub, permisos del repositorio.
