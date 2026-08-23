# KANBAN MAESTRO — AndesScale SaaS

> **Fuente única de verdad del proyecto.** Fusiona y reemplaza:
> - `Documentacion/Planificación/Kanban_RanchoCachimba.md` (Tablero A)
> - `Documentacion/Planificación/Kanban_Plataforma_v2.md` (Tablero B)
> - `Documentacion/KanBan_RanchoCachimba.md` y `KanBan_NuevoCliente.md` (versiones históricas, solo archivo)
>
> **Generado:** 2026-08-20, a partir de una auditoría integral del código (ver §1).
> **Stack:** Django 5.2 + Tailwind/Alpine + Supabase/Render + Cloudinary.
> **Ejecución:** desarrollo desde Claude Code sobre el repo. Toda ruta es relativa a la raíz.
> **IDs:** se conservan los IDs originales (`#RC-xx`, `#DEUDA-xx`, `#TOOL-xx`, `#SEC-xx`, `#FLOW-xx`, `#DS-xx`, `#DB-xx`, `#PAY-xx`). Los hallazgos nuevos de la auditoría usan `#AUD-xx`.
>
> **Etiquetas:** Prioridad `[P0-Crítica]` `[P1-Alta]` `[P2-Media]` · Esfuerzo `[S]` `[M]` `[L]` `[XL]` · Capa `[Backend]` `[Frontend]` `[DevOps]` `[Database]`

---

## 🌙 Retomar aquí (actualizado 2026-08-23)

**Rancho Cachimba — maquetación del hero (`#RC-20`), las 6 cards `RC-BOLT-01..06` están DONE (2026-08-23).** Detalle completo, hallazgos y DoD verificado en `Documentacion/Planificación/spec_bolt_hero_cachimba.md`. Resumen: tokens CSS rotos `var(--primary/secondary/accent)` corregidos (143 usos reales, no 114 como decía el análisis original), patrón de tartán unificado en una sola clase, navbar restyleado a fondo oscuro con CTA "Reservar visita", barra de utilidad nueva sobre el navbar, stats reescrito con copy propio del rancho, CTAs del hero con copy y hovers del mockup. Gate real en verde en cada card (suite completa + `npx playwright test`, 6/6). Commits `6a43eaf`..`5af0a6c` en `feature/RanchocachimbaEtapa1`. **Hallazgo pendiente, no bloqueante:** el pill "El oficio" del hero queda oculto bajo el header fijo (navbar + barra de utilidad) — pre-existente a estas 6 cards, no corregido; falta abrir una card para revisar el offset del contenido bajo el header fijo del tema.

**El gate de seguridad de §4 está cerrado y commiteado.** `#AUD-01`, `#AUD-02`, `#AUD-03` y `#AUD-04` — los 4 bloqueadores P0 de la auditoría (checkout inalcanzable, webhook sin firma, fuga cross-tenant en login/dashboard, `render.yaml` roto) — están **DONE**, cada uno con TDD estricto (Rojo→Verde, ver detalle en §4 y §7) y verificados de punta a punta con `git stash` contra el estado original cuando aplicaba (`#AUD-04`). Commit `b5539f9` en `feature/RanchocachimbaEtapa1`. Archivos nuevos: `apps/orders/tests/`, `apps/website/tests/`, `apps/core/tests/`, `apps/accounts/decorators.py`, `ruff.toml`, `requirements-dev.txt`.

**`#AUD-05`, `#AUD-06`, `#AUD-07`, `#PAY-03` (parcial) y `#MED-02` también DONE (2026-08-22)**, mismo TDD estricto — ver §4/§5/§7. Suite: **62 tests, OK (1 skip)**. Commits: `10cf3ec` (AUD-05), `2e8b226` (AUD-06), `fabedf2` (AUD-07), `37d09c7` (PAY-03); MED-02 pendiente de commit propio.

**Hallazgos incidentales corregidos esta sesión (ninguno era el alcance original de su card, pero bloqueaban el DoD o eran riesgos reales encontrados al escribir el test):**
- `process_onboarding` llamaba `UserProfile.objects.create(...)` chocando con el signal `create_or_update_user_profile` → `IntegrityError` en **todo** onboarding real. Cambiado a `update_or_create` (AUD-06).
- `redirect('orders:onboarding_success', ...)` usaba un namespace que no existe (`urls_onboarding.py` no tiene `app_name`) → `NoReverseMatch` atrapado por un `except Exception` genérico: el cliente veía "hubo un error" aunque su sitio SÍ se había creado. Corregido a `redirect('onboarding_success', ...)` (PAY-03).
- `Order.mark_as_completed()` limpiaba `onboarding_token` justo antes de que la página de éxito lo buscara por ese mismo token → `Http404` incluso con el bug anterior arreglado. Ya no se limpia (PAY-03).
- `TenantAwareManager._current_client`: código muerto en producción (nunca se seteaba fuera del comando manual) — eliminado junto con `TenantManager`/`TenantQuerySet` (nunca usados) (MED-02).

**3 cabos sueltos menores, no bloqueantes (acción del usuario, no verificable desde el repo):**
1. `#AUD-01` — falta el caso "un plan no puede llamarse `process`/`success`/`error`".
2. `#AUD-04` — falta confirmar contra el dashboard real de Render qué configuración está efectivamente activa.
3. `#AUD-07`/`#PAY-03` — falta SPF/DKIM de Zoho + una pasada manual real contra el sandbox de MP (tarjeta de prueba + browser, requiere credenciales de test).

**Siguiente en la ruta crítica:** `#AUD-11` (consolida `#AUD-11`+`#TOOL-04`+`#DS-01`/`#DS-02`) está **DONE, 4/4 pasos (2026-08-22)** — ver detalle en §4. Resumen: Paso 1 sacó el CDN de Tailwind y armó el pipeline de build, encontrando y cerrando `#BUG-01` de paso (comentarios Django multilínea rotos, bug preexistente en 17 templates, ya en producción); Paso 2 documentó el contrato de tema en `docs/design-system.md` y corrigió una cita inexacta del precedente de componentes compartidos; Paso 3 expuso `accent_color`/`font_family` (lista curada) en `BrandingForm` del dashboard; Paso 4 retiró `tenant_custom_css` (código muerto) por completo.

`#SEC-02` (headers de seguridad) también **DONE (2026-08-22)** — quedó explícitamente desbloqueada por el cierre de `#AUD-11` (la propia card decía "complicada por Tailwind CDN — hacer después de `#AUD-11`"). Agregado CSP + Permissions-Policy vía `django-csp`/`django-permissions-policy`, solo en `production.py`. Decisión de riesgo importante: `/checkout/` queda excluido de la CSP a propósito (Checkout Bricks de MercadoPago crea iframes cuyo dominio exacto no está documentado de forma confiable — ver detalle en §5) — habilitarla ahí requiere sandbox real, mismo cabo suelto que `#AUD-07`/`#PAY-03`. Ver detalle completo en §5.

`#AUD-10` (higiene de repo) también **DONE (2026-08-22)** — ver detalle en §5. `db_production_test.sqlite3`/`exit` fuera del repo, `staticfiles/` (134 archivos) desindexado y gitignorado, CSVs de auditoría viejos eliminados (el comando que los genera ahora escribe en `scripts/output/`, gitignorado, por defecto), y test anti-regresión real (`ast` sobre el código fuente, no runtime) para que `CLOUDINARY_PRESETS`/`VIDEO_PRESETS` no vuelvan a pisarse una clave en silencio.

`#DEUDA-05` (reconciliar README/skill) también **DONE (2026-08-22)** — ver detalle en §5. `Documentacion/README.md` reescrito donde describía comportamiento que ya no existe (auto-filtro de `TenantAwareManager`, resolución de templates sin el tier `default/`, roles, env vars de MercadoPago); se creó el skill `andesscale-saas` que la card asumía existente y nunca se había hecho (`.claude/skills/andesscale-saas/SKILL.md`). Dos hallazgos incidentales (una copia muerta de `TenantAwareManager` en `apps/core/managers.py` con el mismo riesgo que `#MED-02` ya había cerrado en el archivo real; un login duplicado en `apps/accounts/views.py` inalcanzable por orden de `include()` en `config/urls.py`) — documentados, el segundo no se tocó (decisión de limpieza le corresponde al usuario). **No se pudo correr la suite completa de Django en esta sesión** (el runner de comandos bloqueó `python manage.py test` vía el clasificador de auto-mode de la sesión) — pendiente correrla manualmente para confirmar que borrar `apps/core/managers.py` no rompió nada (el `import` en frío sí funcionó).

**Lo que sigue, sin depender de Rancho Cachimba** (todas `[P2-Media]`, independientes entre sí, sin orden forzoso — ver §5 para el detalle de cada una): `#MED-04` (plantillas de email responsive), `#MED-05` (rate limit + IP confiable en login/checkout), `#SEC-03` (inventario de secretos), `#FLOW-01`/`#FLOW-02`/`#PAY-02` (flujo comercial repetible). El resto (`#RC-01`/`#RC-06b`/`#RC-18`) sigue en pausa por decisión del usuario, que necesita tiempo de diseño/investigación antes de retomarlo. También quedó postergado (a pedido del usuario) verificar `EXPLAIN ANALYZE` de `#MED-03` contra la base real — nota aparte: la base de producción es **Neon**, no Supabase como dice el resto de este documento; corrección pendiente, el usuario pidió posponer el tema completo hasta tener más contexto sobre Neon.

**No tocar sin que el usuario lo pida:** limpieza de lint global (135 errores preexistentes fuera de los archivos de este cierre — es `#AUD-10`/deuda técnica, no parte del gate), ni nada de Rancho Cachimba (`#RC-01`/`#RC-06b`/`#RC-18`) — depende de insumos del cliente, no de código.

---

## §1 · AUDITORÍA Y DIAGNÓSTICO (2026-08-20)

### 1.1 Los 3 bloqueadores críticos

| # | Hallazgo | Evidencia | Impacto |
|---|---|---|---|
| **B1** | **El endpoint de pago es inalcanzable.** En `apps/orders/urls.py` la ruta `<slug:plan_slug>/` está declarada antes que `process/`, `success/` y `error/` — Django resuelve `/checkout/process/` como `checkout_view(plan_slug='process')` → 404. | `apps/orders/urls.py:19-24` | El flujo de checkout con Mercado Pago **nunca puede completarse**. Explica por qué "el flujo nunca se probó de punta a punta" (`#PAY-03`). |
| **B2** | **Sin verificación de pertenencia usuario↔tenant.** `client_login` autentica a cualquier `User` en cualquier dominio, y ninguna vista de dashboard valida `request.user.profile.client == request.client` (cero referencias a `profile` en `apps/website/views.py`). Un owner del tenant A puede loguearse en el dominio del tenant B y **editar el contenido de B**. | `apps/website/auth_views.py:37-53`, `apps/website/views.py` | Fuga de datos y escalada cross-tenant. Es el riesgo #1 del modelo multi-tenant. |
| **B3** | **Webhook de MP sin validar firma.** La llamada a `validate_webhook_signature()` está **comentada** en la vista, y el método devuelve `True` si `MP_WEBHOOK_SECRET` está vacío. | `apps/orders/views.py:353-356`, `mercadopago_service.py:271-273` | Endpoint público falsificable. Mitigado parcialmente porque la vista re-consulta el pago contra la API de MP, pero permite replay/manipulación de estados. |

### 1.2 Otros hallazgos de la auditoría

