# Master Plan y Arquitectura — AndesScale SaaS

> Documento de consolidación. No repite desde cero el diagnóstico ya hecho en `ARQUITECTURA_SISTEMA.md` (manual técnico, 374 líneas) y `AUDITORIA_ARQUITECTURA_Y_NEGOCIO.md` (auditoría de riesgo, 149 líneas) — los cita con archivo/clase/función real y los traduce a un tablero Kanban ejecutable y a un flujo de trabajo con el GitHub MCP Server ya activo en este repo (`MANUAL_MCP_GITHUB.md`). Fuente única de verdad de trabajo pendiente día a día: `Documentacion/KANBAN_PROYECTO.md`; este documento es la capa de priorización estratégica y los prompts de ejecución inmediata sobre esa misma base de hallazgos.
>
> Estructura: §1 diagnóstico técnico/legal, §2 tablero Kanban de ejecución, §3 viabilidad comercial y competitiva (consultoría de posicionamiento), §4 modelo de pricing/costos de infraestructura y correcciones al código de planes/renovación, §5 flujo de trabajo MCP y prompts listos para ejecutar las cards críticas.

---

## 1. Diagnóstico Profundo de Arquitectura y Negocio

### 1.1 Estrategia Multitenant — riesgo de tenant bleed

El aislamiento es por **FK explícita (`client_id`) + resolución de dominio en middleware**, no por schema-per-tenant ni Row-Level Security de Postgres (`apps/tenants/middleware.py::TenantMiddleware`, `apps/tenants/managers.py::TenantAwareManager`). El auto-filtro basado en atributo de clase (`_current_client`) se eliminó deliberadamente (`#MED-02`) por ser inseguro bajo concurrencia — el contrato vigente es que **toda vista debe llamar `.for_client(request.client)` explícitamente**, verificado solo por `apps/tenants/tests_isolation.py`.

En las vistas públicas y de dashboard este contrato se cumple (`apps/website/views.py`, decorador `apps/accounts/decorators.py::tenant_member_required`). El **hallazgo más severo confirmado en código** está en una superficie distinta — el Django Admin:

- `apps/orders/admin.py::OrderAdmin` y `PaymentLogAdmin` **no heredan `TenantAdminMixin`** ni definen `get_queryset` propio → cualquier staff con el permiso estándar `orders.view_order` lista y busca (`search_fields` incluye `billing_rut`) las órdenes de **todos** los tenants: RUT, razón social, dirección, teléfono, email, IP, user agent y el payload crudo de Mercado Pago (`Order.mp_response_data`).
- `apps/tenants/admin.py::ClientEmailSettingsAdmin` tampoco filtra, y expone `smtp_password`/`api_key` de todos los tenants (el `help_text` de `smtp_password` dice "se almacena encriptada" pero es un `CharField` plano — sin `Fernet`/`django-cryptography` en el repo, confirmado por grep).
- `apps/marketing/admin.py::SEOConfigAdmin` tampoco filtra (impacto menor: metadatos, no datos de personas).
- En contraste, `apps/website/admin.py` (`SectionAdmin`, `ServiceAdmin`, `ContactSubmissionAdmin`) **sí** usa `TenantAdminMixin` con `tenant_field = 'client'` correctamente — el patrón correcto ya existe en el código, simplemente no se aplicó a los modelos con los datos más sensibles.

Este hallazgo es el ítem #1 del tablero Kanban (sección 2).

### 1.2 Integraciones externas — ubicación exacta

| Integración | Archivo | Símbolo | Detalle verificado |
|---|---|---|---|
| Mercado Pago — wrapper SDK | `apps/orders/services/mercadopago_service.py` | `MercadoPagoService` | Lee `MP_ACCESS_TOKEN`/`MP_PUBLIC_KEY`/`MP_WEBHOOK_SECRET`/`MP_SANDBOX`; `MercadoPagoError(code="CONFIG_ERROR")` si falta el token. |
| Mercado Pago — idempotencia webhook | `apps/orders/views.py` | `mercadopago_webhook_view` (`@csrf_exempt @require_POST`, `POST /webhook/mercadopago/`) | Nunca confía en el payload: siempre re-consulta `get_payment(data_id)`; idempotente si la `Order` ya está `completed`/`refunded`; excepciones no manejadas devuelven **500 a propósito** (`#AUD-08`) para forzar reintento de MP, distinto de los 200 "ignorado a propósito". |
| Mercado Pago — firma | `apps/orders/services/mercadopago_service.py` | `validate_webhook_signature` | HMAC-SHA256 sobre `x-signature`; fail-closed salvo `DEBUG=True` sin secreto configurado; **401** si inválida (`#AUD-02`). |
| Mercado Pago — provisioning post-pago | `apps/orders/views_onboarding.py` | `process_onboarding` (`@transaction.atomic`) | Crea `Client`+`Domain`+`ClientSettings`+`User` owner+`UserProfile`, siembra `Section`s, `order.mark_as_completed()`, dos `transaction.on_commit()` para emails. |
| Cloudinary | `apps/core/cloudinary_utils.py` | `CLOUDINARY_PRESETS`, `get_cloudinary_url`, `upload_to_cloudinary`, `get_srcset_urls` | Convención de carpeta `tenants/{tenant_slug}/{resource_type}/`; `validate_image_file`/`validate_video_file` **existen pero no se llaman desde ningún upload real**. |
| Cloudflare | — | — | **No hay evidencia en el repo** (sin headers `CF-*`, sin config de proxy adicional) — el único proxy reconocido es el de Render (`SECURE_PROXY_SSL_HEADER`). No incluir Cloudflare en ningún diagrama de arquitectura hasta que exista configuración real. |

### 1.3 Transición de Entornos

