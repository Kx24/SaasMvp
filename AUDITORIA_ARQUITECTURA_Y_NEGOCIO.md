# Auditoría de Arquitectura y Negocio — AndesScale SaaS

> Análisis técnico y estratégico basado en el código real del repositorio (Django 5.2, multitenant) a la fecha de este documento. Tono directo: se identifican fortalezas donde las hay, pero el foco es riesgo técnico, riesgo legal (Ley 21.719) y riesgo de negocio. Cada afirmación cita archivo/clase/función. Donde existe un documento interno previo (`Documentacion/Informe_Cumplimiento_Ley21719.md`, `Documentacion/KANBAN_PROYECTO.md`) que ya identifica el mismo problema como pendiente, se cita explícitamente para no duplicar trabajo de diagnóstico — este informe verifica cuánto de ese roadmap ya está implementado en código (respuesta corta: casi nada de la capa legal, bastante de la capa de pagos/aislamiento básico).

---

## 1. Diagnóstico objetivo de la arquitectura actual

### 1.1 Stack y calidad de separación de capas

Django 5.2 monolítico, 6 apps con responsabilidades razonablemente bien separadas (`tenants`, `accounts`, `website`, `orders`, `marketing`, `core`). No hay API REST real pese a que `djangorestframework==3.15.1` está en `requirements.txt` — **no está en `INSTALLED_APPS`** (`config/settings/base.py`), no existe un solo `serializers.py` ni `viewsets`/`APIView` en todo el repo. Es una dependencia instalada y nunca usada: o se elimina, o se documenta como intención de roadmap para una API pública futura, pero no debería quedar en el limbo — aumenta la superficie que un auditor de seguridad o de compliance tiene que revisar sin necesidad.

Deuda de arquitectura concreta encontrada:

- **`apps/orders/services/order_processor.py::OrderProcessor`** es una capa de orquestación alternativa (`create_order`, `process_successful_payment`, `complete_onboarding`) que el flujo real (`apps/orders/views.py`, `apps/orders/views_onboarding.py`) no usa — construyen `Order`/`PaymentLog` inline. Dos implementaciones del mismo dominio de negocio conviviendo sin que una las reemplace es un riesgo de mantenimiento: alguien va a editar la que no corre.
- **`apps/accounts/views.py`** llama a `profile.is_invitation_valid()`, `profile.generate_invitation_token()`, `profile.clear_invitation()` y `user.profile.last_login_at` — **ninguno de estos métodos/campos existe en `UserProfile`** (`apps/accounts/models.py`). Son rutas de código potencialmente rotas (`AttributeError` en ejecución) en el flujo de login/reset de contraseña de esta app específica.
- Ese mismo riesgo queda parcialmente oculto porque `apps/accounts/urls.py` y `apps/website/auth_urls.py` están montados en el mismo prefijo `/auth/` en `config/urls.py`, y `apps.website.auth_urls` se incluye primero — las rutas `login/`/`logout/` de `apps.accounts` quedan shadowed y **nunca se ejecutan** en la práctica. El login real es `apps/website/auth_views.py::client_login`. Esto significa que el código roto de `apps/accounts/views.py` probablemente no se ha disparado en producción por accidente de orden de includes, no porque esté probado y funcionando. **`apps/accounts` no tiene un solo archivo de test** (confirmado: cero archivos `*test*` en esa app) — es la app de identidad/autenticación y es la que menos cobertura tiene.
- Duplicación de configuración de Cloudinary: `config/settings/cloudinary_settings.py` define su propio `cloudinary.config()`, `CLOUDINARY_PRESETS`, `CLOUDINARY_DEFAULT_LIMITS`, `CLOUDINARY_ALERT_THRESHOLDS` — pero **nunca se importa** desde ningún settings module (confirmado por grep). `base.py` duplica la misma configuración inline con presets distintos. Código muerto que aparenta ser la fuente de verdad y no lo es.

### 1.2 Aislamiento multi-tenant

El mecanismo es **FK explícita (`client_id`) + middleware de resolución de dominio**, no `django-tenants` ni esquemas separados ni Row-Level Security de Postgres.