**Seguridad / correctitud**
- `render.yaml` **malformado**: el cron `contact-digest` quedó insertado en medio del servicio web; `buildCommand`, `startCommand`, `healthCheckPath` y todos los `envVars` quedaron anidados bajo el cron, no bajo el web service. Si Render re-sincroniza el blueprint, el deploy queda sin build command ni variables (`render.yaml:23-36`).
- `Order._generate_order_number()` usa `count()+1` → **condición de carrera**: dos compras simultáneas generan el mismo `order_number` (campo `unique`) → `IntegrityError` y pago cobrado sin orden guardada (`apps/orders/models.py:455-462`).
- Emails transaccionales se envían **dentro de `@transaction.atomic`** (`process_onboarding`, webhook, checkout): SMTP bloquea el hilo HTTP dentro de la transacción y, si la transacción hace rollback, el correo ya salió.
- Producción cae **silenciosamente** a `console.EmailBackend` si falta `EMAIL_HOST_USER` (`production.py:153-154`) → correos "enviados" que no existen, sin error visible.
- `send_welcome` / `send_site_ready` hardcodean `https://{slug}.andesscale.cl` ignorando `BASE_DOMAIN` y dominios custom (`email_service.py:149,183`).
- El webhook devuelve **200 incluso ante excepción inesperada** (`views.py:436-439`) → MP no reintenta y la notificación se pierde.
- `onboarding_view` muta estado en **GET** (`order.start_onboarding()`, `views_onboarding.py:85-86`).
- `TenantAwareManager._current_client` es un **atributo de clase** (compartido entre hilos). Hoy solo lo usa `test_isolation`, pero es una trampa armada: si alguien lo setea en una vista, contamina requests concurrentes (`apps/tenants/managers.py`).
- `get_client_ip()` confía en `X-Forwarded-For` sin validar el proxy → el rate-limit se puede evadir spoofeando el header (`views.py:454-461`, `rate_limit.py:51-58`).
- `DEBUG_PRODUCTION=true` enciende DEBUG en producción — footgun documentado como "temporal" (`production.py:190`).
- Higiene de repo: `db_production_test.sqlite3` y el archivo `exit` están **trackeados en git**; `staticfiles/` sin ignorar; 3 CSV de auditoría en la raíz. `.env` está ignorado y **nunca entró al historial** (verificado con `git log --all -- .env`).

**Rendimiento / ORM**
- Tailwind se sirve por **CDN JIT en producción** (`cdn.tailwindcss.com` en 7 `base.html`, incl. temas activos) — sin build, sin purga, flash de estilos y dependencia externa.
- Los FKs tienen índice por defecto, pero faltan **índices compuestos** en los patrones reales de consulta: `Section(client, is_active, section_type)`, `Service(client, is_active, order)`, `GalleryItem(client, gallery_type, is_active, order)`.
- Consultas de `home` y dashboards son razonables (filtran por `client`); no se detectaron N+1 graves en las rutas calientes. `seo_tags` cachea 5 min (LocMemCache, por proceso — aceptable en single dyno).
- `conn_max_age=600` + Supabase: correcto; considerar pgbouncer si crece.

**Lo que está sólido** (heredado del Tablero B, re-verificado)
- Separación por dominio en `apps/` limpia; `orders/services/` aísla bien las integraciones.
- `TenantMiddleware` como allowlist dinámica de hosts + `production.py` con fuente única de dominios, HSTS, cookies host-only, SameSite — nivel serio.
- `check_tenant_setup` **ya existe** (la deriva doc↔código de `#DEUDA-05` se cerró parcialmente); 11 management commands en `tenants/`.
- Rate limiting propio (`apps/core/rate_limit.py`) aplicado al formulario de contacto, con honeypot.
- `.env` fuera del historial de git.

### 1.3 Estado de la suite de tests

`python manage.py test apps` → **8 tests, 7 OK, 1 skip** (0.04s), snapshot original de la auditoría. Cobertura real: middleware y modelo `Client`. **Cero tests** de orders/pagos/webhooks/onboarding/aislamiento (el aislamiento vive en un management command manual, no en la suite).

**Actualización (2026-08-20, tras cerrar `#AUD-01`–`#AUD-04`):** 35 tests, OK (1 skip). Se agregaron `apps/orders/tests/` (URLs de checkout, firma de webhook), `apps/website/tests/` (autorización cross-tenant en dashboard y login) y `apps/core/tests/test_render_config.py`. Aislamiento multi-tenant real (`#MED-02`) y cobertura de emails/onboarding (`#AUD-06`/`#AUD-07`) siguen pendientes — el arnés de §2 recién se está poblando, no está completo.

---

## §2 · ARNÉS DE SEGURIDAD (SAFETY HARNESS / TDD)

Marco para que el código futuro se acepte por verificación automática dura, no por revisión manual.

### 2.1 Reglas de testing (obligatorias para cerrar cualquier card)

1. **Toda card de Backend/Database entrega tests** que fallan sin el cambio (Rojo→Verde). Sin test, la card no se cierra.
2. **Aislamiento de DB:** los tests corren contra la DB efímera de Django (`manage.py test`), nunca contra `db.sqlite3` de dev ni Supabase. Prohibido `--keepdb` en CI.
3. **Cobertura mínima por módulo crítico** (medida con `coverage`): `apps/orders/` ≥ 80 %, `apps/tenants/middleware.py` y `managers.py` ≥ 90 %, resto de código nuevo ≥ 70 %. La cobertura global sube de forma monótona: nunca se mergea un cambio que la baje.
4. **Tests de aislamiento multi-tenant como suite**, no como comando manual: cada modelo con FK a `Client` tiene al menos un test "tenant A no ve/edita datos de tenant B".
5. **Regresión visual/funcional de tenants:** antes de deploy, smoke sobre los 3 tenants (`#TOOL-01`).

### 2.2 Métricas de calidad y herramientas

Agregar `requirements-dev.txt`:
```
ruff==0.6.*
bandit==1.7.*
coverage==7.*
```

| Verificación | Comando | Gate |
|---|---|---|
| Lint + formato | `ruff check apps/ config/` | 0 errores |
| Seguridad estática | `bandit -r apps/ -x apps/*/tests.py -ll` | 0 medium+ |
| Suite | `python manage.py test apps -v 1` | 0 fallos |
| Cobertura | `coverage run manage.py test apps && coverage report --fail-under=70` | ≥ umbral |
| Salud Django | `python manage.py check --deploy --settings=config.settings.production` | sin errores nuevos |
| Migraciones | `python manage.py makemigrations --check --dry-run` | sin migraciones pendientes |

(`mypy` queda **diferido**: el código no tiene anotaciones sistemáticas; adoptarlo hoy genera ruido, no seguridad. Revisitar en `#DEUDA-02`.)

### 2.3 Bucle autónomo de reparación (instrucciones para cada tarea futura)

```
1. SPEC    → escribir el test que expresa el comportamiento (falla: ROJO)
2. CODE    → implementar el mínimo que lo pone en VERDE
3. VERIFY  → ruff + bandit + suite completa + coverage (§2.2)
4. REPAIR  → si algo falla, arreglar y volver a 3 (máx. 3 iteraciones;
             a la 4ª, detenerse y reportar el bloqueo con diagnóstico)
5. CLOSE   → actualizar la card en este kanban en el mismo commit
```

Regla de commit: un commit por card (o por sub-entregable coherente), mensaje con el ID de card. Nada se commitea con la suite en rojo.

---

## §3 · HECHO (historial condensado)

Detalle completo en git history y en los tableros originales archivados.

- ✅ `#RC-02` Gate galería/Cloudinary — `AttributeError` de `GalleryItem` eliminado; `CLOUDINARY_PRESETS` deduplicado (cierra `#DEUDA-01`). Veredicto: hero split viable sin `#DEUDA-02`.
- ✅ `#RC-03` Tokens de marca — `accent_color` agregado (migración 0018), paleta oficial en `ClientSettings` + `:root` del theme, cero hex hardcodeados, Fraunces+Inter. *(parcial: favicon y logo_footer pendientes → absorbido en `#RC-11`)*
- ✅ `#RC-05` Tema `ranchocachimba` + rubro `turismo_rural` registrados; `provision_tenant` verificado con tenant descartable.
- ✅ `#RC-06` Hero split asimétrico construido (grid 1.32fr/10px/1fr, costura de tartán CSS, preset `hero_split` 3:4); bug de `upload_to_cloudinary(format='auto')` corregido. *(con fotos de prueba → pasada de diseño real en `#RC-06b`)*
- ✅ `#RC-07` Navbar/footer/contacto — leftovers de Servelec corregidos, botón WhatsApp arreglado (`wa.me` solo dígitos + mensaje precargado).
- ✅ `#DEUDA-01` Presets Cloudinary deduplicados *(test anti-regresión cerrado en `#AUD-10`)*.
- ✅ `#RC-04` (parcial) `LinkRevisar.md` con 8 entradas clasificadas; 3 abiertas (morphicons, *Babe*, afiche trials) → pospuestas.
- ✅ `check_tenant_setup` existe y funciona (cierra la mitad de `#DEUDA-05` / `#FLOW-02`).

---

## §4 · CORTO PLAZO — MVP / Lanzamiento Rancho Cachimba

> Ordenado por ruta crítica. Los `#AUD-0x` de seguridad van primero porque bloquean cualquier cobro real y comprometen el aislamiento — el argumento de venta central de la plataforma.

### 🔴 Gate de seguridad (antes de cualquier deploy con cobros)

#### ✅ `#AUD-01` — Reordenar rutas de checkout `[P0-Crítica]` `[S]` `[Backend]` — **DONE (2026-08-20)**
`/checkout/process/` era capturado por `<slug:plan_slug>/`. Patrón slug movido al final de `apps/orders/urls.py`.
**Resultado:** `apps/orders/tests/test_urls.py` (6 tests) prueba resolución de las 4 rutas + `reverse()`; reproducido en rojo antes del fix (`process`/`error` resolvían a `checkout_view`), verde después. Suite completa: 14 tests OK. `ruff check` limpio (fix de import-sort preexistente en el mismo archivo, sin relación con el bug).

#### ✅ `#AUD-02` — Firma de webhook obligatoria (absorbe `#SEC-01`) `[P0-Crítica]` `[M]` `[Backend]` — **DONE (2026-08-20)**
Validación descomentada en `mercadopago_webhook_view`; `validate_webhook_signature` falla cerrado cuando falta el secret y `not settings.DEBUG`.
**Resultado:** `apps/orders/tests/test_webhooks.py` (4 tests): sin firma → 401, firma inválida → 401, sin secret fuera de DEBUG → 401 (fail-closed), firma válida → 200 y la orden pasa a `paid`. En los 3 casos de rechazo se verifica además que `get_payment()` (mock) nunca se llama y que la orden no cambia de estado. Reproducido en rojo (3/4 fallaban con 200) antes del fix. Se agregó `requirements-dev.txt` (ruff/bandit/coverage) y `ruff.toml` (set conservador E/F/I — el codebase usa `except Exception` deliberadamente en varios puntos de resiliencia, no se adopta BLE/TRY hoy). Suite completa: 18 tests OK.

