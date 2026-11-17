# Seguridad y protección de datos — AndesScale SaaS

> **Chequeo del 2026-11-12** sobre `develop`. Solo lectura de código y escáneres locales (`bandit`, `check --deploy`, greps). **No** incluye pruebas de penetración, revisión del dashboard real de Render/Neon/Cloudinary/Cloudflare ni auditoría manual de dependencias (`pip-audit` corre en CI desde `SEC-10`/`SEC-12`).
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
| Integración continua | GitHub Actions en cada push y en PR a `develop`/`main`: `gatekeeper.py --strict`, suite de aislamiento, `ruff check apps/ config/` y `pip-audit`; permisos `contents: read`, sin secretos, variables ficticias | `.github/workflows/ci.yml`, `apps/core/tests/test_ci_workflow.py` (`SEC-12`) |
| Código | `bandit -ll`: **0 High y 0 Medium** (`bandit_medium_high` = 0 en `scripts/gate_baseline.json`; el gate impide que suba); `mark_safe` reemplazado por `format_html` y JSON-LD escapado (`SEC-14`) | `scripts/gate_baseline.json`, `apps/website/templatetags/cloudinary_tags.py` |
| Credenciales de clientes | `smtp_password` y `api_key` de `ClientEmailSettings` cifradas en reposo (`MultiFernet`, `FIELD_ENCRYPTION_KEY`; producción falla al importar sin la clave); el admin no devuelve el secreto (`SEC-06`) | `apps/tenants/models.py`, `Inventario_Secretos.md` |
| Admin | Todo `ModelAdmin` con datos de clientes hereda un único `TenantAdminMixin`: el staff ve solo su tenant (lista, filtros y desplegables FK); `ClientAdmin`, `/superadmin/nuevo/` y `/tenants/` solo superuser (`SEC-05`, `SEC-18`) | `apps/accounts/mixins.py`, `apps/accounts/tests_admin_scope.py` |
| Roles del dashboard | Matriz única `DASHBOARD_PERMISSIONS` aplicada con `tenant_permission_required`: `viewer` solo lectura, `editor` no borra ni cambia la marca (`DASH-04`) | `apps/accounts/permissions.py` |
| Subidas | Validación en servidor del contenido real (Pillow), sin SVG, tope de 10 MB en las 6 subidas del dashboard y los logos (`SEC-11`) | `apps/core/cloudinary_utils.py` |
| Logs y login | Sin emails en logs (`email_ref`, guardia AST); un solo login (`client_login`) sin enumeración de usuarios y con `next` validado (`SEC-07`, `SEC-08`) | `apps/website/auth_views.py` |
| Dependencias | Django 5.2.19, gunicorn 27, pillow 13; herramientas de desarrollo separadas en `requirements-dev.txt`; `pip-audit` limpio y en CI (`SEC-10`) | `requirements.txt`, `.github/workflows/ci.yml` |
| Privacidad | Páginas `/privacidad/` (cliente y plataforma) con versión vigente; consentimiento no pre-marcado en contacto y checkout, con fecha, versión e IP (`LEY-01`) | ver §3.2 |
| Atajos de desarrollo | `?tenant=<slug>` solo funciona con `DEBUG=True` | `apps/tenants/middleware.py::_detect_tenant` |

## 2. Hallazgos abiertos

Cerrados en las rondas 4 a 8: `SEC-05`/`SEC-05b`, `SEC-06`, `SEC-07`, `SEC-08`, `SEC-10`, `SEC-11`, `SEC-14`, `SEC-17`, `SEC-18` (detalle y commit en `historico/KANBAN_HISTORICO.md`).