- `apps/tenants/middleware.py::TenantMiddleware` resuelve `request.client` contra `Domain.objects.get(domain=host, ...)` y actúa como reemplazo dinámico de `ALLOWED_HOSTS` (que por eso vale `['*']`).
- `apps/tenants/managers.py::TenantAwareManager` **no filtra automáticamente**. El auto-filtro basado en atributo de clase se eliminó a propósito (`#MED-02`) porque era inseguro bajo concurrencia. El contrato vigente es: **cada vista debe llamar `.for_client(request.client)` explícitamente**. Esto es una decisión de diseño defendible (evita el riesgo de un atributo de clase compartido entre requests), pero tiene una consecuencia que hay que decir sin eufemismos: **un desarrollador que olvida `.for_client()` en una vista nueva no genera un error visible — genera una fuga de datos entre tenants silenciosa**. El único control que detecta esto es `apps/tenants/tests_isolation.py`, que corre en cada push pero solo cubre lo que ya se le ocurrió testear a alguien; no hay un linter ni un check estático que lo fuerce estructuralmente.
- **Hallazgo más severo de esta auditoría — aislamiento roto en el admin de Django**, no en las vistas públicas:
  - `apps/orders/admin.py::OrderAdmin` y `PaymentLogAdmin` **no heredan `TenantAdminMixin`** y no tienen `get_queryset` propio. Cualquier usuario staff con el permiso estándar de Django `orders.view_order` puede listar y buscar (`search_fields` incluye `billing_rut`) **las órdenes de todos los tenants**: RUT, razón social, dirección, teléfono, email, IP, user agent y el payload crudo de Mercado Pago (`mp_response_data`).
  - `apps/tenants/admin.py::ClientEmailSettingsAdmin` tampoco filtra por tenant. Expone `smtp_password` y `api_key` — el campo `smtp_password` tiene un `help_text` que dice "se almacena encriptada", pero es un `CharField` plano; no hay `Fernet`, `django-cryptography` ni ningún mecanismo de cifrado en el repo (confirmado por grep). Es decir: **el admin expone credenciales de terceros en texto plano, sin scoping por tenant, a cualquier staff con el permiso de Django correspondiente** — no solo a superusers.
  - `apps/marketing/admin.py::SEOConfigAdmin` tampoco filtra (impacto menor: son metadatos de negocio, no datos de personas naturales).
  - En contraste, `apps/website/admin.py` (`SectionAdmin`, `ServiceAdmin`, `ContactSubmissionAdmin`) sí usa `TenantAdminMixin` correctamente, con `tenant_field = 'client'`. El patrón correcto existe en el código — simplemente no se aplicó de forma consistente a los modelos con los datos más sensibles del sistema.
  - Esto no es un problema teórico de "algún día un staff malicioso": es la superficie de acceso que cualquier empleado con permisos de soporte/ventas tendría hoy si se le da acceso al admin para resolver un ticket de un tenant. El control de acceso real es "¿tenés el permiso de modelo de Django?", no "¿sos del tenant correspondiente?".

### 1.3 SQLite (dev) vs. Postgres (producción)

- `config/settings/development.py` hardcodea SQLite. El comentario arriba del bloque dice "Database - Neon (configuración para desarrollo local)" sobre un bloque que es SQLite puro — comentario obsoleto, no afecta funcionamiento pero confunde a quien lo lea por primera vez.
- `base.py`/`production.py` usan `dj_database_url.config(...)` leyendo `DATABASE_URL`; en producción no hay fallback a SQLite (requiere la env var).
- **Discrepancia de proveedor sin resolver**: `CLAUDE.md` dice "Supabase/Postgres"; `Documentacion/README.md` dice "Neon"; `render.yaml` provisiona su propia Postgres gestionada por Render (`databases: saasmvp-db`) sin connection string externa visible en el repo. El propio `KANBAN_PROYECTO.md` (línea 48, sección "Retomar aquí") ya lo reconoce: *"la base de producción es Neon, no Supabase como dice el resto de este documento; corrección pendiente"*. Es un detalle menor de higiene documental, salvo por un punto que sí importa para la sección 2: **el proveedor real de base de datos determina la jurisdicción de transferencia internacional de datos**, y hoy ni la documentación interna se pone de acuerdo en cuál es.
- Riesgo técnico real de compatibilidad SQLite↔Postgres: bajo. No se detectaron features Postgres-específicas (sin `ArrayField`, sin búsqueda full-text nativa). Los `JSONField` en uso (`Order.mp_response_data`, `Plan.features`, `SEOConfig.schema_json`) funcionan en ambos motores; el único riesgo es que SQLite es más permisivo con estructuras JSON malformadas que Postgres, así que un bug de shape de JSON puede pasar desapercibido en dev y aparecer recién en producción.

---