#### ✅ `#AUD-03` — Vínculo usuario↔tenant en login y dashboard `[P0-Crítica]` `[M]` `[Backend]` — **DONE (2026-08-20)**
`tenant_member_required` (nuevo, `apps/accounts/decorators.py`) reemplaza los 26 `@login_required(login_url='/auth/login/')` de `apps/website/views.py`; el login (`apps/website/auth_views.py::client_login`) valida `UserProfile.client == request.client` antes de loguear. Superusers exentos en ambos puntos; staff también exento en login (acceso Django admin, no ligado a tenant) pero sigue gateado por el decorador en el dashboard.
**Resultado:** `apps/website/tests/test_tenant_authorization.py` (9 tests, matriz {owner A, owner B, superuser, sin profile} × {dashboard, edit_section, delete_service}) + `test_login_tenant_authorization.py` (4 tests: login propio, login cross-tenant rechazado con mensaje genérico indistinguible de credenciales inválidas, password incorrecta, superuser). Reproducido en rojo antes del fix (owner A veía 200 en dashboard de B; login cross-tenant devolvía 302). Suite completa: 31 tests OK.

#### ✅ `#AUD-04` — Reparar `render.yaml` `[P0-Crítica]` `[S]` `[DevOps]` — **DONE (2026-08-20)**
`buildCommand`/`startCommand`/`healthCheckPath`/`envVars` devueltos al servicio web; cron `contact-digest` declarado como servicio propio y completo (runtime, buildCommand, envVars — incluye DB y SMTP porque el comando envía correo).
**Resultado:** `apps/core/tests/test_render_config.py` (4 tests, vía PyYAML — agregado a `requirements-dev.txt`) valida que el web service tenga build/start/healthcheck y las 11 env vars requeridas, y que el cron sea autocontenido. Reproducido en rojo contra el `render.yaml` original (`git stash`): 3/4 tests fallaban (web sin buildCommand, sin envVars, cron sin runtime propio). Suite completa: 35 tests OK.

### 🟠 Robustez del flujo transaccional

#### ✅ `#AUD-05` — `order_number` sin carrera `[P1-Alta]` `[S]` `[Backend]` `[Database]` — **DONE (2026-08-22)**
`count()+1` reemplazado por `ORD-{año}-{self.uuid.hex[:6].upper()}`. El `uuid` (PK) ya está asignado en memoria por el `default=uuid.uuid4` del campo antes del INSERT, así que la generación no depende de ninguna lectura compartida de la tabla — dos órdenes en paralelo nunca compiten por el mismo número.
**Resultado:** `apps/orders/tests/test_models.py` (3 tests): formato `ORD-YYYY-XXXXXX`, independencia bajo `count()` mockeado a un valor fijo compartido (reproduce la ventana de carrera — con la implementación vieja esto lanzaba `IntegrityError` en el segundo `save()`), no regeneración en re-save. Reproducido en rojo antes del fix (formato viejo `ORD-2026-0001` no matchea + `IntegrityError` en el test de carrera). Suite completa: 38 tests OK (1 skip). `ruff check` limpio en el archivo nuevo.

#### ✅ `#AUD-06` — Emails fuera de la transacción `[P1-Alta]` `[M]` `[Backend]` — **DONE (2026-08-22)**
Los 3 puntos de envío (`process_payment_view`, `mercadopago_webhook_view`, `process_onboarding`) encapsulados en una función local y diferidos con `transaction.on_commit()`. (El asincronismo real es `#MED-01`, ✅ cerrado 2026-08-22.)
**Hallazgo incidental corregido:** `process_onboarding` llamaba `UserProfile.objects.create(user=user, ...)`, pero `create_user()` ya dispara el signal `create_or_update_user_profile` (`apps/accounts/models.py:100-102`) que crea un `UserProfile` vacío vía `get_or_create` — el `.create()` explícito chocaba con el `OneToOneField` y lanzaba `IntegrityError` en **todo** onboarding real (bug no relacionado con AUD-06, pero bloqueaba el flujo completo; encontrado porque el test de commit exitoso no podía pasar sin él). Cambiado a `UserProfile.objects.update_or_create(user=user, defaults={...})`.
**Resultado:** `apps/orders/tests/test_emails.py` (4 tests): checkout y webhook verifican que el email queda en `on_commit` callbacks (outbox vacío hasta ejecutarlos); onboarding prueba rollback → outbox vacío (rojo confirmado: con el send directo, el correo salía igual antes del rollback forzado) y commit exitoso → 2 correos. Suite completa: 42 tests OK (1 skip). `ruff check` limpio en los archivos nuevos/tocados (errores preexistentes de import-sort en `views_onboarding.py` sin relación, `#AUD-10`).

#### ✅ `#AUD-07` — Correo de producción confiable `[P1-Alta]` `[S]` `[Backend]` `[DevOps]` — **DONE (2026-08-22)**
`config/settings/production.py` ya no cae a `console.EmailBackend` si falta `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`: falla al importar (`raise ValueError`, mismo patrón que `SECRET_KEY`). `EmailService._site_url()` (nuevo) prioriza `client.get_absolute_url()` (dominio primario real) y solo cae a `BASE_DOMAIN` si el tenant no tiene dominio activo; reemplaza el `f"https://{client.slug}.andesscale.cl"` hardcodeado en `send_welcome`/`send_site_ready`.
**Pendiente (no verificable desde el repo):** SPF/DKIM de Zoho — acción del usuario en el panel de Zoho/DNS.
**Resultado:** `apps/core/tests/test_production_settings.py` (2 tests, vía subprocess — el módulo de settings solo se evalúa una vez por proceso): sin credenciales → falla con `EMAIL_HOST_USER` en stderr (rojo confirmado con `git stash` contra el `production.py` original); con credenciales → arranca limpio. `apps/orders/tests/test_email_service.py` (8 tests): `_site_url` usa dominio primario o cae a `BASE_DOMAIN` (rojo confirmado: el método no existía), y smoke test de los 6 templates de `EmailService` con contexto real (`payment_success`, `welcome`, `site_ready`, `token_expiring`, `set_password`, `contact_received`). Suite completa: 52 tests OK (1 skip). `ruff check` limpio en archivos nuevos/tocados.

#### ✅ `#AUD-08` — Webhook con reintento honesto `[P2-Media]` `[S]` `[Backend]` — **DONE (2026-08-22)**
El `except Exception` genérico del webhook devolvía 200 ("para que MP no reintente") — en la práctica, una excepción inesperada hacía que la notificación se perdiera para siempre en vez de reintentarse. Ahora devuelve 500; los "ignorar" legítimos (tipo distinto de `payment`, sin `data.id`, orden no encontrada, ya finalizada) siguen devolviendo 200 explícito, sin cambios.
**Resultado:** `apps/orders/tests/test_webhooks.py` +2 tests: excepción inesperada (firma válida, `get_payment` lanza) → 500 (rojo confirmado: devolvía 200 antes del fix); idempotencia de orden ya finalizada → no-op sin `PaymentLog` duplicado (ya funcionaba, solo faltaba el test — verde sin cambios de código). Suite completa: 68 tests OK (1 skip).

#### ✅ `#AUD-09` — Onboarding sin mutación en GET `[P2-Media]` `[S]` `[Backend]` — **DONE (2026-08-22)**
`order.start_onboarding()` (paid→onboarding) se llamaba incondicionalmente en `onboarding_view`, sin mirar el método HTTP — un simple GET (link preview de un cliente de correo, prefetch del browser) mutaba el estado de la orden. Movido dentro del bloque `if request.method == 'POST':`.
**Resultado:** `apps/orders/tests/test_onboarding.py` (2 tests): GET no muta el estado (rojo confirmado: pasaba a `onboarding` antes del fix); POST sí transiciona (aunque el form sea inválido, refleja que el cliente empezó). Suite completa: 68 tests OK (1 skip).

#### ✅ `#PAY-03` — E2E sandbox de pago→provisioning `[P1-Alta]` `[M]` `[Backend]` — **DONE (parcial, 2026-08-22)**
Automatizado con `MercadoPagoService` mockeado (sin red, sin credenciales reales) — cubre el contrato completo checkout→onboarding→tenant en CI. **No reemplaza** la verificación manual contra la API real de MP en sandbox (tarjeta de prueba + browser), que sigue pendiente y requiere `MP_ACCESS_TOKEN`/`MP_PUBLIC_KEY` de test del usuario.
**2 bugs de producción encontrados y corregidos al construir el test** (nadie había corrido este flujo de punta a punta):
1. `views_onboarding.py` redirigía con `redirect('orders:onboarding_success', ...)`, pero `urls_onboarding.py` se incluye **sin namespace** en `config/urls.py` → `NoReverseMatch` en **todo** onboarding real, atrapado por el `except Exception` genérico → el cliente veía "Ocurrió un error al crear tu sitio" aunque el tenant ya se había creado exitosamente. Corregido a `redirect('onboarding_success', ...)` (y el mismo bug en el redirect de token inválido/expirado).
2. `Order.mark_as_completed()` limpiaba `onboarding_token` (`= None`) justo antes de que `onboarding_success_view` buscara la orden **por ese mismo token** → `Http404` incluso arreglado el bug #1. El token ya no se limpia al completar (el propio `onboarding_view` corta el flujo antes por `status == 'completed'`, así que dejarlo no reabre el formulario).
**Resultado:** `apps/orders/tests/test_pay03_e2e_sandbox.py` (2 tests): tarjeta aprobada → checkout→email→formulario→Client+Domain+UserProfile(owner)+Sections(hero,contact)+orden `completed`+2 emails, siguiendo el redirect real hasta la página de éxito (no un 404); tarjeta rechazada → orden `failed`, sin tenant. Reproducido en rojo antes de ambos fixes (`NoReverseMatch` primero, luego `redirect_chain` vacío). Suite completa: 54 tests OK (1 skip). `ruff check` limpio en archivos nuevos/tocados.

### 🟡 Lanzamiento Rancho Cachimba (código ya listo, faltan insumos + publicación)

#### `#RC-01` — Inventario del material del cliente `[P1-Alta]` `[S]` *(depende del usuario)*
Catalogar fotos/video entregados; pedir lo que falta (horarios, precios, coordenadas, datos del pastor). **DoD:** brief en `Documentacion/ClientesRanchoCachimba/brief.md`.

#### `#RC-06b` — Pasada de diseño real del hero `[P1-Alta]` `[S]` `[Frontend]` *(pospuesto 2026-08-18, retomar antes de publicar)*
Reemplazar `zar.jpeg`/`FotoGaleria.jpeg` por el material definitivo, decidir slot A/B, validar recorte 3:4 (`gravity:'auto'` puede fallar en fotos de acción). Decidir destino del video `Animaciondefondo.mp4`.

