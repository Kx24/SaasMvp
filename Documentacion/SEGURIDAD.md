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

**Fuente:** texto oficial en [`Ley-21719_13-DIC-2024.pdf`](Ley-21719_13-DIC-2024.pdf) (BCN, versión con la modificación de la Ley 21.806 del 05-feb-2026). Los artículos citados son los de la Ley 19.628 tal como quedan modificados. Vigencia: día primero del mes 24 tras la publicación (art. primero transitorio) = **1-dic-2026**. Lectura técnica, no asesoría jurídica.

### 3.1 Rol de AndesScale
- **Responsable** (art. 2 n) de los datos de sus compradores y usuarios: `Order`, `PaymentLog`, `User`/`UserProfile`.
- **Encargado o tercero mandatario** (art. 2 x, art. 15 bis) de los leads que cada cliente recibe en su sitio (`ContactSubmission`): los trata por cuenta del cliente, que es el responsable.
- Neon, Render, Cloudinary y Zoho son a su vez encargados de AndesScale (sub-encargo): el art. 15 bis exige **autorización específica y por escrito** del responsable para delegar.

### 3.2 Obligaciones y estado

| Artículo | Qué exige | Estado en la plataforma | Card |
|---|---|---|---|
| **12** Consentimiento | Libre, informado, específico, previo e inequívoco (acto afirmativo); revocable por un medio equivalente; **el responsable debe poder probarlo** | Formulario de contacto sin checkbox ni registro; el aviso enlaza a `href="#"` | `LEY-01` |
| **13** Otras bases de licitud | c) ejecución de contrato o **medidas precontractuales a solicitud del titular**; d) interés legítimo. El responsable debe acreditar la base | Sin base documentada por tratamiento. Un formulario de contacto puede apoyarse en 13 c), pero entonces aplica el 14 d) | `LEY-05` |
| **14 d)** | Suprimir o anonimizar los datos obtenidos para medidas precontractuales | Leads sin purga efectiva (bug de `digest_enabled`); borrado solo manual | `LEY-03` |
| **14 ter** Información y transparencia | Publicar de forma permanente la política (con fecha y versión) y: identidad y contacto del responsable, canal para solicitudes, categorías de datos, universo de personas, destinatarios, finalidades, base de licitud, medidas de seguridad, derechos del titular y recurso ante la Agencia, transferencias internacionales y sus garantías, plazo de conservación, origen de los datos, derecho a retirar el consentimiento, decisiones automatizadas | No existe política publicada, ni de AndesScale ni por tenant | `LEY-01` |
| **4–9** Derechos | Acceso, rectificación, supresión, oposición, portabilidad, no ser objeto de decisiones automatizadas | Sin exportación ni supresión asistida | `LEY-02` |
| **10–11** Procedimiento | Canal sencillo y gratuito (correo o formulario); acusar recibo; responder en **30 días corridos** (prorrogables 30 una vez); **bloqueo temporal en 2 días hábiles**; guardar respaldo de la respuesta; informar el recurso ante la Agencia | No hay canal ni registro de solicitudes | `LEY-02` |
| **14 quáter** Protección desde el diseño y por defecto | Tratar solo los datos estrictamente necesarios | `FormConfig` permite activar muchos campos; se guarda IP y user-agent de cada lead y orden | `LEY-05` |
| **14 quinquies** Seguridad | Medidas acordes al riesgo: cifrado, confidencialidad/integridad/disponibilidad, **capacidad de restaurar**, **verificación regular**; ante un incidente, el responsable debe acreditar sus medidas. Aplica también al encargado | Ver §1 y §2: credenciales en claro, sin backup probado, sin CI | `SEC-05`, `SEC-06`, `SEC-07`, `SEC-10`, `SEC-12`, `DB-02` |
| **14 sexies** Brechas | Reportar a la Agencia sin dilaciones indebidas cuando haya riesgo razonable; **registrar** naturaleza, efectos, categorías, número de afectados y medidas; avisar a los titulares si son datos sensibles, de menores de 14 o económicos. El encargado debe reportar al responsable | No existe procedimiento ni registro | `LEY-06`, `SEC-15` |
| **15 bis** Encargo | Contrato con objeto, duración, finalidad, tipo de datos, categorías de titulares, derechos y obligaciones; prohibido usar los datos para otro fin; sub-encargo solo con autorización escrita; al terminar, **suprimir o devolver** los datos | No hay contrato de encargo con los clientes | `LEY-07`, `BIZ-03` |
| **27–28** Transferencia internacional | Lícita con país adecuado, cláusulas contractuales u otras garantías, o cuando es necesaria para ejecutar un contrato con el titular | Datos en proveedores fuera de Chile sin contratos archivados | `LEY-04` |
| **15 ter** Evaluación de impacto | Obligatoria para perfiles automatizados, tratamiento masivo, monitoreo de zonas públicas o datos sensibles | En principio no aplica (sin datos sensibles ni gran escala); confirmar si un cliente pide capturar datos de salud o de menores | — |
| **49–51** Modelo de prevención | Voluntario; certificarlo es atenuante | No abordado | Congelado |

### 3.3 Sanciones (art. 34 bis a 37 y sexto transitorio)
- **Leves** (p. ej. incumplir el deber de información del 14 ter, no tener canal de contacto, responder tarde): amonestación o multa de hasta 5.000 UTM.
- **Graves** (tratar datos sin consentimiento ni otra base, vulnerar la confidencialidad o las obligaciones de seguridad, omitir comunicaciones o registros de brechas, impedir el ejercicio de derechos, transferir datos al extranjero contra la ley): hasta 10.000 UTM.
- **Gravísimas** (tratamiento fraudulento, omitir deliberadamente una brecha, incumplir resoluciones de la Agencia): hasta 20.000 UTM.
- Durante los **primeros 12 meses** de vigencia, a las empresas de menor tamaño (Ley 20.416) la Agencia **puede** aplicar una amonestación escrita en lugar de multa; queda registrada. Los estándares de información y seguridad se diferencian por tamaño de empresa mediante instrucción general de la Agencia (art. 14 septies), aún por conocerse.
- Atenuantes: reparación, colaboración, ausencia de sanciones previas, autodenuncia.

`LEY-00`: `Informe_Cumplimiento_Ley21719.md` (citado en `MASTER_PLAN` §1.4) sigue sin estar en el repo; con el texto de la ley ya no bloquea, pero conviene recuperarlo.

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