## 2. Auditoría técnica para cumplimiento de la Ley 21.719

**Contexto de partida**: ya existe un documento interno de intención — `Documentacion/Informe_Cumplimiento_Ley21719.md` — que identifica correctamente el marco legal (rol de AndesScale como Responsable sobre datos propios y Encargado sobre datos de tenants, Art. 15 bis de responsabilidad solidaria, plazo del 1-dic-2026, sanciones hasta 20.000 UTM). Es un buen diagnóstico legal. Lo que sigue es la verificación de **cuánto de ese plan ya está en el código**: la respuesta, con evidencia, es que casi nada.

### 2.1 Mapeo de datos personales (dónde vive qué)

| Dato | Modelo / campo | Sensibilidad |
|---|---|---|
| RUT, razón social, dirección, comuna | `apps/orders/models.py::Order` (`billing_rut`, `billing_razon_social`, `billing_direccion`, `billing_comuna`) | Alta |
| Email, nombre, teléfono comprador | `Order.email`, `.buyer_name`, `.buyer_phone` | Alta |
| IP, user agent (comprador) | `Order.ip_address`, `.user_agent` | Media-alta |
| IP, payload crudo de pago | `apps/orders/models.py::PaymentLog` (`ip_address`, `raw_data`) | Alta |
| Nombre, email, teléfono, IP, UA (leads) | `apps/website/models.py::ContactSubmission` | Alta |
| Credenciales SMTP / API key de terceros | `apps/tenants/models.py::ClientEmailSettings` (`smtp_password` — texto plano pese al help_text, `api_key`) | Crítica (credencial, no solo dato personal) |
| Cuerpo completo de emails transaccionales | `apps/core/models.py::EmailOutbox` (`html_content`, `text_content`) — sin campo de retención, sin purga | Alta |
| Email/teléfono de contacto del tenant | `apps/tenants/models.py::Client.contact_email/phone`, `ClientSettings.contact_email/phone/address` | Media |

### 2.2 Derechos ARCOP y portabilidad

**No existe ningún mecanismo de ARCOP implementado en código.** Grep de `export_data`, `delete_user`, `anonymize`, "portabilidad" sobre todo el repo: cero resultados fuera de los propios documentos de roadmap (`Documentacion/Informe_Cumplimiento_Ley21719.md`, `AGENTE_SPEC.md`). Específicamente:

- El memo interno pide (Art. 8 ter / Art. 11) un campo `is_blocked_at` + flag `status_blocked` en el modelo de usuario, con un trigger que bloquee tratamiento en 2 días hábiles ante solicitud. **No existe en `apps/accounts/models.py::UserProfile` ni en `User`.**
- El memo pide (Art. 4-9) una interfaz de dashboard para que el usuario descargue o pida supresión de sus datos, con respuesta legal en 30 días corridos. **No existe ninguna vista, endpoint ni management command para esto.**
- Card #57 del memo pide `SoftDelete` para preservar integridad referencial ante supresión. **No hay soft-delete en ningún modelo** — todos los `delete()` son físicos por defecto de Django.
- Card #54/nueva-#54 pide exportación en JSON estructurado para portabilidad. No existe.

Esto no es un matiz — es la diferencia entre "tenemos un plan" y "tenemos la obligación legal implementada". Con vigencia el 1-dic-2026, este es el gap más grande del informe en términos de exposición legal directa.

### 2.3 Logs, trazabilidad y consentimiento

**Auditoría/trazabilidad:**
- El único modelo tipo audit-log es `apps/orders/models.py::PaymentLog`, y es específico de pagos, no genérico. No existe un `AuditLog` transversal.
- `apps/accounts/mixins.py::TenantAdminMixin`/`TenantAdminReadOnlyMixin` controlan acceso en el admin pero **no registran ninguna acción** — no queda rastro de quién vio o modificó qué dato de qué tenant vía admin. Dado el hallazgo de §1.2 (admin sin scoping en `Order`/`PaymentLog`/`ClientEmailSettings`), esto es doblemente problemático: no solo cualquier staff puede ver datos cross-tenant, tampoco queda registro de que lo hizo.
- `LOGGING` (`config/settings/base.py`, `production.py`) es un `StreamHandler` a stdout sin sink externo, sin redacción de PII. Y el código sí interpola PII en los mensajes de log en texto plano: emails de comprador en `apps/orders/views.py`, `apps/orders/views_onboarding.py`, `apps/orders/services/mercadopago_service.py`; y en `apps/accounts/views.py` (líneas ~51-248) se loguea el email en **login fallido y en el caso "email inexistente"** — esto es, además de una fuga de PII a los logs (que Render retiene y son buscables), un patrón clásico de **user enumeration**: un atacante puede usar el comportamiento del sistema (o, peor, acceso a logs) para determinar qué emails existen registrados.