#### `#RC-20` — Maquetación del hero según mockup aprobado `[P1-Alta]` `[M]` `[Frontend]` *(spec lista 2026-08-24, ejecutar en esta branch — NO es del piloto agéntico)*
Análisis del mockup `Documentacion/Planificación/hero_cachimba.html` (`#RC-06b`) contra `docs/design-system.md` y el código real del tema → 6 tarjetas atómicas en `Documentacion/Planificación/spec_bolt_hero_cachimba.md` (renumeradas `RC-BOLT-*` para no chocar con los `BOLT-*` de `docs/kanban_agente.md` en `agent/ai-dlc-pilot`, que por su propia regla §0.4 no toca nada de Rancho Cachimba). Orden sugerido: **RC-BOLT-01** tokens CSS rotos — los 12 componentes del tema usan `var(--primary|secondary|accent)` que nadie define (114 ocurrencias; el `:root` define `--color-*`) — bug real, bloqueante → **RC-BOLT-04** clase `.tartan` en `base.html` + banda hero→stats → **RC-BOLT-03** navbar oscura + CTA "Reservar visita" → **RC-BOLT-02** barra de utilidad (nueva, datos desde `ClientSettings`) → **RC-BOLT-05** stats fondo claro con copy rancho (números reales dependen de `#RC-01`) → **RC-BOLT-06** CTAs del hero ("Reservar visita" / "Ver el pastoreo →"). Propuestas del mockup rechazadas por `design-system.md` §2b (hero con `layout: single|split`, `hero_overlay mode="block"`): documentadas en la spec, sin card. **Corte con el piloto agéntico (2026-08-24):** las 3 generalizaciones *de plataforma* que salieron del mismo análisis (guardia del contrato de tokens CSS, CTA del navbar compartido configurable por tenant, `hero_ctas` a `components/`) se extrajeron como `BOLT-06..08` en `docs/kanban_agente.md` (branch `agent/ai-dlc-pilot`, commit `6b7b844`) — ejecutables por el piloto sin violar su regla §0.4; acá quedan solo las `RC-BOLT-*` Rancho-específicas. La guardia de tokens (`BOLT-06`) atrapará automáticamente los 114 usos rotos de este tema cuando la branch se integre; `RC-BOLT-01` (el renombrado concreto) sigue siendo necesario acá. **DoD:** las 6 tarjetas cerradas con el gate de `CLAUDE.md` (ruff + suite + `makemigrations --check`) y verificación visual contra el mockup.

#### `#RC-08` — Publicar Etapa 1 `[P1-Alta]` `[M]` `[DevOps]` *(checklist en manos del usuario)*
PR → develop → main, verificar tenant en producción, Custom Domains en Render, DNS NIC Chile, `check_tenant_setup --settings=config.settings.production`, apagar `mode_under_construction` cuando el copy deje de ser placeholder. *(Checklist detallado de 8 pasos: ver Tablero A archivado, `#RC-08`.)*

#### `#RC-09` — Landing completa por componente `[P1-Alta]` `[L]` `[Frontend]`
Orden: experiencias → el pastor (`#RC-10`) → galería → cómo visitar → colegios. Regla: antes de escribir un componente, revisar si existe en `servelec`/`andesscale`/`themes/default`; si existe en 2+ lugares, generalizar a `templates/components/`. Contrato completo + precedente real en `docs/design-system.md` (`#AUD-11` Paso 2): `components/media_collection.html` con parámetro `mode="slideshow"|"grid"` + slots de override por ruta de template (`effects`/`overlay`/`theme_ctas`) — no "`hero` con variante `layout: single|split`" como decía antes esta card, cita que no existe en el código y quedó corregida al verificarla contra el código actual. Preferir clases Tailwind sobre `style=""` inline (guía del usuario; ver `#TOOL-04`). Consulta y actualiza `LinkRevisar.md` (`#RC-19`).

#### `#RC-10` — Sección del pastor `[P1-Alta]` `[M]` `[Frontend]`
Retrato, torneos, perros, video. **DoD:** funciona como pieza compartible por sí sola.

#### `#RC-11` — Contenido real y media en Cloudinary `[P1-Alta]` `[M]` `[Frontend]`
Subidas vía `apps/core/cloudinary_utils.py` a `tenants/rancho-cachimba/{branding,services,sections}`; favicon y `logo_footer` pendientes de `#RC-03`. **DoD:** cero placeholders.

#### `#RC-12` — Formulario de contacto + SMTP del tenant `[P1-Alta]` `[M]` `[Backend]` `[Frontend]`
`ClientEmailSettings` + `FormConfig` con tipo de visita (familia/colegio/grupo) y fecha tentativa. **DoD:** envío end-to-end en bandeja de entrada, no spam. *(depende de `#AUD-07`)*

#### `#RC-13` — SEO local + datos estructurados `[P1-Alta]` `[M]` `[Backend]`
`SEOConfig` + JSON-LD `TouristAttraction`×`LocalBusiness` con `openingHoursSpecification` y `geo`. Keywords: granja interactiva Maullín, pastoreo con perros ovejeros, visitas colegios Los Lagos. **DoD:** válido en Rich Results Test. Escapar `</` en el JSON-LD embebido de `seo_tags.py` al pasar por aquí.