| Card | Prioridad | Hallazgo | Evidencia | Riesgo |
|---|---|---|---|---|
| `SEC-13` | P1 | `/superadmin/` sin segundo factor y fuera del rate limiter propio | `config/urls.py:16`; `RateLimiter` solo en `client_login` | Fuerza bruta contra la cuenta con más privilegios |
| `SEC-09` | P2 (bloqueada) | `/checkout/` excluido de la CSP | `security_headers.py` | Requiere sandbox real de MercadoPago |
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
| **12** Consentimiento | Libre, informado, específico, previo e inequívoco (acto afirmativo); revocable por un medio equivalente; **el responsable debe poder probarlo** | **Implementado** (`BOLT-34`): checkbox no pre-marcado y obligatorio en el contacto (todas las variantes) y en el checkout; se guardan `consent_at`, `consent_policy_version` e IP en `ContactSubmission` y `Order`; el user-agent ya no se captura. El onboarding no lleva checkbox (base: ejecución del contrato, art. 13 c) y solo enlaza la política. La política ya está publicada en `/privacidad/`, con fecha y versión (`PRIVACY_POLICY_VERSION`), y el aviso del formulario la enlaza (`BOLT-33`) | `LEY-01` ✅ (`BOLT-34`) |
| **13** Otras bases de licitud | c) ejecución de contrato o **medidas precontractuales a solicitud del titular**; d) interés legítimo. El responsable debe acreditar la base | Sin base documentada por tratamiento. Un formulario de contacto puede apoyarse en 13 c), pero entonces aplica el 14 d) | `LEY-05` |
| **14 d)** | Suprimir o anonimizar los datos obtenidos para medidas precontractuales | Mensajes de contacto: tope duro de 365 días (`CONTACT_MAX_RETENTION_DAYS`) para todo tenant activo y cualquier estado, más purga por preferencia (`BOLT-14`, `BOLT-26`). `Order`/`PaymentLog` 6 años y `EmailOutbox` 90 días (`BOLT-48`, tabla de plazos abajo). Pendiente solo el cron en Render (`OPS-06`) | `LEY-03` (parcial) |
| **14 ter** Información y transparencia | Publicar de forma permanente la política (con fecha y versión) y: identidad y contacto del responsable, canal para solicitudes, categorías de datos, universo de personas, destinatarios, finalidades, base de licitud, medidas de seguridad, derechos del titular y recurso ante la Agencia, transferencias internacionales y sus garantías, plazo de conservación, origen de los datos, derecho a retirar el consentimiento, decisiones automatizadas | Política publicada en `/privacidad/` por tenant (cliente responsable) y de AndesScale (tenant `PLATFORM_TENANT_SLUG`), con versión y fecha (`BOLT-33`). Texto legal pendiente de revisión por abogado | `LEY-01` (hecho) |
| **4–9** Derechos | Acceso, rectificación, supresión, oposición, portabilidad, no ser objeto de decisiones automatizadas | Sin exportación ni supresión asistida | `LEY-02` |
| **10–11** Procedimiento | Canal sencillo y gratuito (correo o formulario); acusar recibo; responder en **30 días corridos** (prorrogables 30 una vez); **bloqueo temporal en 2 días hábiles**; guardar respaldo de la respuesta; informar el recurso ante la Agencia | No hay canal ni registro de solicitudes | `LEY-02` |
| **14 quáter** Protección desde el diseño y por defecto | Tratar solo los datos estrictamente necesarios | `FormConfig` permite activar muchos campos; se guarda IP y user-agent de cada lead y orden. Decidido 2026-11-15: se guarda la IP y no el user-agent (la política ya lo dice; quitar el user-agent pendiente en `LEY-05`) | `LEY-05` |
| **14 quinquies** Seguridad | Medidas acordes al riesgo: cifrado, confidencialidad/integridad/disponibilidad, **capacidad de restaurar**, **verificación regular**; ante un incidente, el responsable debe acreditar sus medidas. Aplica también al encargado | Ver §1 y §2: credenciales cifradas (`SEC-06`), CI activo (`SEC-12`); pendiente el backup con restore probado | `DB-02` |
| **14 sexies** Brechas | Reportar a la Agencia sin dilaciones indebidas cuando haya riesgo razonable; **registrar** naturaleza, efectos, categorías, número de afectados y medidas; avisar a los titulares si son datos sensibles, de menores de 14 o económicos. El encargado debe reportar al responsable | No existe procedimiento ni registro | `LEY-06`, `SEC-15` |
| **15 bis** Encargo | Contrato con objeto, duración, finalidad, tipo de datos, categorías de titulares, derechos y obligaciones; prohibido usar los datos para otro fin; sub-encargo solo con autorización escrita; al terminar, **suprimir o devolver** los datos | No hay contrato de encargo con los clientes | `LEY-07`, `BIZ-03` |
| **27–28** Transferencia internacional | Lícita con país adecuado, cláusulas contractuales u otras garantías, o cuando es necesaria para ejecutar un contrato con el titular | Datos en proveedores fuera de Chile sin contratos archivados | `LEY-04` |
| **15 ter** Evaluación de impacto | Obligatoria para perfiles automatizados, tratamiento masivo, monitoreo de zonas públicas o datos sensibles | En principio no aplica (sin datos sensibles ni gran escala); confirmar si un cliente pide capturar datos de salud o de menores | — |
| **49–51** Modelo de prevención | Voluntario; certificarlo es atenuante | No abordado | Congelado |

**Plazos de conservación por tipo de dato** (purga: `send_contact_digest` y `purge_expired_data`):

| Dato | Plazo | Setting | Razón |
|---|---|---|---|
| `ContactSubmission` | 365 días | `CONTACT_MAX_RETENTION_DAYS` | Art. 14 d (medida precontractual) |
| `Order` y `PaymentLog` | 6 años (2190 días) | `ORDER_RETENTION_DAYS` | Obligación tributaria |
| `EmailOutbox` (enviado o fallido; los pendientes no se borran) | 90 días | `EMAIL_OUTBOX_RETENTION_DAYS` | Proporcionalidad |

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
python -m pip_audit -r requirements.txt            # pip install -r requirements-dev.txt
python manage.py check --deploy --settings=config.settings.production   # con SECRET_KEY, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, FIELD_ENCRYPTION_KEY
python manage.py test apps.tenants.tests_isolation apps.website.tests
python manage.py test apps -v 1
git ls-files | grep -iE "\.env$|\.pem$|\.key$|\.sqlite3$"                # debe salir vacío
```
Greps útiles: `csrf_exempt` (solo los 2 webhooks), `mark_safe` y `|safe`, `logger.*email`, `class .*Admin` sin `TenantAdminMixin`.

## 5. Checklist por release (`develop` → `main`)

- [ ] Suite completa y suite de aislamiento en verde; `makemigrations --check` limpio.
- [ ] `bandit -ll` sin High nuevos; `pip-audit` sin vulnerabilidades conocidas.
- [ ] Toda vista nueva del dashboard usa `tenant_permission_required(acción)` (matriz en `ARQUITECTURA.md`, `DASH-04`) y filtra por `request.client`; todo `ModelAdmin` nuevo con datos de clientes usa `TenantAdminMixin`.
- [ ] Ninguna variable nueva con secretos fuera de `Inventario_Secretos.md`; nada de datos personales en logs.
- [ ] Formularios nuevos que capturan datos personales: consentimiento y enlace a la política.
- [ ] Smoke test post-deploy: login por tenant, login cruzado rechazado, formulario de contacto.

## 6. Próxima revisión

Repetir este chequeo al cerrar la Fase 1 del plan (antes del 1-dic-2026) y en cada release. Pendiente fuera del repo: cuentas staff reales en producción, 2FA en Render/Neon/Cloudinary/Cloudflare/Zoho/GitHub, permisos del repositorio.