**Consentimiento:**
- El memo interno (Art. 12) exige explícitamente que `ContactSubmission` no se alimente de checkboxes pre-marcados y que se registre timestamp + versión de política aceptada. **Nada de esto existe.** `apps/website/forms.py::ContactForm` no tiene campo de consentimiento en absoluto — ni checkbox marcado ni desmarcado.
- Lo que sí existe es texto pasivo de disclaimer: `templates/partials/contact_form.html` ("Al enviar este formulario, aceptas nuestra política de privacidad") con un link `href="#"` — **no hay página de política de privacidad real enlazada**. Mismo patrón en el footer (`templates/andesscale/components/footer.html`).
- El flujo de checkout/onboarding (`apps/orders/forms.py::ClientOnboardingForm`) tampoco captura consentimiento/ToS en ningún punto.

### 2.4 Terceros y transferencia internacional

El propio memo interno ya lo dice con precisión quirúrgica (línea 55): *"Dado que Neon, Render y Cloudinary procesan datos fuera de Chile, y ante la ausencia de un listado oficial de 'países adecuados' [...] AndesScale debe implementar proactivamente Cláusulas Contractuales Tipo (Model Clauses) [...] de forma inmediata"*. Verificación de estado: **no implementado**. No hay evidencia en el repo de DPA, Model Clauses, ni siquiera de una página de "subprocesadores" pública. Esto es responsabilidad contractual, no de código — pero el código sí participa: cada `CloudinaryField`, cada fila en la Postgres de producción y cada request a través de Render es, hoy, una transferencia internacional de datos personales sin cobertura contractual formal documentada en el repositorio.

Nota de consistencia: la confusión Neon/Supabase/Render de §1.3 no es solo higiene documental — si el equipo no tiene claro cuál proveedor de base de datos está realmente en producción, tampoco puede firmar correctamente el DPA con el proveedor correcto.

---

## 3. Análisis del modelo de negocio e integraciones SaaS

### 3.1 Monetización e integración con Mercado Pago

**No hay cobro recurrente implementado — es pago único.** `Plan.price` está documentado como "pago único inicial"; `Plan.renewal_price` existe con `help_text="Precio mensual de renovación (futuro")` y está poblado en `apps/orders/management/commands/setup_plans.py`, pero **no se lee en ningún código de negocio** (confirmado por grep). `Client.next_payment_due` es un campo huérfano: sin cron, sin comando, sin señal que lo compare contra la fecha actual, sin lógica que desactive `Client.is_active` al vencer. El propio docstring de `apps/orders/models.py` reconoce que el diseño (`Order` desacoplado de `Client`) fue pensado para "escalabilidad a suscripciones recurrentes" — pero eso quedó en el modelo de datos, no en la lógica.

No hay dunning: `OrderProcessor.process_failed_payment()` marca la orden como `failed` y loguea, sin reintento ni notificación ni suspensión de cuenta.

Más relevante para el diagnóstico de negocio: **según `Documentacion/KANBAN_PROYECTO.md` (`#PAY-01`), Mercado Pago ni siquiera está en producción real todavía** — "resta el trámite SII de facturación". Es decir, hoy el sistema no está cobrando en producción de forma operativa. Combinado con `#DB-04` ("congelado hasta 3+ clientes pagando"), la señal de tracción es: **menos de 3 clientes pagando activos**, negocio en etapa muy temprana. Esto cambia la lectura de todo el resto del informe — no es una plataforma con escala y deuda técnica acumulada por volumen, es una plataforma pre-escala con deuda de fundamentos (aislamiento, compliance, cobro recurrente) que es barato corregir ahora y caro corregir después.

### 3.2 Gestión de medios e infraestructura (Cloudinary / Render)

Los límites de cuota existen como **configuración, no como enforcement**: `CLOUDINARY_DEFAULT_LIMITS` (max 50 items, 100MB, umbral `block=95%`) y `CLOUDINARY_ALERT_THRESHOLDS` están definidos en `config/settings/cloudinary_settings.py` (y duplicados en `base.py`) pero **nunca se importan ni se evalúan en ningún código de `apps/`**. `apps/core/cloudinary_utils.py::validate_image_file`/`validate_video_file` existen pero tampoco se llaman desde ningún upload real. `get_tenant_usage()` calcula uso por tenant pero solo es invocado manualmente vía `apps/core/management/commands/cloudinary_usage.py` (reporte de consola, no cron, no bloqueo).