- **Local (SQLite, Windows/PowerShell)**: `config/settings/development.py` hardcodea `ENGINE: django.db.backends.sqlite3` directo (sin pasar por `dj_database_url`). El comentario arriba del bloque dice *"Database - Neon (configuración para desarrollo local)"* sobre un bloque que es SQLite puro — comentario obsoleto confirmado, no afecta funcionamiento pero confunde a quien lo lea por primera vez.
- **Producción/QAS (Postgres/Render)**: `config/settings/production.py` usa `dj_database_url.config(default=os.environ.get('DATABASE_URL'), conn_health_checks=True)`, sin fallback a SQLite — requiere `DATABASE_URL` seteada o falla al *importar* (mismo patrón fail-fast que `SECRET_KEY`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`).
- **Discrepancia de proveedor Postgres — no resuelta, se cita, no se resuelve acá**: `CLAUDE.md` dice "Supabase/Postgres"; `Documentacion/README.md` dice "Neon"; `render.yaml` provisiona su propia Postgres gestionada por Render (`databases: saasmvp-db`, `fromDatabase.connectionString`) sin connection string externa visible en el repo. Corrección de wording pendiente por decisión explícita del usuario — este documento no la fuerza, solo la deja registrada como bloqueante del punto legal 2.4 (DPA).
- **Gestor de dependencias**: **pip puro** — `requirements.txt` (`Django==5.2.6`, `dj-database-url==3.0.1`, `psycopg2-binary`, `gunicorn`, `whitenoise==6.11.0`, `cloudinary==1.44.1`, `mercadopago`, `django-csp`, `django-permissions-policy`, `python-decouple`, `djangorestframework` — instalado y **sin usar**, no está en `INSTALLED_APPS` ni existe un solo `serializers.py`/`viewsets` en el repo) + `requirements-dev.txt` (`ruff`, `bandit`, `coverage`, `pyyaml`). No hay `Pipfile`, `pyproject.toml` ni `uv.lock` en la raíz — confirmado por listado directo, no hay gestor veloz (`uv`) ni `Pipenv` en juego.
- **Sin `.env.example` committeado** — el README indica `cp .env.example .env` pero el archivo no existe; onboarding de un dev nuevo depende de variables documentadas en prosa.

### 1.4 Compliance Ley 21.719

**Contexto**: ya existe `Documentacion/Informe_Cumplimiento_Ley21719.md` con el diagnóstico legal (rol de AndesScale como Responsable/Encargado, Art. 15 bis, plazo 1-dic-2026, sanciones hasta 20.000 UTM). Lo verificado en código es **cuánto de ese plan está implementado: casi nada**.

**Mapeo de datos personales:**

| Dato | Modelo/campo | Sensibilidad |
|---|---|---|
| RUT, razón social, dirección, comuna | `apps/orders/models.py::Order` (`billing_rut`, `billing_razon_social`, `billing_direccion`, `billing_comuna`) | Alta |
| Email, nombre, teléfono comprador | `Order.email`, `.buyer_name`, `.buyer_phone` | Alta |
| IP, payload crudo de pago | `apps/orders/models.py::PaymentLog` (`ip_address`, `raw_data`) | Alta |
| Nombre, email, teléfono, IP, UA (leads) | `apps/website/models.py::ContactSubmission` | Alta |
| Credenciales SMTP / API key de terceros | `apps/tenants/models.py::ClientEmailSettings` (`smtp_password` en texto plano, `api_key`) | Crítica |
| Cuerpo completo de emails transaccionales | `apps/core/models.py::EmailOutbox` (`html_content`/`text_content`, sin retención ni purga) | Alta |

**Gaps verificados (grep negativo sobre `export_data`, `delete_user`, `anonymize`, "portabilidad" — cero resultados fuera de los documentos de roadmap):**

- **ARCOP**: cero implementado. Sin campo `is_blocked_at`/`status_blocked` en `UserProfile`, sin vista/endpoint/management command de exportación o supresión, sin `SoftDelete` en ningún modelo (todos los `delete()` son físicos).
- **Consentimiento**: `apps/website/forms.py::ContactForm` no tiene campo de consentimiento. El disclaimer en `templates/partials/contact_form.html` ("Al enviar este formulario, aceptas nuestra política de privacidad") enlaza a `href="#"` — no existe página de política real. `apps/orders/forms.py::ClientOnboardingForm` tampoco captura consentimiento/ToS.
- **Retención/purga**: solo `ContactSubmission` tiene purga (`apps/tenants/management/commands/send_contact_digest.py::_purge_old_contacts`), y con un bug — solo corre si `digest_enabled=True`, así que un tenant con `auto_purge_enabled=True` pero `digest_enabled=False` nunca purga nada, y mensajes `status='new'`/`is_spam=True` nunca se purgan sin importar antigüedad. `Order`, `PaymentLog`, `EmailOutbox` no tienen ninguna política de retención.
- **Transferencia internacional**: Neon/Render/Cloudinary procesan datos fuera de Chile sin Cláusulas Contractuales Tipo ni DPA documentado en el repo — bloqueado, entre otras cosas, por la discrepancia de proveedor de §1.3 (no se puede firmar el DPA correcto sin saber con certeza quién procesa los datos).
- **Logging de PII**: `apps/accounts/views.py` (login fallido y caso "email inexistente"), `apps/orders/views.py`, `views_onboarding.py`, `mercadopago_service.py` interpolan emails de comprador en logs de texto plano a stdout sin redacción — además de fuga de PII a logs retenidos/buscables en Render, es un patrón de **user enumeration**.

---

## 2. Tablero Kanban de Ejecución (Priorizado)

| Prioridad | Épica | Tarea (User Story) | Archivos a Intervenir | Criterio de Aceptación |
| :--- | :--- | :--- | :--- | :--- |
| 🚨 CRÍTICO | Seguridad | Como admin del sistema, quiero que el Django Admin de `Order`/`PaymentLog`/`ClientEmailSettings` no muestre datos de otros tenants a staff sin ese scope. | `apps/orders/admin.py`, `apps/tenants/admin.py` | `OrderAdmin`, `PaymentLogAdmin`, `ClientEmailSettingsAdmin` heredan `TenantAdminMixin` (mismo patrón que `apps/website/admin.py::SectionAdmin`); test que crea 2 tenants y verifica que un staff no-superuser scoped a tenant A no ve queryset de tenant B. |
| 🚨 CRÍTICO | Seguridad | Como responsable de datos, quiero que las credenciales SMTP/API de terceros no queden en texto plano en la base de datos. | `apps/tenants/models.py::ClientEmailSettings`, `apps/tenants/admin.py`, migración nueva | `smtp_password`/`api_key` cifrados en reposo (ej. `django-cryptography`/Fernet); `help_text` deja de mentir; test que verifica que el valor crudo en DB no es el texto plano ingresado. |
| 🚨 CRÍTICO | Seguridad | Como responsable de compliance, quiero que ningún email de usuario quede interpolado en texto plano en los logs de login/pagos. | `apps/accounts/views.py`, `apps/orders/views.py`, `apps/orders/views_onboarding.py`, `apps/orders/services/mercadopago_service.py` | Logs usan un identificador no reversible (hash/ID) en vez de email crudo; caso "email inexistente" en login/reset ya no distingue de "password incorrecta" en el mensaje ni en timing; test que audita que `caplog`/`assertLogs` no contiene un email literal. |
| 🔴 ALTO | Mantenibilidad/Seguridad | Como developer, quiero que solo exista una implementación real de login para no mantener código roto sin test. | `config/urls.py`, `apps/accounts/views.py`, `apps/accounts/models.py::UserProfile`, `apps/accounts/tests/` (nuevo) | Resuelta la colisión `/auth/` (`apps.accounts.urls` vs `apps.website.auth_urls`) de forma explícita (eliminar o remontar uno); `is_invitation_valid()`/`generate_invitation_token()`/`clear_invitation()`/`last_login_at` implementados en `UserProfile` o las llamadas eliminadas; `apps/accounts` pasa de 0 a cobertura ≥70% (mínimo del kanban del proyecto). |
| 🔴 ALTO | Compliance Ley 21.719 | Como visitante, quiero dar consentimiento explícito y no pre-marcado antes de enviar mis datos de contacto u onboarding. | `apps/website/forms.py::ContactForm`, `apps/website/models.py::ContactSubmission`, `apps/orders/forms.py::ClientOnboardingForm`, `templates/partials/contact_form.html`, template de política de privacidad (nuevo) | Checkbox no pre-marcado + timestamp + versión de política guardados en `ContactSubmission`; link real a política de privacidad (ya no `href="#"`) en `templates/partials/contact_form.html` y footer. |
| 🔴 ALTO | Compliance Ley 21.719 | Como titular de datos, quiero poder solicitar exportación o bloqueo de mis datos personales. | `apps/accounts/models.py::UserProfile` (nuevos campos), management command o vista admin scoped (nuevo) | Comando/endpoint que exporta en JSON estructurado los datos de un `UserProfile`+`Order`+`ContactSubmission` asociados; campo de bloqueo (`is_blocked_at`) que impide login/tratamiento; documentado el SLA de respuesta (30 días corridos). |
| 🟡 MEDIO | Compliance Ley 21.719 | Como responsable de retención, quiero una política de purga uniforme y sin el bug actual de `digest_enabled`. | `apps/tenants/management/commands/send_contact_digest.py::_purge_old_contacts`, `apps/orders/models.py`, `apps/core/models.py::EmailOutbox` | Purga de `ContactSubmission` corre según `auto_purge_enabled` independiente de `digest_enabled`; se define y automatiza (cron) una política de retención para `Order`/`PaymentLog`/`EmailOutbox`. |
| 🟡 MEDIO | Compliance Ley 21.719 | Como negocio, quiero saber con certeza qué proveedor procesa la base de datos para poder firmar el DPA correcto. | `CLAUDE.md`, `Documentacion/README.md`, contrato/DPA (fuera de código) | Confirmado contra el dashboard real de Render cuál `DATABASE_URL` está activa; wording de "Supabase" corregido consistentemente; DPA/Model Clauses gestionados con Neon/Render/Cloudinary. |
| 🟡 MEDIO | Optimización Mercado Pago / Negocio | **Decisión ya tomada (2026-09-21, ver §4.4): no es suscripción mensual.** Modelo real = pago único (creación) + mantención incluida 12 meses + renovación anual negociada según servicio entregado. `Plan.renewal_price` (`help_text="Precio mensual de renovación (futuro)"`) y el docstring de `Plan` (`"Escalabilidad a suscripciones recurrentes"`) describen un modelo distinto al vigente. | `apps/orders/models.py::Plan` (`renewal_price`, docstring), `apps/orders/management/commands/setup_plans.py`, `apps/tenants/models.py::Client` (`next_payment_due`) | `renewal_price` renombrado/redocumentado como precio de renovación **anual**, no mensual; `next_payment_due` pasa a significar "fin de período de mantención"; sin cron de desactivación automática (la renovación es negociada, no cobro automático) — en su lugar, un comando o alerta que liste clientes con `next_payment_due` a ≤30 días para gestión manual/comercial. |
| 🟡 MEDIO | Negocio | Como negocio, quiero que los límites de plan (`max_images`/`max_pages`/`max_services`) tengan efecto técnico real. | `apps/website/views.py` (vistas de creación de `Service`/`Section`/`GalleryItem`) | Cada vista de creación de contenido verifica la cuota del `Client.plan` antes de guardar; test que verifica 403/mensaje de error al superar la cuota. |
| 🟡 MEDIO | Negocio/Legal | Como negocio, quiero que la cláusula comercial de "mantención" y de "fin de servicio (descarga/reubicación)" tenga alcance escrito antes de firmarla con el próximo cliente — ver §4.5, no aplica a ningún archivo de código. | Documento contractual nuevo (fuera del repo o en `Documentacion/`) | Cláusula de mantención lista con incluido/no incluido + tope de horas mensuales; cláusula de fin de servicio que define "reubicación" como export estático del frontend por defecto (no migración de backend), con piso de precio ya decidido antes de cotizarlo a un cliente real. |
| 🟢 BAJO | Negocio/Observabilidad | Como negocio, quiero una alerta antes de quedarme sin créditos Cloudinary del free tier, en vez de descubrirlo con un upload fallido en producción — ver §4.2. `CLOUDINARY_ALERT_THRESHOLDS`/`CLOUDINARY_DEFAULT_LIMITS` están definidos en settings pero **cero referencias en `apps/`** (confirmado por grep). | `config/settings/cloudinary_settings.py`, management command nuevo (ej. `check_cloudinary_usage`) | Comando (o tarea programada) que llama `cloudinary.api.usage()`, compara contra `CLOUDINARY_ALERT_THRESHOLDS` y notifica (email/log) al cruzar 70/85/95%; documentado como corriendo con la misma cadencia que `send_pending_emails` en `render.yaml`. |
| 🟢 BAJO | DX/Despliegue | Como developer, quiero que el código muerto no infle la superficie de auditoría. | `config/settings/cloudinary_settings.py`, `apps/orders/services/order_processor.py::OrderProcessor`, `requirements.txt` (`djangorestframework`) | Archivos/dependencia eliminados o, si se decide mantener como roadmap, documentados explícitamente como no-en-uso en el propio archivo; `makemigrations --check --dry-run` y suite completa siguen en verde. |
| 🟢 BAJO | DX/Despliegue | Como equipo, quiero observabilidad real antes de escalar a más de un dyno. | `config/settings/production.py` (`CACHES`), `apps/core/rate_limit.py::RateLimiter`, health check (nuevo), integración Sentry (nuevo) | `RateLimiter` usa cache compartida (Redis) en vez de `LocMemCache`; `/health/` verifica conectividad real a DB/Cloudinary; Sentry (o equivalente) capturando excepciones no manejadas. |

---

## 3. Viabilidad Comercial y Estrategia de Mercado

> Consolidado 2026-09-21, análisis de posicionamiento B2B para AndesScale como studio de desarrollo/automatización con arquitectura preparada para Ley 21.719. Foco 3-6 meses. No es diagnóstico de código — es la capa de negocio que enmarca las decisiones de pricing de §4.

### 3.1 Diferenciación frente a la competencia

- **Vs. agencias web tradicionales**: no competir en sitios informativos ($300-800 USD, 2 semanas) — es una trampa de posicionamiento donde AndesScale pierde por precio y velocidad. La ventaja real aparece recién cuando el cliente ya superó "necesito una página" y está en "necesito que mi negocio deje de depender de copiar datos a mano entre sistemas": ticket 5-10x mayor, segmento más chico.
- **Vs. No-Code (Make/Zapier/n8n)**: acá está el riesgo real, no la ventaja fácil. El 80% de lo que una PYME necesita en su primer año de automatización (formulario→CRM, notificación de stock, sync de planillas) lo resuelve Make por US$30-50/mes sin código. El argumento de Python-sobre-No-Code solo es defendible cuando: (a) el volumen rompe los límites de ejecución de las plataformas no-code, (b) hay lógica condicional compleja que en Make se vuelve indebuggeable, o (c) hay requisitos de seguridad/trazabilidad de datos que una SaaS de terceros no puede garantizar (esto último conecta directo con §1.4/Ley 21.719).
- **Vs. consultoras de compliance legal**: ellas venden tranquilidad jurídica (informe, política de privacidad, capacitación) sin tocar código. AndesScale vende algo que ellas no pueden: arquitectura que hace estructuralmente imposible cierto tipo de incumplimiento (minimización de datos, logs de acceso, retención automatizada — hoy gaps reales según §1.4). Es venta educativa, no venta directa: casi ninguna PYME chilena distingue hoy "tengo una política de privacidad" de "mi sistema no puede filtrar datos por diseño".

**Ángulo defendible**: no "hacemos automatización" ni "cumplimos la ley" por separado — la intersección: automatización que maneja datos personales de forma segura por diseño. Angosta pero propia. Fuera de esa intersección, se compite en mercados donde se pierde por precio o velocidad.

### 3.2 Viabilidad a 90-180 días

- **La Ley 21.719 no debe ser el gancho de venta principal hoy.** La fiscalización efectiva lleva retraso respecto al cronograma original (patrón ya visto en Chile con otras leyes regulatorias — prórroga tras prórroga). Usarla como gancho de miedo expone a tres problemas: el dueño de PYME ya está inmunizado a mensajes de miedo regulatorio, el argumento tiene fecha de vencimiento (colapsa el día que se anuncie una prórroga), y el miedo regulatorio genera consultas gratis sin conversión. **La ley debe ser un atributo estructural silencioso** (el "ah, y esto ya cumple con la ley nueva" que cierra con el cliente más sofisticado), no la apertura de la conversación con el 90% del mercado.
- **Mensaje a la PYME sin tecnicismos**: nunca "Python"/"API"/"backend"/"arquitectura" en la primera conversación. Hablar en horas y plata ("hoy alguien de tu equipo pasa 8 horas/semana copiando pedidos entre sistemas — eso se recupera en un mes"). La tecnología es el "cómo", nunca el "qué" — al cliente no le importa el cómo.

### 3.3 Posicionamiento y cobro

"**Studio de Automatización y Plataformas**" gana el ciclo de venta corto (<30 días) sobre "Consultora Tecnológica de Escalabilidad" — este último activa el reflejo de pedir tres cotizaciones y comparar dos meses. Reservar "consultora" para el producto de entrada de ticket bajo (auditoría/diagnóstico, §3.5), donde sí calza con lo que se vende en ese momento.

**Productización — la única forma de no vivir cobrando por hora**: paquetes ("Sprints") de alcance fijo, tiempo fijo, precio fijo. El margen sale de la repetición (la segunda vez que se arma el mismo sprint toma ~40% del tiempo original por reuso de componentes) — cobrar por hora regala esa eficiencia al cliente. Cobro sugerido: 50% al firmar, 50% contra entrega (el capital de trabajo de un studio de 1-3 personas no aguanta floats de 30-60 días). Resistir personalizar "solo un poco" cada sprint — eso rompe la productización y devuelve a cobrar por hora disfrazado.

### 3.4 Matriz de riesgos a 6 meses

| # | Riesgo | Probabilidad | Impacto | Mitigación concreta |
|---|--------|--------------|---------|----------------------|
| 1 | **Confusión de posicionamiento**: el mercado no distingue si AndesScale es un desarrollador, una agencia o un consultor legal — ciclo de venta se alarga por educación, no por objeción de precio. | Alta | Alto | Un solo mensaje de entrada por segmento de cliente; no mezclar "compliance" y "automatización" en la misma pieza de marketing hasta validar cuál convierte mejor (testear por separado en las primeras 8-10 conversaciones de venta). |
| 2 | **Commoditización por No-Code**: un prospecto compara la cotización con un plan de Make y no entiende por qué pagar 20x más. | Alta | Alto | Calificar leads antes de cotizar (volumen de datos, complejidad de reglas, sensibilidad de datos) antes de agendar reunión; si el caso es simple, derivarlo o resolverlo como servicio de menor ticket en vez de forzar una venta de Python que no se va a ganar. |
| 3 | **Concentración en una sola persona (bus factor)**: sin continuidad de entrega si el fundador se enferma o hay 2-3 clientes simultáneos — techo duro de ingresos. | Media-Alta (a 6 meses si hay 2-3 clientes simultáneos) | Alto (financiero) | Documentar cada sprint como plantilla reproducible desde el sprint #1, no al final, para que un desarrollador subcontratado pueda ejecutar el 70% sin el fundador. Evaluar a los 90 días si el pipeline justifica sumar a alguien part-time. |
| 4 | **Promesa de "descarga/reubicación" no calza con la arquitectura multi-tenant compartida** (detalle técnico completo en §4.5) — riesgo de disputa contractual con un cliente que no renueva. | Media | Medio-Alto | Cláusula contractual explícita antes del primer cliente que no renueve (§2, fila Negocio/Legal), no reactivamente. |
| 5 | **"Mantención" sin alcance escrito se vuelve soporte gratuito ilimitado** — el margen de infraestructura es bueno (§4.1) pero se lo come el tiempo no cobrado. | Alta | Alto | Definir por escrito incluido/no incluido + tope de horas mensuales antes de cerrar el primer contrato bajo este modelo. |

### 3.5 Plan de acción — Sprints de entrada (30/60/90 días)

Tres ofertas de entrada, ticket ascendente, diseñadas para validar disposición a pagar rápido, no para maximizar margen en el primer trimestre:

1. **"Auditoría de Fugas Operativas" (días 0-30, ~US$150-300, 3-5 días de entrega)**: diagnóstico **pagado** (no gratis — un diagnóstico gratis no valida nada, solo genera curiosos) que identifica 3 procesos manuales automatizables con estimación de horas/mes ahorradas y ROI. Es el lead magnet real: bajo riesgo para el cliente, pipeline calificado para los sprints 2 y 3. Meta: 8-10 auditorías vendidas en 30 días para validar mensaje.
2. **"Automatización de un Flujo Crítico" (días 30-60, ~US$800-1500, 2 semanas)**: ejecuta uno de los hallazgos de la auditoría — conectar dos sistemas, automatizar un reporte, eliminar una tarea manual repetitiva. Meta: convertir 30-40% de las auditorías del Sprint 1 — esa tasa es la métrica real de si el modelo funciona.
3. **"Fundación de Datos Segura" (días 60-90, ~US$2000-4000, 3-4 semanas)**: la plataforma/SaaS con arquitectura privacy-by-design, para el cliente que ya compró los sprints 1 y 2 y confía en la ejecución. Único punto donde se menciona explícitamente la Ley 21.719 — cierre para el cliente más grande/sofisticado, no apertura para el mercado masivo.

**Métrica de decisión a los 90 días**: si el Sprint 1 no convierte a Sprint 2 en al menos 25-30% de los casos, el problema no es precio ni mensaje — es que el segmento de cliente elegido no tiene el dolor asumido, y hay que repensar el ICP antes de invertir en construir el Sprint 3.

---

## 4. Modelo Comercial, Pricing y Costos de Infraestructura

> Consolidado 2026-09-21 a partir de un análisis de viabilidad comercial + auditoría de costos reales del stack. No repite el detalle de §1 (arquitectura) ni de `Documentacion/Informe_Cumplimiento_Ley21719.md` (legal) — los conecta con el modelo de negocio real y dónde el código ya no coincide con él.

### 4.1 Costo real de infraestructura — piso operativo compartido, no por cliente

La arquitectura es multi-tenant de **despliegue único** (§1.1): un mismo Django sirve a todos los tenants. Esto significa que el costo de infraestructura es casi fijo y se reparte entre todos los clientes activos, no lineal por cliente — ventaja de margen estructural frente a una agencia que levanta un hosting por cliente.

| Servicio | Uso en el código | Costo confirmado / referencia |
|---|---|---|
| **Render** (hosting web) | `gunicorn`+`whitenoise`, un solo web service (`render.yaml`) | **Plan PRO activo, $29.78/mes total facturado** (dato real del dashboard, 2026-09-21) — no coincide exactamente con la tarifa pública genérica de Workspace Pro ($25/mes flat) ni con Starter ($7/mes); confirmar en el dashboard si el excedente son horas de Postgres gestionada por Render, egress, o el add-on del cron de `send_pending_emails`. Pendiente de desglose exacto, no bloqueante. |
| **Postgres** | `dj_database_url` — proveedor real sin confirmar entre Neon/Render Postgres gestionada (§1.3, discrepancia ya documentada) | Neon: 0.5GB + 100 CU-hora/mes gratis permanente; pagado desde $0.106/CU-hora + $0.35/GB sin piso mensual. Si es Postgres de Render, ya está incluido/aparte del monto de 4.1 — mismo pendiente de desglose. |
| **Cloudinary** (media) | `django-cloudinary-storage`; límites por tenant en `config/settings/cloudinary_settings.py::CLOUDINARY_DEFAULT_LIMITS` (50 archivos / 100MB / 10MB por archivo) | Free: 25 créditos/mes compartidos entre **todos** los tenants (1 crédito = 1GB storage **o** 1GB bandwidth **o** 1000 transformaciones). El límite real que se agota primero son las transformaciones (cada preset de `CLOUDINARY_PRESETS` cuenta), no el storage — ver hallazgo §4.2. |
| **Zoho Mail** (SMTP transaccional) | Obligatorio para arrancar — `production.py` no levanta sin `EMAIL_HOST_USER`/`PASSWORD` (mismo patrón fail-fast que `SECRET_KEY`) | Sin free permanente; Mail Lite ~US$1/usuario/mes. |
| **Mercado Pago** (cobros) | `mercadopago==2.3.0`, `apps/orders/services/mercadopago_service.py` | Sin costo fijo — comisión 3,19%+IVA (acreditación instantánea) o 2,89%+IVA (10 días) sobre cada cobro; 2,59%/2,29% si la cuenta de cobro es nueva. |
| **Dominio .cl** (incluido "primer año" en Plan Pro/Enterprise, ver `setup_plans.py`) | No hay integración de compra de dominios en el repo — es gestión manual | NIC Chile: ~$9.940 + IVA (~$11.828 CLP) por año de registro directo; renovación al mismo valor. Costo marginal bajo frente al ticket de $250.000-450.000 CLP de esos planes, pero es un costo recurrente real que hay que trackear por cliente, no asumir "gratis". |

Sources: [Render Pricing](https://render.com/pricing) — [Neon plans](https://neon.com/docs/introduction/plans) — [Cloudinary pricing](https://cloudinary.com/pricing) — [Comisiones Mercado Pago Chile 2026](https://comocobro.cl/medios-de-pago/mercado-pago) — [Tarifas NIC Chile](https://www.nic.cl/dominios/tarifas.html)

### 4.2 Hallazgo: las alertas de consumo Cloudinary existen en settings pero no están conectadas a nada

`CLOUDINARY_ALERT_THRESHOLDS` (70/85/95%) y `CLOUDINARY_DEFAULT_LIMITS` están definidos en `config/settings/cloudinary_settings.py` pero **cero referencias en `apps/`** (confirmado por grep) — no hay ningún management command, señal, ni vista que los use. Hoy no hay forma de enterarse de que se está por agotar el free tier de Cloudinary hasta que un upload falle en producción para un cliente real. Card nueva en el Kanban (§2, fila 🟢 BAJO Negocio/Observabilidad).

### 4.3 Los planes comerciales SÍ existen en código — el gap es enforcement, no diseño

`apps/orders/models.py::Plan` + `apps/orders/management/commands/setup_plans.py` ya definen 3 planes con quotas diferenciadas reales: **Esencial** ($150.000 CLP, 5 páginas/10 servicios/30 imágenes/50MB, sin dominio propio), **Pro** ($250.000 CLP, 10/20/100/200MB, dominio .cl incluido primer año, analytics), **Enterprise** ($450.000 CLP, 50/100/500/1000MB, white-label, backup diario). Esto ya es una base de pricing por alcance de servicio razonable — no hace falta rediseñarla desde cero.

El gap real (ya registrado en el Kanban, fila 🟡 MEDIO Negocio §2) es que **ninguna vista de creación de contenido verifica esas quotas** — `Client.plan.max_images`/`max_pages`/`max_services` no tienen efecto técnico. Vender "Plan Esencial: hasta 30 imágenes" hoy es una promesa comercial sin respaldo en el código; un cliente Esencial puede subir tantas imágenes como el límite *global* de Cloudinary lo permita (§4.1), no el límite de su plan.

### 4.4 El modelo de pago real: pago único + mantención 12 meses + renovación anual negociada

Decisión de negocio confirmada 2026-09-21: **no es suscripción mensual**. Es pago único que cubre creación + mantención durante 1 año; al cumplirse el año, la renovación se negocia según el servicio entregado (no hay cobro automático). Si el cliente no renueva, tiene la posibilidad de descarga/reubicación de su sitio, a un precio a negociar aparte (no incluido en el pago original). Mismo esquema aplica a scripts/automatizaciones (creación + mantención, sin cobro recurrente automático).

Esto **no coincide** con lo que el código actual describe:
- `Plan.renewal_price` tiene `help_text="Precio mensual de renovación (futuro)"` — dice mensual, el modelo real es anual.
- El docstring de la clase `Plan` dice *"Desacoplado de tenants para permitir: Escalabilidad a suscripciones recurrentes"* — describe un modelo de suscripción automática que no es el vigente.
- `Client.next_payment_due` (`apps/tenants/models.py:83`) existe pero su semántica de uso real (¿fin de mantención? ¿próxima renovación negociada?) no está documentada en el modelo.

Corrección aplicada al Kanban §2 (fila `Optimización Mercado Pago / Negocio`): redocumentar `renewal_price` como precio de renovación **anual**, resignificar `next_payment_due` como "fin de período de mantención", y reemplazar la idea de cron de desactivación automática por un comando/alerta de clientes próximos a vencer para gestión comercial manual — coherente con que la renovación es negociada, no un cobro automático tipo SaaS puro.

### 4.5 Riesgo contractual: "descarga y reubicación" no tiene soporte técnico real

La arquitectura de `apps/tenants/template_loader.py::TenantTemplateLoader` (§1) resuelve el sitio de un cliente combinando su fila en una base de datos compartida, un tema que probablemente comparte con otros tenants, y componentes en `templates/components/` explícitamente compartidos por diseño (`CLAUDE.md`). **No existe un "sitio" como carpeta autocontenida descargable.** Prometer "descarga y reubicación" sin acotar el alcance es prometer, en el peor caso, un re-despliegue completo de un tenant a un codebase independiente — un proyecto de desarrollo, no una descarga.

Acción: la cláusula contractual (Kanban §2, fila 🟡 MEDIO Negocio/Legal, nueva) debe fijar por defecto que "reubicación" = export estático del frontend renderizado (sin backend dinámico: sin formularios, sin checkout, sin panel admin), y que cualquier otra cosa (migrar el backend, separar el tenant a un despliegue propio) es un proyecto nuevo cotizado aparte — con un piso de precio decidido de antemano, no improvisado frente a un cliente que no renovó.

---

## 5. Flujo de Trabajo y Matriz de Prompts MCP

### 5.1 Estrategia MCP

El GitHub MCP Server oficial (`github/github-mcp-server`) ya está activo en este repo como binario local + PAT (`.mcp.json` en la raíz, detallado en `MANUAL_MCP_GITHUB.md`) — la variante remota con OAuth no es viable hoy (`Incompatible auth server: does not support dynamic client registration`, incompatibilidad conocida, no error de configuración). Tools relevantes para ejecutar el tablero de la sección 2 sin salir de la sesión de Claude Code:

| Tool MCP | Uso en este flujo |
|---|---|
| `list_branches` / `create_branch` | Crear una branch de feature por card del kanban (ej. `fix/AUD-XX-tenant-admin-mixin`) partiendo de `develop`. |
| `list_commits` / `get_commit` | Verificar antes de cerrar una card si `develop` está actualizada respecto a `origin` (regla de `CLAUDE.md`: "Sincronización antes de cerrar o cambiar de rama"). |
| `create_pull_request` | Abrir el PR hacia `develop` al cerrar una tanda de commits con el mismo prefijo de card (`AUD-XX`), **solo tras confirmación explícita del usuario** — nunca de forma silenciosa. |
| `list_workflow_runs` / `get_workflow_run` | Confirmar que CI (suite completa + `tests_isolation`) pasó antes de mergear. |
| `create_issue_comment` / `list_issues` | Trazabilidad: comentar en el issue correspondiente qué commit/PR resolvió cada fila del kanban. |

Reglas operativas ya vigentes en `CLAUDE.md` §"Automatización Git/GitHub (MCP)" que todo agente debe seguir al ejecutar estas cards — no son nuevas, se reafirman porque son las que hacen seguro delegar esto a un agente:

1. **Nunca** hacer `cherry-pick` hacia `develop` sin mostrar antes el diff exacto (`git show <sha>`) y pedir confirmación explícita por commit (o por tanda ya aprobada).
2. **Nunca** abrir un PR de forma silenciosa — preparar título/resumen de los commits incluidos y confirmar con el usuario antes de `create_pull_request`.
3. Antes de cerrar una card o cambiar de branch, correr `git status --short --branch` y `git log origin/<branch>..<branch> --oneline` — avisar explícitamente si hay commits sin pushear.

Patrón sugerido de ejecución por card: una branch por card (o por sub-entregable coherente, ver contrato TDD de `CLAUDE.md` §"El arnés de TDD"), un commit por card, PR hacia `develop` al cerrar cada tanda con el mismo prefijo (ej. todas las cards de la fila 🚨 CRÍTICO bajo un prefijo `SEC-XX`).

### 5.2 Prompts de Ejecución Inmediata

Los siguientes 3 prompts cubren las filas 🚨 CRÍTICO del tablero (sección 2). Cada uno sigue el contrato de TDD de `CLAUDE.md` (test rojo confirmado primero, `ruff check` + suite completa + `makemigrations --check --dry-run` en verde antes de cerrar, un commit por card, documentar cualquier hallazgo incidental).

---

**Prompt 1 — Aislamiento del Django Admin (`SEC-01`)**

```
Contexto: en apps/orders/admin.py, las clases OrderAdmin y PaymentLogAdmin no
heredan TenantAdminMixin (definido en apps/accounts/mixins.py) ni sobrescriben
get_queryset, por lo que cualquier staff con el permiso estándar de Django
"orders.view_order" puede listar y buscar (search_fields incluye billing_rut)
las órdenes de TODOS los tenants: RUT, dirección, email, IP y el payload
crudo de Mercado Pago (Order.mp_response_data). Lo mismo ocurre con
ClientEmailSettingsAdmin en apps/tenants/admin.py, que además expone
smtp_password/api_key sin scoping. El patrón correcto ya existe en
apps/website/admin.py (SectionAdmin, ServiceAdmin, ContactSubmissionAdmin),
que sí usa TenantAdminMixin con tenant_field = 'client'.

Tarea:
1. Escribe primero un test en apps/orders/tests/ (o el módulo de tests que
   corresponda) que cree dos tenants distintos con una Order cada uno, un
   usuario staff con profile.client = tenant A y permiso orders.view_order,
   y verifique que el queryset del admin de Order NO incluye la orden del
   tenant B. Confirma que el test falla en rojo contra el código actual.
2. Repite el mismo patrón de test para PaymentLogAdmin y para
   ClientEmailSettingsAdmin en apps/tenants/tests/.
3. Aplica TenantAdminMixin (o el mixin equivalente que corresponda según
   cómo esté implementado en apps/accounts/mixins.py) a OrderAdmin,
   PaymentLogAdmin y ClientEmailSettingsAdmin, ajustando tenant_field al
   nombre correcto de la FK a client en cada modelo (Order.client es
   SET_NULL — decide explícitamente cómo se comporta el filtro cuando
   client es None y documéntalo en un comentario corto si no es obvio).
4. Corre ruff check sobre los archivos tocados, la suite completa
   (python manage.py test apps -v 1) y makemigrations --check --dry-run.
5. Un commit por card. Si encuentras algo fuera de este alcance (ej. otro
   ModelAdmin sin scoping que no esté en esta lista), documéntalo como
   hallazgo incidental en el commit, no lo ignores ni abras una card nueva
   para después.
```

---

**Prompt 2 — Cifrado de credenciales de terceros (`SEC-02`)**

```
Contexto: apps/tenants/models.py::ClientEmailSettings tiene los campos
smtp_password y api_key como CharField en texto plano. El help_text de
smtp_password afirma "se almacena encriptada", pero no hay Fernet,
django-cryptography ni ningún mecanismo de cifrado en el repo (verificado
por grep) — es una discrepancia entre lo que el código documenta y lo que
hace.

Tarea:
1. Escribe primero un test en apps/tenants/tests/ que cree un
   ClientEmailSettings con un smtp_password conocido, lea el valor crudo
   directamente de la base de datos (no vía el atributo del modelo, sino
   con una query cruda o refrescando desde otra instancia) y verifique que
   NO es igual al texto plano ingresado. Confirma que este test falla en
   rojo contra el código actual.
2. Introduce cifrado en reposo para smtp_password y api_key (evalúa
   django-cryptography o un EncryptedCharField equivalente ya usado en
   requirements.txt/requirements-dev.txt si existe una dependencia
   compatible con Django 5.2; si no existe, agrégala a requirements.txt y
   documenta la nueva env var de clave de cifrado en el patrón fail-fast
   de config/settings/production.py, igual que SECRET_KEY).
3. Escribe la migración correspondiente, incluyendo una data migration si
   hace falta re-cifrar filas existentes en un entorno con datos (documenta
   si el repo tiene datos de producción reales a migrar o si es seguro
   asumir que la tabla está vacía en este punto del proyecto).
4. Corrige el help_text para que refleje la realidad una vez implementado.
5. Corre ruff check, la suite completa y makemigrations --check --dry-run.
   Un commit por card. Documenta cualquier hallazgo incidental (ej. otros
   campos de credenciales en texto plano que encuentres al revisar
   apps/tenants/models.py completo).
```

---

**Prompt 3 — Dejar de loguear PII en texto plano (`SEC-03`)**

```
Contexto: apps/accounts/views.py, apps/orders/views.py,
apps/orders/views_onboarding.py y apps/orders/services/mercadopago_service.py
interpolan el email del usuario/comprador directamente en mensajes de log
de texto plano (logger.info/warning/error con el email como parte del
string). El caso más grave está en apps/accounts/views.py: se loguea el
email tanto en login fallido como en el caso "email inexistente", lo que
además de ser una fuga de PII a logs que Render retiene y son buscables,
es un patrón de user enumeration explotable si un atacante llega a tener
acceso a esos logs o si el timing/contenido del log correlaciona con la
respuesta HTTP.

Tarea:
1. Escribe primero un test que dispare un intento de login fallido (email
   inexistente y también email existente con password incorrecta) usando
   el logging framework de Django (assertLogs / caplog) y verifique que
   ningún registro de log contiene el email literal usado en el intento.
   Confirma que el test falla en rojo contra el código actual para al
   menos apps/accounts/views.py.
2. Repite el mismo tipo de test (adaptado al flujo correspondiente) para
   apps/orders/views.py, apps/orders/views_onboarding.py y
   apps/orders/services/mercadopago_service.py donde se logue el email del
   comprador.
3. Reemplaza la interpolación directa del email en los logs por un
   identificador no reversible (ej. el id numérico del Order/User, o un
   hash truncado) o elimina el dato del mensaje si no aporta valor de
   debugging real. NO cambies el mensaje de respuesta HTTP al usuario final
   sin verificar primero si ya es genérico (evita introducir tú mismo un
   vector de enumeración nuevo al "arreglar" el mensaje de error visible).
4. Corre ruff check sobre los archivos tocados, la suite completa y
   makemigrations --check --dry-run (no debería generar migraciones, es un
   cambio de logging puro — confírmalo).
5. Un commit por card, o uno por archivo si prefieres separarlos por
   claridad de revisión (decide y sé consistente). Documenta como hallazgo
   incidental cualquier otro logger.* con PII que encuentres fuera de los
   4 archivos listados arriba.
```