#### ✅ `#AUD-11` — Pipeline de build de Tailwind `[P1-Alta]` `[M]` `[Frontend]` `[DevOps]` — **DONE, 4/4 pasos (2026-08-22)**
Consolida `#AUD-11` + `#TOOL-04` + `#DS-01`/`#DS-02` en un solo plan de 4 pasos (ver `C:\Users\sanch\.claude\plans\streamed-inventing-stroustrup.md`). **Paso 1 (pipeline de build) cerrado:** `tailwind.config.js` compartido en la raíz (Tailwind v3, `content: ['./templates/**/*.html']`, colores/fuentes referenciando `var(--color-*)`/`var(--font-*)`, no hex); `static/css/input.css` real (antes stub sin procesar desde diciembre); `build.sh` corre `npm ci && npm run build:css` antes de `collectstatic --clear`; los 9 `base.html` (7 temas + 2 páginas de error) migrados: CDN + `tailwind.config` inline afuera, un solo `<link>` a `output.css`, un solo bloque `:root` por página (antes duplicado JS+CSS), Alpine.js fijado a `3.16.2` (antes `@3.x.x` flotante en los 9). Config Tailwind muerta descartada (`dorado`/`claro`/`tierra`/`carbon` de ranchocachimba, `surface` de andesscale — confirmado por grep que ninguna se usaba como clase `bg-X`/`text-X`). `.btn-primary` de dashboard se mantuvo separado del compartido a propósito (diseño distinto) — verificado seguro por CSS Cascade Layers (estilos sin capa siempre ganan sobre `@layer components`). CSS compilado: ~68 KB / ~11.5 KB gzip (DoD: < 50 KB gzip). Verificado con la suite Django completa + `npx playwright test` (#TOOL-01) contra los 3 tenants reales — 6/6 en verde, cero purga silenciosa del glob de `content`. **Paso 2 (contrato de tema + librería de componentes) cerrado:** `docs/design-system.md` (nuevo) documenta el contrato de variables CSS obligatorio de `base.html` y la regla de componentes compartidos de `#RC-09`. Al verificar el ejemplo citado contra el código (paso explícitamente pedido por el plan) se encontró que la cita "`hero` con variante `layout: single|split`" (en `CLAUDE.md` y en esta misma card) **no existe en el código** — no hay ningún parámetro `layout` en ningún `hero.html`. El precedente real es `components/media_collection.html`: parámetro `mode="slideshow"|"grid"` + slots de override pasados como ruta de template (`effects`/`overlay`/`theme_ctas`), consumido por los `hero.html` wrapper de `servelec`/`andesscale`/`themes/default`; `ranchocachimba/components/hero.html` es la excepción documentada (estructura distinta, no una variante de estilo — no usa `media_collection.html` a propósito, ya comentado así en el propio archivo). Corregida la cita en `CLAUDE.md` y en la card de `#RC-09`. Sin verificación de gate (es documentación, según el plan) — solo la corrección de precisión de arriba. **Paso 3 (exposición acotada al tenant) cerrado:** `apps/tenants/fonts.py` (nuevo) define `FONT_CHOICES` (Inter/Outfit/Fraunces/Space Grotesk — las 4 que ya usan los temas reales como `--font-display`) y `google_fonts_query()`. `ClientSettings.font_family` pasa a `choices=FONT_CHOICES, default='Inter'` (antes `CharField` libre con default `'Inter, sans-serif'` — un stack CSS completo, no un nombre de fuente; interpolado en `--font-sans: '...'` generaba un valor de fuente inválido que el navegador nunca podía resolver, mismo patrón que `#BUG-01`: un campo que existe pero no hace nada). Migración `0020` (schema) + `0021` (data, normaliza cualquier `font_family` existente fuera de la lista curada — toma la parte antes de la primera coma, si no matchea cae a `Inter`). `BrandingForm` ahora expone `accent_color` (widget color) y `font_family` (`<select>`, validación real vía `choices` del modelo — un valor fuera de la lista curada rechaza el form). `templates/dashboard/branding.html`: color de acento agregado a la grilla de colores, selector de tipografía nuevo. El `<link>` de Google Fonts de cada tema (que antes cargaba Inter fijo sin importar `font_family`) ahora arma su fragmento `family=...` dinámico vía el tag `{% google_fonts_query %}` (`website_tags`) — `--font-sans` (cuerpo) sigue la elección del tenant, `--font-display` (títulos) queda fijo por tema, tal como quedó documentado en `docs/design-system.md`. `andesscale` queda explícitamente afuera (mismo precedente de Paso 1 para `secondary_color`/`accent_color`: marca propia, sin personalización). **Resultado:** `apps/tenants/tests_branding_form.py` (nuevo, 6 tests: campos expuestos, widget color, las 4 fuentes curadas válidas, fuente fuera de lista rechazada, guardado real) + `apps/website/tests/test_font_family_rendering.py` (nuevo, 2 tests: home renderizado carga Inter por default, cambiar `font_family` cambia el `<link>` real) — 92 tests en total, suite completa + `npx playwright test` (3 tenants reales) en verde. **Paso 4 (retirar deuda existente) cerrado:** `templates/partials/tenant_css.html` (0 bytes, no hacía nada) y el tag `{% tenant_custom_css %}` que lo incluía (`apps/tenants/templatetags/tenant_tags.py`) retirados por completo — no arreglados, per el plan (el sistema de tokens de Paso 1-3 es ahora el único camino para personalizar un tenant). Quitadas las dos llamadas al tag (`andesscale/base.html`, `themes/default/base.html`) y el `{% load tenant_tags %}` que quedó sin uso en `andesscale/base.html`. Grep confirma cero referencias restantes al tag/partial en todo el repo. Suite completa (92 tests) + `npx playwright test` (3 tenants reales, 6/6) en verde tras el retiro — sin cambios de comportamiento visible, era código muerto.

Con esto, `#AUD-11` + `#TOOL-04` + `#DS-01`/`#DS-02` quedan consolidados y cerrados en su totalidad (plan de 4 pasos completo).

#### ✅ `#BUG-01` — Comentarios Django `{# #}` multilínea rotos `[P1-Alta]` `[S]` `[Frontend]` — **DONE (2026-08-22)**
Hallazgo incidental verificando `#AUD-11` con screenshots reales (no solo el smoke DOM-check de Playwright): `servelec-e2e` y `ranchocachimba-e2e` mostraban texto de comentario crudo como contenido visible de la página, y el layout se rompía después. Causa raíz confirmada leyendo el código fuente de Django: `django.template.base.tag_re` (`{%.*?%}|{{.*?}}|{#.*?#}`) se compila **sin** `re.DOTALL` — cualquier `{# ... #}` que cruce un salto de línea nunca matchea como tag, Django lo deja como texto literal. El navegador, al toparse con texto no vacío dentro de `<head>`, cierra `<head>` y abre `<body>` antes de tiempo (algoritmo de parsing HTML5), arrastrando el resto de la página. Afectaba **17 archivos**, la mayoría preexistentes (no introducidos por `#AUD-11`): `templates/base.html`, `servelec/base.html`, `andesscale/base.html`, `dashboard/base.html`, `themes/default/base.html`, `themes/electricidad/base.html`, `errors/under_construction.html`, `ranchocachimba/base.html` (éstos con comentarios nuevos de `#AUD-11`) + `emails/contact_digest.html`, `landing/home.html`, `partials/contact_form.html`, `components/media_collection.html`, `ranchocachimba/components/hero.html`, `ranchocachimba/components/hero_overlay_theme.html`, `ranchocachimba/landing/home.html`, `servelec/components/hero_overlay_theme.html`, `servelec/landing/home.html` (preexistentes — bug ya vivo en producción antes de esta sesión). **Fix:** cada comentario multilínea partido en comentarios de una sola línea (`{# ... #}` por línea) — mismo contenido, cero comentarios cruzando saltos de línea. **Resultado:** `apps/core/tests/test_template_comments.py` (nuevo, TDD: rojo confirmado con los 21 casos exactos antes del fix, verde después) escanea `templates/**/*.html` con el mismo `tag_re` de Django y falla si aparece algún `{# #}` multilínea — regresión cubierta a futuro. Suite Django completa + `npx playwright test` reverificados en verde tras el fix.

#### ✅ `#AUD-12` — Endurecer settings de producción `[P2-Media]` `[S]` `[DevOps]` — **DONE (2026-08-22)**
Eliminado el override `DEBUG_PRODUCTION` — `DEBUG = False` fijo en `config/settings/production.py`, sin ninguna variable de entorno que pueda reactivarlo (encender DEBUG en prod expone traceback completo, env vars y rutas del sistema en cualquier error 500). La validación fail-fast de env vars requeridas ya existe para `SECRET_KEY` (previo) y `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` (`#AUD-07`) — incluida en la verificación de este cierre.
**Resultado:** `apps/core/tests/test_production_settings.py` +2 tests (vía subprocess): con `DEBUG_PRODUCTION=true` seteado, `settings.DEBUG` sigue siendo `False` (rojo confirmado: antes daba `True`); sin ningún override, también `False`. Suite completa: 68 tests OK (1 skip).

#### `#RC-18` — Acuerdo comercial y dominio `[P1-Alta]` *(usuario)*
Propuesta, cobro por transferencia (observaciones → `#PAY-02`), compra de `ranchocachimba.cl` en NIC Chile.

---

## §5 · MEDIANO PLAZO — Estabilidad, seguridad y performance

#### ✅ `#MED-01` — Correo asíncrono `[P1-Alta]` `[M]` `[Backend]` — **DONE (2026-08-22)**
Cola en DB: `EmailOutbox` (nuevo modelo en `apps/core/models.py`) + cron `send-pending-emails` cada 5 min (mismo mecanismo que `contact-digest`). `EmailService._send_email()` renderiza el template igual que antes (CPU local, no red) pero si `settings.EMAIL_ASYNC=True` inserta en `EmailOutbox` en vez de abrir la conexión SMTP — el INSERT es lo único que corre dentro del request. `EMAIL_ASYNC=False` por defecto (`base.py`), `True` por defecto en producción (override por env var si hace falta apagarlo). `send_set_password` fuerza `force_sync=True` siempre: quien resetea su contraseña está esperando en el momento, no tiene sentido que dependa del próximo cron.
**Resultado:** `apps/core/tests/test_email_outbox.py` (7 tests): encolado vs. envío directo según `EMAIL_ASYNC`, `set_password` siempre síncrono, comando `send_pending_emails` envía y marca `sent_at`, idempotente (no reenvía lo ya enviado), reintentos con `attempts`/`last_error`, `failed_at` al llegar a `max_attempts` (3). `apps/core/tests/test_production_settings.py` +2 tests: `EMAIL_ASYNC=True` por defecto en producción, desactivable por env var. `apps/core/tests/test_render_config.py` actualizado para 2 crons (ya no asume "exactamente 1"). Suite completa: 79 tests OK (1 skip). **Pendiente (usuario):** confirmar que el plan free de Render admite el schedule `*/5 * * * *` (sub-horario) antes de sincronizar el blueprint.

#### ✅ `#MED-02` — Suite de aislamiento multi-tenant `[P0-Crítica]` `[M]` `[Backend]` `[Database]` *(absorbe `#SEC-04`)* — **DONE (2026-08-22)**
`test_isolation` (management command manual) portado a `apps/tenants/tests_isolation.py`. **Hallazgo:** `TenantAwareManager._current_client` nunca se seteaba en código de request real (ni middleware ni vistas) — solo el comando manual lo hacía. En producción no filtraba nada: `Model.objects.all()` devolvía todos los tenants para `Section`/`Service`/`ContactSubmission`/`GalleryItem`. El aislamiento real siempre dependió (y sigue dependiendo) de que cada vista filtre explícitamente por `client=request.client`, y al auditar esas vistas (home pública, dashboard de galería, contactos) confirmé que sí lo hacen. **Decisión (con el usuario): eliminar el mecanismo** — no hacía nada y era un riesgo si alguien lo llegaba a usar (atributo de clase = contaminación entre requests concurrentes de distintos tenants). Se quitó de `TenantAwareManager` y se eliminó `TenantManager`/`TenantQuerySet` (alternativa "más robusta" que nunca se usó en ningún modelo). Se borró `apps/tenants/management/commands/test_isolation.py` (quedaba roto/engañoso tras el cambio — reportaba `FAIL` en el mecanismo que nunca fue real).
**Resultado:** `apps/tenants/tests_isolation.py` (8 tests) vía HTTP con `HTTP_HOST` por tenant: home pública nunca muestra servicios de otro tenant; IDOR en `GalleryItem` (edit/delete/toggle) y `ContactSubmission` (mark_read) — un owner correctamente logueado en su propio dominio no puede tocar objetos de otro tenant por ID; listados de dashboard (galería, contactos) nunca incluyen datos de otro tenant. Complementa la matriz de `apps/website/tests/test_tenant_authorization.py` (`#AUD-03`, gate a nivel de dominio) con el nivel de objeto que esa suite no cubría. Suite completa: 62 tests OK (1 skip). `ruff check` limpio. `makemigrations --check` limpio (sin cambios de schema).

#### ✅ `#MED-03` — Índices compuestos y revisión de consultas `[P1-Alta]` `[M]` `[Database]` *(absorbe `#DB-03`)* — **DONE (2026-08-22)**
Auditoría completa de todo modelo con FK a `Client` (no solo los 4 que mencionaba el audit original), comparando índices existentes contra patrones de consulta reales en código (no hipotéticos). **Resultado: la mayoría ya estaba bien indexado** de trabajo previo a esta sesión — `Section`, `ContactSubmission`, `GalleryItem` y `SEOConfig` ya tenían exactamente los compuestos que sus vistas necesitan. Solo 2 gaps reales:
1. `Service`: tenía `(client, is_active)` pero `home()` hace `.filter(client=X, is_active=True).order_by('order')` — sin `order` en el índice, Postgres filtra por índice pero igual ordena aparte. Reemplazado por `(client, is_active, order)` (el prefijo sigue sirviendo cualquier query que no use `order`).
2. `Domain`: `Client.primary_domain` hace `.filter(is_primary=True, is_active=True)` y `Domain.save()` hace `.filter(client=X, is_primary=True)` para desmarcar el primario anterior — ninguna cubierta por el índice existente `(client, is_active)`, que no incluye `is_primary`. Se agregó `(client, is_primary, is_active)` (nuevo, no reemplaza — hay también consultas reales que filtran solo por `is_active` sin `is_primary`, en 5+ lugares de `apps/marketing/`).
`UserProfile`, `Order` y los modelos `OneToOneField` (`ClientSettings`, `ClientEmailSettings`, `FormConfig`) no tienen gap: sus queries reales filtran solo por `client` (ya cubierto por el índice de FK por defecto) o el campo es `OneToOneField` (como máximo una fila por cliente, un índice compuesto no aporta nada).
**Resultado:** `apps/website/tests/test_model_indexes.py` (Service) + `apps/tenants/tests.py::DomainIndexTestCase` (Domain) verifican que los índices existen, citando la línea de código real que los necesita. Rojo confirmado antes de cada fix (`assertIn` sobre `Model._meta.indexes`). Suite completa: 81 tests OK (1 skip). `makemigrations --check` limpio. **Pendiente (usuario, no automatizable desde SQLite):** `EXPLAIN ANALYZE` contra datos reales de Supabase para confirmar index scan en producción.

#### `#MED-04` — Plantillas HTML transaccionales responsive `[P2-Media]` `[M]` `[Frontend]`
Rediseñar `templates/emails/*` (tablas, inline CSS, dark-mode friendly, texto plano decente). Probar en Gmail/Outlook móvil.

#### `#MED-05` — Rate limit y auditoría de IP confiable `[P2-Media]` `[S]` `[Backend]`
Tomar la IP del último proxy confiable (Render setea XFF); aplicar `RateLimiter` también a login (`scope='login'`) y checkout.

#### ✅ `#TOOL-01` — Playwright smoke multi-tenant `[P1-Alta]` `[M]` `[DevOps]` — **DONE (2026-08-22)**
Primera herramienta Node/npm del repo (`package.json`, `@playwright/test`, chromium instalado) — sienta base para `#AUD-11` también. `playwright.config.js` levanta un servidor Django dedicado (`config.settings.e2e`, DB SQLite descartable `db_e2e.sqlite3`, puerto 8811) que migra y siembra (`seed_e2e_tenants`, idempotente) antes de correr — `npx playwright test` hace todo en un solo comando, tal como pide el DoD.
**Decisión técnica:** el plan original (override del header `Host` vía Playwright para simular dominios sin DNS real) **no funciona** — Chromium moderno lo rechaza con `ERR_INVALID_ARGUMENT`. Se usa en cambio subdominios `*.localhost` (resuelven a `127.0.0.1` por RFC 6761, confirmado con `nslookup` en Windows sin tocar `/etc/hosts`) — cada tenant navega directo a su propia URL (`andesscale.localhost:8811`, etc.).
**Hallazgo real corregido antes de escribir el smoke (bloqueaba "formulario envía"):** `templates/partials/contact_form.html` (usado por `servelec`, `themes/default` y `themes/electricidad`) hacía un POST nativo sin `intent` ni `form_source` — dos `ChoiceField` requeridos por `ContactForm` sin `required=False`. Resultado: el formulario de contacto **siempre devolvía 400** en cualquier tenant con esa plantilla, `servelec` (producción real) incluido — nadie podía enviar un mensaje desde ahí. Corregido agregando los dos hidden inputs con sus valores por defecto (`general`/`page`, iguales a los que ya declara `ContactForm`). `andesscale` no tenía el bug (usa `components/contact_multistep.html`, que sí arma esos campos vía `fetch()`). `ranchocachimba` no tiene formulario todavía por diseño (`#RC-07`, WhatsApp directo) — el smoke prueba el link de WhatsApp en su lugar, no un formulario que no existe.
**Resultado:** `apps/website/tests/test_contact_submit.py` (2 tests, TDD del bug: rojo confirmado con `git stash` contra la plantilla original — 400 sin `ContactSubmission` creado). `tests/e2e/smoke.spec.js` (6 tests, 3 tenants × {home+hero+navbar+footer, mecanismo de contacto real de cada uno — difiere por tema, no es el mismo formulario}) — verde, `npx playwright test` completo en ~12s. Suite Django completa: 83 tests OK (1 skip).
**Tercera instancia del mismo bug, encontrada al correr la suite en `develop`:** `templates/landing/home.html` (fallback global del `TenantTemplateLoader`, idéntico en ambas branches) tiene su propio `<form>` standalone con el mismo problema — en `feature/RanchocachimbaEtapa1` es código muerto (shadowed por `templates/themes/default/landing/home.html`, que esa branch sí tiene), pero en `develop` (que todavía no tiene esa carpeta) es la plantilla que realmente se sirve para cualquier tenant con `template='themes/default'` — el valor por defecto del campo. Corregido en ambas branches igual. `tests/e2e/smoke.spec.js` en `develop` detecta con `fs.existsSync` si `templates/ranchocachimba/` existe y excluye ese tenant si no (en vez de dejarlo en rojo) — se reincluye solo cuando RC se mergee ahí.

#### ✅ `#TOOL-07` — `CLAUDE.md` en la raíz `[P1-Alta]` `[S]` `[DevOps]` — **DONE (2026-08-22)**
`CLAUDE.md` creado en la raíz: comandos frecuentes, resolución de tenant/templates (`TenantTemplateLoader`), `render_tenant_template`, `TenantAwareManager` sin auto-filtro (post `#MED-02`), `tenant_member_required`, `cloudinary_utils`, emails con `on_commit`, los 4 gotchas reales de esta sesión (orden de `apps/orders/urls.py` — `#AUD-01`; namespace de `redirect()` en onboarding — `#PAY-03`; signal de `UserProfile` — `#AUD-06`; fail-fast de `production.py` — `#AUD-07`/`#AUD-12`), el arnés de TDD de §2 como contrato, y la situación de branches (`develop` vs `feature/RanchocachimbaEtapa1` en pausa).
**"Mover `.claude/` desde `Documentacion/`":** verificado — son solo `settings.local.json` autogenerados (permisos de sesión), ya ignorados por `.gitignore` global del usuario y nunca trackeados en git (`Documentacion/.claude/`, `Documentacion/Planificación/.claude/`, `.claude/` en la raíz). No hay nada que mover a nivel de repo; no bloquea nada.

#### ✅ `#AUD-10` — Higiene de repo + test anti-regresión de presets `[P2-Media]` `[S]` `[DevOps]` *(absorbe `#DEUDA-04` y el pendiente de `#DEUDA-01`)* — **DONE (2026-08-22)**
`db_production_test.sqlite3` y el archivo `exit` (ambos trackeados por accidente, sin ninguna referencia en código/docs, verificado por grep) eliminados del repo y del disco — no eran fixtures, `exit` resultó ser un log de `git log --stat` guardado por error en un archivo con ese nombre. `staticfiles/` (134 archivos, generado por `collectstatic` en cada deploy) desindexado y agregado a `.gitignore` — confirmado con `collectstatic --dry-run` que se regenera igual sin estar trackeado. Los 3 CSV de auditoría en la raíz (`cloudinary_audit_*.csv`, de una corrida de marzo, sin referencias) se eliminaron en vez de "moverse" tal cual pedía la card original — moverlos a una carpeta que además se gitignora hacia adelante los habría dejado trackeados para siempre de forma inconsistente con el resto del cambio; en su lugar, `scripts/output/` se creó como carpeta de salida gitignorada (`.gitkeep` trackeado, contenido no) y `apps/core/management/commands/audit_cloudinary_assets.py` ahora escribe ahí por defecto (antes cada corrida sin `--output` explícito dejaba un CSV nuevo suelto en la raíz — se corrigió la causa, no solo el síntoma).
**Test anti-regresión de `CLOUDINARY_PRESETS`:** ruff ya detecta claves de dict duplicadas (regla `F601`, ya seleccionada en `ruff.toml` sin cambios), pero eso depende de que alguien corra `ruff check` sobre ese archivo puntual — no hay CI que lo automatice. `apps/core/tests/test_cloudinary_presets.py` (nuevo, TDD real: parsea el *código fuente* de `cloudinary_utils.py` con `ast` — un dict literal ya evaluado no conserva rastro de una clave duplicada, así que inspeccionar el objeto en runtime no sirve. Verificado reintroduciendo una clave duplicada real en `CLOUDINARY_PRESETS`: rojo confirmado, revertido, verde de nuevo) cubre `CLOUDINARY_PRESETS` y `VIDEO_PRESETS`, corre con `manage.py test` sin depender de que se acuerden de correr ruff.
**Resultado:** 103 tests en total, suite completa + `npx playwright test` en verde. `makemigrations --check` limpio. **No se tocó** la limpieza de lint global (135 errores preexistentes fuera de los archivos de este cierre) — la card, en su texto original, nunca la incluyó explícitamente en el DoD; queda disponible como pedido aparte si se quiere.
**Hallazgo incidental al cherry-pickear a `develop`:** `apps/core/cloudinary_utils.py` en `develop` sí tenía una clave duplicada real — `gallery_card`/`gallery_full` definidos dos veces (bloque "GALERÍA" y un bloque "HEROGALLERY" con valores distintos, el segundo pisaba al primero en silencio). `feature/RanchocachimbaEtapa1` ya había consolidado ambos bloques en una sola definición vía `#DEUDA-01`/`#RC-02`, pero ese fix nunca llegó a `develop` — el test nuevo lo agarró de inmediato al correr ahí. Aplicado en `develop` el mismo consolidado ya revisado del feature branch, no una fusión propia nueva.

#### ✅ `#DEUDA-05` — Reconciliar README y skill con el código `[P2-Media]` `[S]` `[DevOps]` — **DONE (2026-08-22)**
`Documentacion/README.md` estaba desactualizado en varios puntos estructurales, no solo `ClientSettings.template` → `Client.template` (que también se corrigió): describía `TenantAwareManager` con auto-filtro automático (falso desde `#MED-02`; la sección "Convenciones" del propio README decía literalmente lo contrario de la regla real — corregido), la resolución de `TenantTemplateLoader` sin el tier `default/` intermedio ni el caso especial `andesscale`, estructura de carpetas con `templates/themes/electricidad/` (no existe; los temas reales son `servelec`/`ranchocachimba`/`andesscale`/`themes/default`), roles inventados (`SuperAdmin`/`ClientAdmin` en vez de `owner`/`admin`/`editor`/`viewer` de `UserProfile.ROLE_CHOICES`), nombres de función y env vars de MercadoPago equivocados (`MERCADOPAGO_ACCESS_TOKEN` → `MP_ACCESS_TOKEN`, faltaba `MP_WEBHOOK_SECRET`), un comando `test_isolation` que ya no existe, y una sección 10 con numeración de cards (#1–#54) que dejó de usarse hace tiempo (reemplazada por un puntero a este kanban). El "skill" que la card asumía existente (`andesscale-saas`) en realidad **nunca se había creado** — se creó ahora en `.claude/skills/andesscale-saas/SKILL.md` (resolución de templates, filtrado por tenant, provisioning, brand tokens — con foco en las 3 áreas que ya tuvieron bugs reales: `#BUG-01`, `#MED-02`, `#AUD-11`).
**Hallazgos incidentales corregidos al reconciliar (ninguno era el alcance original de la card):**
- `apps/core/managers.py` era una copia muerta de `TenantAwareManager` con el patrón `_current_client` que `#MED-02` ya había eliminado de `apps/tenants/managers.py` — nunca se importaba desde ningún lado (confirmado por grep), pero era exactamente el mismo riesgo que `#MED-02` cerró en el archivo real: un atributo de clase compartido entre requests concurrentes, listo para resucitar por error si alguien importaba del archivo equivocado. Eliminado.
- `apps/accounts/views.py::login_view`/`logout_view` están registrados en `apps/accounts/urls.py` bajo `auth/`, pero `apps/website/auth_urls.py` monta el mismo prefijo `auth/` con sus propios `login/`/`logout/` **antes** en `config/urls.py` (línea 19 vs línea 40) — Django resuelve ahí primero, así que los de `accounts` son código muerto en la práctica (mismo patrón de "código que existe pero no se ejecuta" que `#BUG-01`/`font_family` en `#AUD-11`). No rompe nada hoy porque el login real (`apps/website/auth_views.py::client_login`) sí tiene el chequeo de `#AUD-03`, pero es confuso para quien lea `accounts/views.py` esperando que sea el login vigente. Documentado en README y en el skill; no se tocó el código (decisión de limpieza le corresponde al usuario, no bloqueaba el DoD de esta card).
**Verificación:** `python -c "import django; django.setup(); import apps.core.models, apps.tenants.managers"` confirma que el repo sigue importando sin `apps/core/managers.py`. **No se pudo correr la suite completa de Django en esta sesión** (el runner de comandos bloqueó `python manage.py test` vía el clasificador de auto-mode) — pendiente correrla manualmente antes de dar el hallazgo por cerrado del todo.

#### `#FLOW-01` / `#FLOW-02` / `#PAY-02` — Flujo comercial repetible `[P2-Media]` `[M]`
Procedimiento de ingreso de cliente + `check_tenant_setup` ampliado (SEOConfig completo, sin placeholders, `ClientEmailSettings`) + registro de fricciones del cobro manual de Cachimba (es la spec de `#FLOW-03`).

#### ✅ `#SEC-02` — Headers de seguridad `[P2-Media]` `[S]` `[DevOps]` — **DONE (2026-08-22)**
Ya había HSTS/nosniff/X-Frame/cookies seguras. Agregado: **CSP** (`django-csp==4.0`) y **Permissions-Policy** (`django-permissions-policy==4.33.0`), ambos solo en `config/settings/production.py` (mismo patrón que el resto del hardening — `development`/`e2e` sin tocar). Diccionarios reales en `config/settings/security_headers.py` (módulo aparte, sin `SECRET_KEY`/`EMAIL_*` de por medio, así se testea con un import normal en vez de subprocess): hosts auditados contra el código real, no una lista genérica — Google Fonts, Alpine.js (jsdelivr), htmx (unpkg), Google Analytics (opcional), imágenes de Cloudinary. `script-src`/`style-src` llevan `'unsafe-inline'` a propósito: los temas usan `<style>` inline con variables CSS por tenant (`#AUD-11`, no es deuda) y hay `onclick=` inline en 11 templates — un nonce no cubre atributos de evento, así que sacar `unsafe-inline` es una reescritura grande, fuera de alcance de esta card.
**Decisión de riesgo:** `/checkout/` queda **excluido de la CSP** (`EXCLUDE_URL_PREFIXES`) — el SDK de MercadoPago ahí usa Checkout Bricks (`mp.bricks()`, `apps/orders/templates/orders/checkout.html`), que crea iframes de Secure Fields cuyo dominio exacto no está documentado de forma confiable por MercadoPago; calibrar mal la CSP ahí puede romper el cobro en silencio, el mismo tipo de riesgo que ya mordió en `#AUD-01`. Habilitarla requiere una pasada manual contra el sandbox real de MP — mismo cabo suelto pendiente que `#AUD-07`/`#PAY-03` (credenciales de test). `Permissions-Policy` deshabilita features no usadas en ningún lado (camera, microphone, geolocation, usb, gyroscope, magnetometer, accelerometer, ambient-light-sensor, display-capture, encrypted-media); `payment`/`autoplay`/`fullscreen` quedan sin restringir a propósito, mismo motivo que checkout.
**Resultado:** `apps/core/tests/test_security_headers.py` (nuevo, 8 tests: forma del diccionario + **respuesta real** vía `override_settings` con el middleware activo — confirma que el header aparece de verdad en una response y que `/checkout/` efectivamente no lo lleva) + `apps/core/tests/test_production_settings.py` (+1 test: `CSPMiddleware`/`PermissionsPolicyMiddleware` presentes en `MIDDLEWARE` y después de `XFrameOptionsMiddleware`). 101 tests en total, suite completa en verde. `manage.py check --deploy --settings=config.settings.production` limpio (solo el warning esperado de `SECRET_KEY` de prueba). **Pendiente (usuario, no automatizable desde acá):** correr securityheaders.com contra los 3 dominios reales una vez deployado, y la pasada de sandbox de MP para eventualmente habilitar CSP en `/checkout/`.

#### `#SEC-03` — Inventario de secretos `[P2-Media]` `[S]` `[DevOps]`
`.env` verificado fuera del historial ✅. Falta: inventario de dónde vive cada secreto (Render env vars), y política de rotación.

---

## §6 · LARGO PLAZO — Escalabilidad y operaciones

- `#FLOW-03` — **Onboarding autoservicio completo** `[P1]` `[L]`: pago → onboarding → sitio sin intervención manual. Bloqueado por `#PAY-01`; la spec sale de `#PAY-02`.
- `#PAY-01` — **MercadoPago a producción** `[P1]` `[M]`: la parte técnica queda lista en corto plazo (`#AUD-01/02/05/08` + `#PAY-03`); resta el trámite SII de facturación.
- `#DB-02` — **Backups con restore probado** `[P1]` `[M]` `[Database]`: restore completo a branch de Supabase/Neon, documentado con tiempos. Un backup sin restore probado no es un backup.
- `#DEUDA-02` — **Pool único de imágenes** (`GalleryItem` sin `gallery_type` como rol fijo) `[P2]` `[XL]` `[Database]`: FK/M2M desde `Section`/`Service`, migración de datos. No empezar a medias.
- `#DEUDA-03` — **Unificar temas bajo `templates/themes/`** `[P2]` `[M]`: migración de datos de `Client.template`; ojo renames case-only en Windows.
- `#TOOL-04` + `#DS-01` + `#DS-02` — **Design system**: tokens Andes Horizon (`docs/design-system.md` + `tokens.css`), config Tailwind compartida, librería `templates/components/` (regla: token de marca en `ClientSettings` vs utilidad de diseño en Tailwind). Preferencia del usuario: utilidades Tailwind, no `style=""` inline.
- `#DS-03` — **Accesibilidad AA** `[P2]` `[M]`: argumento comercial con colegios/municipalidades.
- `#DB-01` — Branch de DB por feature (probar `#DEUDA-02` ahí) · `#DB-04` — pgvector (congelado hasta 3+ clientes pagando).
- `#TOOL-02/03/05/06/08` — StackHawk recurrente + Strix puntual post-MP · MCPs (Neon, Cloudinary) · skill `frontend-design` · skill `andesscale-saas` actualizada · kanban: markdown como fuente de verdad (decidido: este archivo).
- **Dashboard self-service del cliente** `[P2]` `[XL]`: administración independiente (evolución del dashboard actual). Cards #47–#54 del kanban viejo (marketing/GA4/Ads): **congeladas** explícitamente.
- `#RC-14`–`#RC-17` — Cierre Cachimba: QA multi-tenant + Lighthouse ≥85/≥90 · Search Console + sitemap · entrega y capacitación · post-lanzamiento GA4 y retrospectiva.

---

## §7 · DESGLOSE TÉCNICO (historias de corto y mediano plazo)

### `#AUD-01` — Reordenar rutas de checkout
- **Contexto:** el endpoint AJAX de pago devuelve 404; ningún pago puede procesarse.
- **Archivos:** `apps/orders/urls.py`.
- **Criterios de aceptación:**
  - [x] `POST /checkout/process/` llega a `process_payment_view`.
  - [x] `/checkout/error/` y `/checkout/success/<uuid>/` resuelven a sus vistas.
  - [x] `/checkout/<plan>/` sigue funcionando para un plan real.
  - [ ] Ningún plan puede llamarse `process`, `success` ni `error` — **no verificado**: no se agregó validación en `Plan.slug` ni test que documente el conflicto (un plan con ese slug quedaría inalcanzable vía `checkout_view`, silenciosamente). Pendiente si se quiere cerrar el DoD al 100%.
- **Verificación:** `python manage.py test apps.orders -v 2` con `tests/test_urls.py`: `resolve('/checkout/process/').func == process_payment_view` (Rojo antes del fix) + reverse de las 4 rutas. ✅ Ejecutado 2026-08-20, verde.

### `#AUD-02` — Firma de webhook obligatoria
- **Contexto:** endpoint público sin autenticación de origen; MP firma con HMAC-SHA256 (`x-signature: ts=..,v1=..`).
- **Archivos:** `apps/orders/views.py` (descomentar y devolver 401), `apps/orders/services/mercadopago_service.py` (fail-closed sin secret fuera de DEBUG).
- **Criterios de aceptación:**
  - [x] Webhook sin firma o con firma inválida → 401, sin tocar la orden.
  - [x] Firma válida (HMAC calculado con secret de test sobre `id:{data.id};request-id:{rid};ts:{ts};`) → 200 y procesamiento normal.
  - [x] En producción sin `MP_WEBHOOK_SECRET` la validación **rechaza** (no `return True`).
- **Verificación:** `python manage.py test apps.orders.tests.test_webhooks` — casos: firma válida, firma falsificada, sin header, sin secret con `DEBUG=False` (`override_settings`). ✅ Ejecutado 2026-08-20, verde (4/4).

### `#AUD-03` — Vínculo usuario↔tenant
- **Contexto:** dashboard autoriza solo con `@login_required`; falta la segunda mitad: membresía en el tenant del dominio.
- **Archivos:** nuevo `apps/accounts/decorators.py` (`tenant_member_required`), aplicar en `apps/website/views.py` (todas las vistas `dashboard_*`, `edit_*`, `create_*`, `delete_*`, `toggle_*`, `reorder_*`, `gallery_*`, `mark_contact_*`), `apps/website/auth_views.py` (login valida membresía).
- **Criterios de aceptación:**
  - [x] Usuario del tenant A autenticado en dominio de B → 403 en todo el dashboard de B.
  - [x] Login en dominio de B con credenciales de A: rechazado con mensaje genérico.
  - [x] Superuser conserva acceso.
  - [x] Usuario sin `UserProfile` → 403, no 500.
- **Verificación:** `python manage.py test apps.website.tests.test_tenant_authorization` — matriz {owner A, owner B, superuser, sin profile} × {dashboard, edit_section, delete_service}. ✅ Ejecutado 2026-08-20, verde (9/9 + 4/4 en `test_login_tenant_authorization`).

### `#AUD-04` — Reparar `render.yaml`
- **Contexto:** YAML válido pero semánticamente roto: el servicio web quedó sin build/start/envVars (todos anidados bajo el cron insertado en medio).
- **Archivos:** `render.yaml`.
- **Criterios de aceptación:**
  - [x] Servicio `saasmvp` (web) con `buildCommand`, `startCommand`, `healthCheckPath` y **todos** los `envVars` actuales.
  - [x] Cron `contact-digest` como servicio independiente completo (runtime, build, `DJANGO_SETTINGS_MODULE`, `DATABASE_URL`…).
  - [ ] Confirmar contra el dashboard de Render qué configuración está efectivamente activa antes de sincronizar el blueprint — **pendiente, requiere acceso al dashboard de Render (acción del usuario, no verificable desde el repo)**.
- **Verificación:** `python -c "import yaml,sys; d=yaml.safe_load(open('render.yaml')); ws=[s for s in d['services'] if s['type']=='web'][0]; assert 'buildCommand' in ws and 'envVars' in ws"` + revisión manual del diff. ✅ Formalizado como `apps/core/tests/test_render_config.py`, ejecutado 2026-08-20, verde (4/4). Rojo confirmado contra el YAML original vía `git stash`.

### ✅ `#AUD-05` — `order_number` sin carrera
- **Contexto:** `count()+1` bajo concurrencia duplica el número → `IntegrityError` post-cobro.
- **Archivos:** `apps/orders/models.py` (`_generate_order_number`).
- **Criterios de aceptación:**
  - [x] Formato legible se mantiene (`ORD-2026-XXXXXX`, hex derivado del uuid en vez de contador).
  - [x] Dos creaciones "simultáneas" (mock de `count()` a un valor fijo compartido) → números distintos, cero excepciones.
  - [x] Órdenes existentes no cambian (sin migración de datos — el cambio es solo en la generación de números nuevos).
- **Verificación:** `python manage.py test apps.orders.tests.test_models` (3 tests). ✅ Ejecutado 2026-08-22, verde. Suite completa: 38 tests OK (1 skip).

### ✅ `#AUD-06` — Emails fuera de la transacción
- **Contexto:** envío dentro de `atomic` = bloqueo + emails de transacciones que hicieron rollback.
- **Archivos:** `apps/orders/views_onboarding.py`, `apps/orders/views.py`.
- **Criterios de aceptación:**
  - [x] Todo `send_*_email` en flujos con `atomic` va dentro de `transaction.on_commit(...)` (función local, no lambda, para capturar `order`/`client`/`user` por valor vía default args y loguear éxito/error igual que antes).
  - [x] Si el onboarding hace rollback, no se envía nada.
  - [x] Si el email falla, la transacción ya commiteada no se ve afectada (log ERROR, no excepción al usuario — `EmailService._send_email` ya atrapa la excepción internamente).
- **Verificación:** `python manage.py test apps.orders.tests.test_emails` (4 tests) — con `django.core.mail.outbox`: rollback simulado → `len(outbox)==0` (rojo confirmado con send directo); commit → los 2 correos esperados; `TestCase.captureOnCommitCallbacks`. ✅ Ejecutado 2026-08-22, verde. Suite completa: 42 tests OK (1 skip).

### ✅ `#AUD-07` — Correo de producción confiable
- **Contexto:** fallback silencioso a console + URLs hardcodeadas `.andesscale.cl` rompen los correos de tenants con dominio propio.
- **Archivos:** `config/settings/production.py`, `apps/orders/services/email_service.py`.
- **Criterios de aceptación:**
  - [x] En producción, sin credenciales SMTP: error explícito al arrancar (`raise ValueError` en el import del módulo, nunca console silencioso).
  - [x] `send_welcome`/`send_site_ready` construyen `site_url` desde `client.get_absolute_url()`/`Domain` primario (nuevo `EmailService._site_url()`).
  - [x] Los 6 templates de email renderizan con contexto completo (smoke test) — el audit original decía "5", el servicio expone 6 (`payment_success`, `welcome`, `site_ready`, `token_expiring`, `set_password`, `contact_received`).
- **Verificación:** `python manage.py test apps.orders.tests.test_email_service apps.core.tests.test_production_settings` (10 tests). ✅ Ejecutado 2026-08-22, verde. Suite completa: 52 tests OK (1 skip). **Pendiente (usuario):** envío real de prueba a una casilla propia tras el deploy + verificar SPF/DKIM de Zoho.

### ✅ `#AUD-08` / `#AUD-09` — Webhook honesto + onboarding sin mutar en GET
- **Archivos:** `apps/orders/views.py`, `apps/orders/views_onboarding.py`.
- **Criterios:**
  - [x] Excepción inesperada en webhook → 500 (MP reintenta).
  - [x] `payment_id` ya procesado (orden en estado final) → 200 no-op idempotente, sin `PaymentLog` duplicado.
  - [x] GET de onboarding no cambia `order.status`; POST sigue transicionando `paid`→`onboarding`.
- **Verificación:** `python manage.py test apps.orders.tests.test_webhooks apps.orders.tests.test_onboarding` (8 tests). ✅ Ejecutado 2026-08-22, verde. Suite completa: 68 tests OK (1 skip).

### ✅ `#AUD-12` — Endurecer settings de producción
- **Archivos:** `config/settings/production.py`.
- **Criterios:** `DEBUG` fijo en `False`, sin override por `DEBUG_PRODUCTION` ni ninguna otra env var.
- **Verificación:** `python manage.py test apps.core.tests.test_production_settings` (4 tests). ✅ Ejecutado 2026-08-22, verde.

### ✅ `#PAY-03` — E2E sandbox (parcial: automatizado con mocks, falta la pasada manual real)
- **Contexto:** validar la cadena completa checkout→webhook→onboarding→tenant con MP en modo test.
- **Archivos:** `apps/orders/tests/test_pay03_e2e_sandbox.py` (nuevo); fixes en `apps/orders/views_onboarding.py` y `apps/orders/models.py` (ver hallazgos abajo).
- **Criterios:**
  - [x] Pago con tarjeta de prueba aprobado (mockeado) → orden `paid` + email con token → formulario de onboarding crea Client+Domain+User+secciones → orden `completed`.
  - [x] Tarjeta rechazada (mockeada) → orden `failed`, sin tenant.
  - [ ] Pasada manual real contra el sandbox de MP (tarjeta de prueba + browser) — requiere `MP_ACCESS_TOKEN`/`MP_PUBLIC_KEY` de test del usuario, no automatizable desde el repo.
- **Hallazgos corregidos (bugs de producción, no del test):**
  1. `redirect('orders:onboarding_success', ...)` → `NoReverseMatch` porque `urls_onboarding.py` no tiene namespace `orders:`. Atrapado por el `except Exception` genérico → el cliente veía un error falso aunque el tenant sí se creaba. Corregido a `redirect('onboarding_success', ...)` (y el mismo patrón en el redirect de token inválido).
  2. `Order.mark_as_completed()` limpiaba `onboarding_token`, y `onboarding_success_view` busca la orden por ese token inmediatamente después → `Http404` incluso con el bug 1 arreglado. Ya no se limpia el token al completar.
- **Verificación:** `python manage.py test apps.orders.tests.test_pay03_e2e_sandbox` (2 tests). ✅ Ejecutado 2026-08-22, verde (rojo confirmado antes de cada fix). Suite completa: 54 tests OK (1 skip). Pendiente: pasada manual guiada en sandbox real de MP.

### `#RC-12` — Formulario de contacto Cachimba + SMTP
- **Contexto:** el lead de Cachimba vale más con tipo de visita y fecha tentativa; hoy contacto = WhatsApp.
- **Archivos:** `apps/website/forms.py` (campos condicionales por `FormConfig`), `templates/ranchocachimba/components/contact.html`, `apps/tenants/models.py` (`ClientEmailSettings` ya existe — configurar), `apps/website/views.py::contact_submit`.
- **Criterios:**
  - [ ] Form con tipo de visita (familia/colegio/grupo) y fecha tentativa; validación server-side.
  - [ ] `ContactSubmission` guarda los campos nuevos; rate limit y honeypot intactos.
  - [ ] Notificación llega a la casilla real del cliente (no spam — SPF/DKIM verificados).
- **Verificación:** `python manage.py test apps.website.tests.test_contact` (POST válido, honeypot, rate limit 429, campos nuevos persistidos) + envío real E2E.

### `#RC-13` — SEO local + JSON-LD
- **Archivos:** `apps/marketing/models.py` (`SEOConfig.get_schema_json`), `apps/tenants/templatetags/seo_tags.py` (escape de `</` en JSON-LD), datos del tenant.
- **Criterios:** JSON-LD `TouristAttraction`+`LocalBusiness` con `geo` y `openingHoursSpecification` válido en Rich Results Test; OG image 1200×630 desde Cloudinary; sitemap incluye el dominio del tenant.
- **Verificación:** `python manage.py test apps.marketing apps.tenants.tests.test_seo_tags` (render del tag con config completa/sin config; escape correcto) + Rich Results Test manual.

### `#AUD-11` — Pipeline Tailwind
- **Archivos:** `package.json` + `tailwind.config.js` (nuevos, config base + extensión por tema), `static/css/`, los 7 `base.html`, `build.sh`, `render.yaml` (node en build).
- **Criterios:** cero referencias a `cdn.tailwindcss.com`; CSS compilado y purgado por tema (< 50 KB gzip); tokens de marca siguen viniendo de `ClientSettings` como custom properties; los 3 tenants renderizan idéntico (screenshot diff con `#TOOL-01`).
- **Verificación:** `grep -r "cdn.tailwindcss" templates/ → 0` como test de CI + smoke Playwright.

### ✅ `#MED-01` — Correo asíncrono (outbox + cron)
- **Archivos:** `apps/core/models.py` (`EmailOutbox`), `apps/core/management/commands/send_pending_emails.py`, `apps/orders/services/email_service.py` (`_send_email` encola cuando `EMAIL_ASYNC=True` y no es `force_sync`), `config/settings/base.py`/`production.py` (`EMAIL_ASYNC`), `render.yaml` (cron `send-pending-emails` cada 5 min).
- **Criterios:**
  - [x] Encolar es un solo INSERT (el render del template ya corría antes, es CPU local — lo único que se difiere es el `.send()` SMTP).
  - [x] El cron envía con reintentos (máx. 3, backoff = el propio intervalo del cron) y marca `sent_at`/`failed_at`.
  - [x] Un fallo de SMTP no afecta la request HTTP (ocurre en el proceso del cron, no del web).
  - [x] Correos "urgentes" (`set_password`) fuerzan envío síncrono vía `force_sync=True`, ignorando `EMAIL_ASYNC`.
- **Verificación:** `python manage.py test apps.core.tests.test_email_outbox apps.core.tests.test_production_settings apps.core.tests.test_render_config` (15 tests). ✅ Ejecutado 2026-08-22, verde. Suite completa: 79 tests OK (1 skip).

### ✅ `#MED-02` — Suite de aislamiento multi-tenant
- **Archivos:** `apps/tenants/tests_isolation.py` (nuevo), `apps/tenants/managers.py` (`_current_client` eliminado), `apps/tenants/management/commands/test_isolation.py` (borrado, superseded).
- **Criterios:**
  - [x] `Section`/`Service`: usuario/dominio de A no lee datos de B en la home pública (vía HTTP con `HTTP_HOST`).
  - [x] `GalleryItem`/`ContactSubmission`: owner de B no lee ni escribe (IDOR) objetos de A por ID, aunque esté correctamente logueado en su propio dominio.
  - [x] `SEOConfig`/`ClientSettings`: ya no tienen vector de IDOR (sin ID en URL, siempre `get_or_create`/lookup por `client=request.client`) — no requieren test de objeto, solo se documentó el análisis.
  - [x] `_current_client`: decidido con el usuario — **eliminado** (código muerto en producción, riesgo de atributo de clase compartido si se llegaba a usar). `TenantManager`/`TenantQuerySet` (alternativa nunca usada) también eliminados.
- **Verificación:** `python manage.py test apps.tenants.tests_isolation` (8 tests). ✅ Ejecutado 2026-08-22, verde. Suite completa: 62 tests OK (1 skip) — corre en cada push (gate de §2).

### ✅ `#MED-03` — Índices compuestos
- **Archivos:** `apps/website/models.py` (`Service`), `apps/tenants/models.py` (`Domain`) + migraciones. `apps/marketing/models.py` (`SEOConfig`) auditado, ya estaba correcto — sin cambios.
- **Criterios:**
  - [x] `Meta.indexes` revisado contra patrones de consulta reales (no los de §1.2 a ciegas — varios ya no aplicaban porque el índice necesario ya existía de trabajo previo).
  - [x] `Service(client, is_active, order)`, `Domain(client, is_primary, is_active)` agregados; `Section`, `ContactSubmission`, `GalleryItem`, `SEOConfig` confirmados ya correctos.
  - [x] `makemigrations --check` limpio después.
  - [ ] `EXPLAIN ANALYZE` en Supabase — pendiente, requiere datos reales de producción, no automatizable desde SQLite.
- **Verificación:** `python manage.py test apps.website.tests.test_model_indexes apps.tenants.tests.DomainIndexTestCase` + `python manage.py makemigrations --check --dry-run`. ✅ Ejecutado 2026-08-22, verde.

### `#MED-04` / `#MED-05` — ver §5; sus DoD son autocontenidos. `#TOOL-01`/`#TOOL-07` ✅ cerrados, detalle en §4.

---

## §8 · RUTA CRÍTICA

```
GATE SEGURIDAD ✅ CERRADO (2026-08-20)   LANZAMIENTO CACHIMBA
AUD-01 ✅ → AUD-02 ✅ → AUD-03 ✅ → AUD-04 ✅   RC-01 → RC-06b ─┐
   │                                        RC-18 ──────────┼→ RC-08 (publicar Etapa 1)
   ▼                                                        │
ROBUSTEZ TRANSACCIONAL ✅ CERRADA (2026-08-22)               ▼
AUD-05 ✅ → AUD-06 ✅ → AUD-07 ✅ → PAY-03 ✅(parcial)   RC-09 → RC-10 → RC-11 → RC-12 → RC-13
   │
   ▼
MED-02 (aislamiento) ✅ CERRADO (2026-08-22)         MEDIANO: MED-01 ✅ ∥ MED-03 ✅ ∥ TOOL-01 ✅ (2026-08-22) ∥ AUD-11 (Tailwind) pendiente
   │                                                                  ▼
   ▼ ESTAMOS AQUÍ                                    RC-14 → RC-15 → RC-16 → RC-17 (cierre)
Sin bloqueadores de código en el corto plazo —
queda RC-* (insumos del cliente) o mediano plazo (§5)
```

**Riesgo 1 — publicar con los P0 abiertos.** ✅ **Cerrado (2026-08-22).** `#AUD-03` (cross-tenant en dashboard/login) y `#MED-02` (aislamiento del resto del ORM, ahora en suite automática — `apps/tenants/tests_isolation.py`) ambos cerrados.
**Riesgo 2 — el material del cliente.** `#RC-01`/`#RC-06b` dependen del usuario, no de código; son lo único que bloquea `#RC-08` una vez pasado el gate.
**Riesgo 3 — tocar Render sin reparar `render.yaml`.** ✅ **Cerrado (2026-08-20).** Falta solo confirmar contra el dashboard real de Render qué configuración quedó efectivamente activa (acción del usuario).
**Riesgo 4 — onboarding real roto en producción sin que nadie lo notara.** ✅ **Cerrado (2026-08-22).** El E2E de `#PAY-03` encontró 2 bugs que rompían el redirect post-onboarding (`NoReverseMatch` + token limpiado antes de tiempo) — ver hallazgos incidentales arriba. Nadie había corrido el flujo completo de punta a punta hasta ahora.

---

## Batería de validación inmediata (estado al 2026-08-22, post robustez transaccional + aislamiento)

```bash
python manage.py test apps                              # 62 tests · OK (1 skip) ✅
python manage.py makemigrations --check --dry-run       # sin pendientes ✅
python manage.py check --deploy --settings=config.settings.production
python manage.py check_tenant_setup ranchocachimba      # [OK] tema/dominio ✅ (sesión RC)
python manage.py test apps.tenants.tests_isolation      # 8 tests, aislamiento real vía HTTP ✅ (#MED-02, reemplaza el comando manual `test_isolation`, eliminado)
python -m ruff check apps/ config/                      # ~135 preexistentes fuera de lo tocado — #AUD-10
python -m ruff check <archivos tocados en esta sesión>  # limpio ✅
```

Dependencias de desarrollo nuevas (`requirements-dev.txt`): `ruff`, `bandit`, `coverage`, `pyyaml`. Instalar con `pip install -r requirements-dev.txt` antes de retomar.