Traducido a negocio: **el costo de Cloudinary escala linealmente con lo que suban los tenants, sin ningún circuit-breaker automático**. Con pocos tenants hoy esto es invisible; deja de serlo en el momento en que uno solo empieza a subir contenido pesado sin límite real.

No hay evidencia de Cloudflare en el repo (contrario a lo que asumía el brief original de este análisis) — el despliegue es directo a Render, con WhiteNoise sirviendo estáticos. No hay capa de CDN/edge cache adicional ni protección DDoS más allá de lo que Render ofrezca por defecto.

### 3.3 Escalabilidad hacia clientes Enterprise

Estado actual, sin ambigüedad: **el producto no está listo para Enterprise**, y no por falta de features de producto sino de fundamentos de plataforma:

- **Sin SSO/SAML/OAuth** — autenticación 100% Django session/password.
- **Sin API pública** — DRF instalado y sin usar (§1.1).
- **Sin cache distribuido** — `CACHES` es `LocMemCache` en producción. Esto no es solo una limitación de performance: `apps/core/rate_limit.py::RateLimiter` (el único rate-limiting real del sistema, aplicado solo al formulario de contacto) **deja de funcionar correctamente en cuanto haya más de un dyno/worker**, porque cada proceso tiene su propio contador en memoria. Escalar horizontalmente hoy rompe silenciosamente el rate-limiting.
- **Cuotas de plan no enforced**: `Client.max_images`/`max_pages`/`max_services` se copian desde `Plan` en el onboarding (`apps/orders/views_onboarding.py`) pero ninguna vista de creación en `apps/website/views.py` los verifica antes de permitir crear más contenido. Los planes de precio no tienen dientes técnicos — un tenant en el plan más barato puede consumir tanto como uno enterprise.
- **Observabilidad mínima**: sin Sentry/APM (grep negativo en todo el repo), logging solo a stdout, health check (`render.yaml`, `healthCheckPath: /`) es la home page pública, no un endpoint que verifique conectividad real a DB/Cloudinary.
- **Cobertura de tests desigual**: 104 funciones de test en 20 archivos, concentradas en `apps/orders` (pagos) y aislamiento multi-tenant — trabajo reciente y bueno donde existe. Pero `apps/marketing` y `apps/accounts` tienen **cero tests**, y `apps/accounts` es justamente la app con el código roto identificado en §1.1.

Ninguno de estos puntos es difícil de resolver individualmente. El problema es que, juntos, son exactamente el checklist que un comprador Enterprise (o su equipo de seguridad) pide en una auditoría de proveedor antes de firmar: SSO, SLA con observabilidad demostrable, aislamiento de datos verificable, rate-limiting real. Hoy el producto falla la mayoría de esos puntos por diseño, no por bug.

---

## 4. Recomendaciones técnicas y roadmap de acción

### 4.1 Crítico — acción inmediata (seguridad / refactor)

1. **Agregar `TenantAdminMixin` (o equivalente) a `OrderAdmin`, `PaymentLogAdmin` y `ClientEmailSettingsAdmin`** (`apps/orders/admin.py`, `apps/tenants/admin.py`). Es el hallazgo de mayor severidad del informe: hoy cualquier staff con permiso de Django estándar ve RUT, dirección, email, IP y credenciales SMTP/API de **todos** los tenants, no solo del propio.
2. **Cifrar `ClientEmailSettings.smtp_password` y `.api_key` en reposo** (ej. `django-cryptography`/Fernet) — el campo dice "se almacena encriptada" en su propio `help_text` y no lo está. Esto es una discrepancia entre lo que el código documenta y lo que hace, que además es exactamente el tipo de hallazgo que hunde una auditoría de seguridad externa.
3. **Dejar de loguear emails en texto plano** en `apps/accounts/views.py`, `apps/orders/views.py`, `apps/orders/views_onboarding.py`, `apps/orders/services/mercadopago_service.py` — especialmente el caso de "email inexistente" en login/reset, que es un vector de enumeración de usuarios via logs.
4. **Resolver la colisión de rutas `/auth/`** entre `apps.accounts.urls` y `apps.website.auth_urls`, y decidir cuál es el login real. Mientras convivan dos implementaciones sin resolver, el código roto de `apps/accounts/views.py` (métodos inexistentes en `UserProfile`) es una bomba de tiempo sin test que la detecte.
5. **Escribir tests para `apps/accounts` (cero hoy)** antes de tocar nada más ahí — es la app que decide quién entra al dashboard de qué tenant; es el módulo con menos justificación posible para tener cero cobertura.
6. Eliminar o documentar como intencional el código muerto que infla la superficie de auditoría: `config/settings/cloudinary_settings.py`, `apps/orders/services/order_processor.py::OrderProcessor`, la dependencia `djangorestframework` si no hay plan concreto de API pública.

### 4.2 Adecuación legal — rumbo a diciembre 2026

1. **Consentimiento explícito real**: agregar checkbox (no pre-marcado) + timestamp + versión de política en `ContactForm`/`ContactSubmission` y en `ClientOnboardingForm`, tal como ya especifica el memo interno (Art. 12, Card #55). Publicar una página de política de privacidad real y reemplazar los links `href="#"` en `templates/partials/contact_form.html` y el footer.
2. **Implementar el ciclo ARCOP mínimo viable**: un endpoint o management command de exportación de datos por sujeto/tenant en JSON estructurado (portabilidad, Art. 9), y un mecanismo de bloqueo/supresión — aunque sea manual al inicio (vía Django admin bien scoped, una vez resuelto el punto 4.1.1), es mejor que la ausencia actual total.
3. **Uniformar la retención de datos**: hoy solo `ContactSubmission` tiene purga (`apps/tenants/management/commands/send_contact_digest.py::_purge_old_contacts`), y con un bug de diseño — solo corre si `digest_enabled=True`, por lo que un tenant con `auto_purge_enabled=True` pero `digest_enabled=False` nunca purga nada, y los mensajes `status='new'`/`is_spam=True` nunca se purgan sin importar la antigüedad. `Order`, `PaymentLog` y `EmailOutbox` no tienen ninguna política de retención. Definir plazos y automatizarlos, no dejarlos acoplados como efecto secundario de un email de digest.
4. **Formalizar DPA / Model Clauses con Cloudinary, Render y el proveedor real de base de datos** — resolver primero la ambigüedad Neon/Supabase/Render de §1.3, porque no se puede firmar el acuerdo correcto sin saber con certeza quién procesa los datos.
5. Evaluar si el alcance completo del memo interno (DPO formal, Modelo de Prevención Art. 49, motor de políticas dinámicas por módulo activo) es proporcional al tamaño actual del negocio (<3 clientes pagando) — probablemente sí conviene priorizar los puntos 1-4 de esta lista sobre la certificación formal por ahora, y revisar la certificación cuando la base de tenants crezca.

### 4.3 Optimización de modelo de negocio y mantenibilidad

1. **Decidir de forma explícita si hay cobro recurrente o no.** Hoy `renewal_price`/`next_payment_due` existen en el modelo de datos sin ninguna lógica detrás — es deuda de producto, no solo de código. Si el modelo de negocio es efectivamente pago único + renovación manual, simplificar el schema; si es suscripción, construir el cron de verificación + suspensión antes de vender el segundo plan de precio.
2. **Enforce las cuotas de plan** (`max_images`/`max_pages`/`max_services`) en `apps/website/views.py` antes de que el volumen de tenants haga que esto importe — hoy los tiers de precio no tienen ningún control técnico detrás.
3. **Mover el rate-limiting y cualquier cache compartida a Redis** antes de escalar horizontalmente — `LocMemCache` rompe el `RateLimiter` en cuanto haya más de un proceso.
4. **Agregar observabilidad real** (Sentry como mínimo, health check que verifique DB/Cloudinary) — con <3 clientes pagando es el momento más barato de instrumentar esto, antes de que un incidente en producción con clientes reales sea la primera vez que el equipo se entera de un log de error.
5. **Aprovechar la etapa temprana del negocio**: con pocos tenants y datos, el costo de retrofitting de aislamiento de admin (§4.1.1), cifrado de credenciales (§4.1.2) y consentimiento/retención (§4.2) es hoy mínimo comparado con hacerlo con decenas de tenants y volumen de datos reales acumulados sin estas protecciones. La ventana entre ahora y el 1-dic-2026, y entre ahora y la primera decena de clientes pagando, es la misma ventana — conviene tratarlas como una sola prioridad, no como dos backlogs separados.
