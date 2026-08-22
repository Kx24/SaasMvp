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

## 🌙 Retomar aquí (actualizado 2026-08-22)

**El gate de seguridad de §4 está cerrado y commiteado.** `#AUD-01`, `#AUD-02`, `#AUD-03` y `#AUD-04` — los 4 bloqueadores P0 de la auditoría (checkout inalcanzable, webhook sin firma, fuga cross-tenant en login/dashboard, `render.yaml` roto) — están **DONE**, cada uno con TDD estricto (Rojo→Verde, ver detalle en §4 y §7) y verificados de punta a punta con `git stash` contra el estado original cuando aplicaba (`#AUD-04`). Commit `b5539f9` en `feature/RanchocachimbaEtapa1`. Archivos nuevos: `apps/orders/tests/`, `apps/website/tests/`, `apps/core/tests/`, `apps/accounts/decorators.py`, `ruff.toml`, `requirements-dev.txt`.

**`#AUD-05` (carrera en `order_number`) también DONE (2026-08-22)**, mismo TDD estricto — ver §4/§7. Suite: **38 tests, OK (1 skip)**. Pendiente de commit propio (no incluido en `b5539f9`).

**2 cabos sueltos menores del cierre del gate, no bloqueantes:**
1. `#AUD-01` — falta el caso "un plan no puede llamarse `process`/`success`/`error`" (sin validación ni test).
2. `#AUD-04` — falta confirmar contra el dashboard real de Render qué configuración está efectivamente activa (acción del usuario, no verificable desde el repo).

**Siguiente en la ruta crítica — 🟠 Robustez del flujo transaccional (§4):** `#AUD-06` (emails fuera de la transacción) → `#AUD-07` (correo de producción confiable) → `#PAY-03` (E2E sandbox de pago, ahora desbloqueado por el gate cerrado). En paralelo, `#MED-02` (suite de aislamiento multi-tenant real, hoy sigue siendo un management command manual) es la otra card `[P0-Crítica]` pendiente — vale la pena antes de tocar más código de dashboard.

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
- ✅ `#DEUDA-01` Presets Cloudinary deduplicados *(pendiente el test anti-regresión → `#AUD-10`)*.
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
Los 3 puntos de envío (`process_payment_view`, `mercadopago_webhook_view`, `process_onboarding`) encapsulados en una función local y diferidos con `transaction.on_commit()`. (El asincronismo real es `#MED-01`, mediano plazo.)
**Hallazgo incidental corregido:** `process_onboarding` llamaba `UserProfile.objects.create(user=user, ...)`, pero `create_user()` ya dispara el signal `create_or_update_user_profile` (`apps/accounts/models.py:100-102`) que crea un `UserProfile` vacío vía `get_or_create` — el `.create()` explícito chocaba con el `OneToOneField` y lanzaba `IntegrityError` en **todo** onboarding real (bug no relacionado con AUD-06, pero bloqueaba el flujo completo; encontrado porque el test de commit exitoso no podía pasar sin él). Cambiado a `UserProfile.objects.update_or_create(user=user, defaults={...})`.
**Resultado:** `apps/orders/tests/test_emails.py` (4 tests): checkout y webhook verifican que el email queda en `on_commit` callbacks (outbox vacío hasta ejecutarlos); onboarding prueba rollback → outbox vacío (rojo confirmado: con el send directo, el correo salía igual antes del rollback forzado) y commit exitoso → 2 correos. Suite completa: 42 tests OK (1 skip). `ruff check` limpio en los archivos nuevos/tocados (errores preexistentes de import-sort en `views_onboarding.py` sin relación, `#AUD-10`).

#### `#AUD-07` — Correo de producción confiable `[P1-Alta]` `[S]` `[Backend]` `[DevOps]`
Sin fallback silencioso a console en producción (fallar al arrancar o loggear CRITICAL); URLs de sitio en emails construidas desde `Domain`/`BASE_DOMAIN`, no hardcodeadas `.andesscale.cl`. Verificar SPF/DKIM de Zoho.

#### `#AUD-08` — Webhook con reintento honesto `[P2-Media]` `[S]` `[Backend]`
Devolver 500 en excepción inesperada para que MP reintente; conservar 200 para casos "ignorar" legítimos. Registrar idempotencia: un `payment_id` ya procesado en estado final → no-op (ya cubierto parcialmente, dejar test).

#### `#AUD-09` — Onboarding sin mutación en GET `[P2-Media]` `[S]` `[Backend]`
`start_onboarding()` solo en POST válido.

#### `#PAY-03` — E2E sandbox de pago→provisioning `[P1-Alta]` `[M]` `[Backend]`
Con `#AUD-01/02` cerrados: pasar un tenant ficticio por checkout completo en modo test, sin tocar el shell. **DoD:** tenant creado automáticamente por un pago de prueba.

### 🟡 Lanzamiento Rancho Cachimba (código ya listo, faltan insumos + publicación)

#### `#RC-01` — Inventario del material del cliente `[P1-Alta]` `[S]` *(depende del usuario)*
Catalogar fotos/video entregados; pedir lo que falta (horarios, precios, coordenadas, datos del pastor). **DoD:** brief en `Documentacion/ClientesRanchoCachimba/brief.md`.

#### `#RC-06b` — Pasada de diseño real del hero `[P1-Alta]` `[S]` `[Frontend]` *(pospuesto 2026-08-18, retomar antes de publicar)*
Reemplazar `zar.jpeg`/`FotoGaleria.jpeg` por el material definitivo, decidir slot A/B, validar recorte 3:4 (`gravity:'auto'` puede fallar en fotos de acción). Decidir destino del video `Animaciondefondo.mp4`.

#### `#RC-08` — Publicar Etapa 1 `[P1-Alta]` `[M]` `[DevOps]` *(checklist en manos del usuario)*
PR → develop → main, verificar tenant en producción, Custom Domains en Render, DNS NIC Chile, `check_tenant_setup --settings=config.settings.production`, apagar `mode_under_construction` cuando el copy deje de ser placeholder. *(Checklist detallado de 8 pasos: ver Tablero A archivado, `#RC-08`.)*

#### `#RC-09` — Landing completa por componente `[P1-Alta]` `[L]` `[Frontend]`
Orden: experiencias → el pastor (`#RC-10`) → galería → cómo visitar → colegios. Regla: antes de escribir un componente, revisar si existe en `servelec`/`andesscale`/`themes/default`; si existe en 2+ lugares, generalizar a `templates/components/` (precedente: `hero` con variante `layout: single|split`). Preferir clases Tailwind sobre `style=""` inline (guía del usuario; ver `#TOOL-04`). Consulta y actualiza `LinkRevisar.md` (`#RC-19`).

#### `#RC-10` — Sección del pastor `[P1-Alta]` `[M]` `[Frontend]`
Retrato, torneos, perros, video. **DoD:** funciona como pieza compartible por sí sola.

#### `#RC-11` — Contenido real y media en Cloudinary `[P1-Alta]` `[M]` `[Frontend]`
Subidas vía `apps/core/cloudinary_utils.py` a `tenants/rancho-cachimba/{branding,services,sections}`; favicon y `logo_footer` pendientes de `#RC-03`. **DoD:** cero placeholders.

#### `#RC-12` — Formulario de contacto + SMTP del tenant `[P1-Alta]` `[M]` `[Backend]` `[Frontend]`
`ClientEmailSettings` + `FormConfig` con tipo de visita (familia/colegio/grupo) y fecha tentativa. **DoD:** envío end-to-end en bandeja de entrada, no spam. *(depende de `#AUD-07`)*

#### `#RC-13` — SEO local + datos estructurados `[P1-Alta]` `[M]` `[Backend]`
`SEOConfig` + JSON-LD `TouristAttraction`×`LocalBusiness` con `openingHoursSpecification` y `geo`. Keywords: granja interactiva Maullín, pastoreo con perros ovejeros, visitas colegios Los Lagos. **DoD:** válido en Rich Results Test. Escapar `</` en el JSON-LD embebido de `seo_tags.py` al pasar por aquí.

#### `#AUD-11` — Pipeline de build de Tailwind `[P1-Alta]` `[M]` `[Frontend]` `[DevOps]`
Sacar `cdn.tailwindcss.com` de los 7 `base.html`; build con CLI de Tailwind (config compartida + extensión por tema, semilla de `#TOOL-04`), integrado a `build.sh`/Render y `collectstatic`.

#### `#AUD-12` — Endurecer settings de producción `[P2-Media]` `[S]` `[DevOps]`
Eliminar el override `DEBUG_PRODUCTION`; documentar variables de entorno requeridas y validarlas al boot (fail-fast con mensaje claro). Verificación `manage.py check --deploy` limpia.

#### `#RC-18` — Acuerdo comercial y dominio `[P1-Alta]` *(usuario)*
Propuesta, cobro por transferencia (observaciones → `#PAY-02`), compra de `ranchocachimba.cl` en NIC Chile.

---

## §5 · MEDIANO PLAZO — Estabilidad, seguridad y performance

#### `#MED-01` — Correo asíncrono `[P1-Alta]` `[M]` `[Backend]`
Hoy SMTP bloquea el hilo HTTP (~1-3 s por envío en Zoho). Sin broker disponible en Render free: cola en DB (modelo `EmailOutbox` + cron de Render cada 5 min, mismo mecanismo que `contact-digest`) o `threading` con `on_commit` como paso intermedio. Sube sobre `#AUD-06`.

#### `#MED-02` — Suite de aislamiento multi-tenant `[P0-Crítica]` `[M]` `[Backend]` `[Database]` *(absorbe `#SEC-04`)*
Portar `test_isolation` a tests reales (`apps/tenants/tests_isolation.py`): por cada modelo con FK a `Client`, lectura y escritura cross-tenant deben fallar. Incluye tests del nuevo `tenant_member_required` (`#AUD-03`) y del atributo de clase `_current_client` (decidir: thread-local o eliminación del auto-filtro).

#### `#MED-03` — Índices compuestos y revisión de consultas `[P1-Alta]` `[M]` `[Database]` *(absorbe `#DB-03`)*
Migraciones con `Meta.indexes`: `Section(client, is_active)`, `Service(client, is_active, order)`, `GalleryItem(client, gallery_type, is_active, order)`, `ContactSubmission(client, created_at)`. `EXPLAIN` sobre datos reales de Supabase antes/después.

#### `#MED-04` — Plantillas HTML transaccionales responsive `[P2-Media]` `[M]` `[Frontend]`
Rediseñar `templates/emails/*` (tablas, inline CSS, dark-mode friendly, texto plano decente). Probar en Gmail/Outlook móvil.

#### `#MED-05` — Rate limit y auditoría de IP confiable `[P2-Media]` `[S]` `[Backend]`
Tomar la IP del último proxy confiable (Render setea XFF); aplicar `RateLimiter` también a login (`scope='login'`) y checkout.

#### `#TOOL-01` — Playwright smoke multi-tenant `[P1-Alta]` `[M]` `[DevOps]`
`tests/e2e/` parametrizado por tenant: home 200, hero visible, formulario envía, navbar/footer. **DoD:** `npx playwright test` cubre servelec, andesscale y ranchocachimba.

#### `#TOOL-07` — `CLAUDE.md` en la raíz `[P1-Alta]` `[S]` `[DevOps]`
Comandos frecuentes, convenciones críticas (`render_tenant_template`, managers, `cloudinary_utils`, orden de `config/urls.py` — incluir la lección de `#AUD-01`), mapa de insumos de diseño, y el arnés de §2 como contrato. Mover `.claude/` desde `Documentacion/`.

#### `#AUD-10` — Higiene de repo + test anti-regresión de presets `[P2-Media]` `[S]` `[DevOps]` *(absorbe `#DEUDA-04` y el pendiente de `#DEUDA-01`)*
`git rm --cached db_production_test.sqlite3 exit`; ignorar `staticfiles/`, mover CSVs a `scripts/output/`; test que falla si `CLOUDINARY_PRESETS` reintroduce clave duplicada (definirlo como literal verificado o lint específico).

#### `#DEUDA-05` — Reconciliar README y skill con el código `[P2-Media]` `[S]` `[DevOps]`
`check_tenant_setup` ya existe — actualizar README; corregir `ClientSettings.template` → `Client.template` en README y skill; `Procedimiento_Nuevo_Tenant.md` ya existe en `Documentacion/` — validar contenido.

#### `#FLOW-01` / `#FLOW-02` / `#PAY-02` — Flujo comercial repetible `[P2-Media]` `[M]`
Procedimiento de ingreso de cliente + `check_tenant_setup` ampliado (SEOConfig completo, sin placeholders, `ClientEmailSettings`) + registro de fricciones del cobro manual de Cachimba (es la spec de `#FLOW-03`).

#### `#SEC-02` — Headers de seguridad `[P2-Media]` `[S]` `[DevOps]`
Ya hay HSTS/nosniff/X-Frame/cookies seguras; falta **CSP** (complicada por Tailwind CDN — hacer después de `#AUD-11`) y verificación externa. **DoD:** nota A en securityheaders.com para los 3 dominios.

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

### `#AUD-07` — Correo de producción confiable
- **Contexto:** fallback silencioso a console + URLs hardcodeadas `.andesscale.cl` rompen los correos de tenants con dominio propio.
- **Archivos:** `config/settings/production.py`, `apps/orders/services/email_service.py`.
- **Criterios de aceptación:**
  - [ ] En producción, sin credenciales SMTP: error explícito al arrancar (o log CRITICAL + health check en rojo), nunca console silencioso.
  - [ ] `send_welcome`/`send_site_ready` construyen `site_url` desde `client.get_absolute_url()`/`Domain` primario.
  - [ ] Los 5 templates de email renderizan con contexto completo (smoke test).
- **Verificación:** `python manage.py test apps.orders.tests.test_email_service` + envío real de prueba a una casilla propia tras el deploy (`manage.py shell` en Render, documentado en el runbook).

### `#AUD-08` / `#AUD-09` — Webhook honesto + onboarding sin mutar en GET
- **Archivos:** `apps/orders/views.py`, `apps/orders/views_onboarding.py`.
- **Criterios:** excepción inesperada en webhook → 500 (MP reintenta); `payment_id` ya procesado → 200 no-op idempotente con `PaymentLog` único; GET de onboarding no cambia `order.status`.
- **Verificación:** `python manage.py test apps.orders.tests.test_webhooks apps.orders.tests.test_onboarding`.

### `#PAY-03` — E2E sandbox
- **Contexto:** validar la cadena completa checkout→webhook→onboarding→tenant con MP en modo test.
- **Archivos:** sin cambios de código (es verificación); fixture de `Plan` de prueba (`apps/orders/management/commands/setup_plans.py`).
- **Criterios:** pago con tarjeta de prueba aprobado → orden `paid` + email con token → formulario de onboarding crea Client+Domain+User+secciones → orden `completed`. Tarjeta rechazada → orden `failed`, sin tenant.
- **Verificación:** manual guiada en sandbox + `python manage.py test apps.orders` completo en verde antes de intentarlo.

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

### `#MED-01` — Correo asíncrono (outbox + cron)
- **Archivos:** `apps/core/models.py` (`EmailOutbox`), `apps/core/management/commands/send_pending_emails.py`, `email_service.py` (encolar en vez de enviar cuando `EMAIL_ASYNC=True`), `render.yaml` (cron cada 5 min).
- **Criterios:** encolar es O(1 insert); el cron envía con reintentos (máx. 3, backoff) y marca `sent_at`/`failed_at`; un fallo de SMTP no afecta la request HTTP; correos "urgentes" (reset de contraseña) pueden forzar envío síncrono.
- **Verificación:** `python manage.py test apps.core.tests.test_email_outbox` — encolado, envío por comando, reintentos, idempotencia del cron.

### `#MED-02` — Suite de aislamiento multi-tenant
- **Archivos:** `apps/tenants/tests_isolation.py` (nuevo), `apps/tenants/managers.py` (decisión sobre `_current_client`).
- **Criterios:** para `Section`, `Service`, `GalleryItem`, `ContactSubmission`, `SEOConfig`, `ClientSettings`: usuario/dominio de A no lee ni escribe datos de B (vía HTTP con `HTTP_HOST`, no solo ORM); `_current_client` documentado como solo-para-comandos o migrado a thread-local.
- **Verificación:** `python manage.py test apps.tenants.tests_isolation` — corre en cada push (gate de §2).

### `#MED-03` — Índices compuestos
- **Archivos:** `apps/website/models.py`, `apps/marketing/models.py` + migraciones.
- **Criterios:** `Meta.indexes` según patrones de §1.2; `EXPLAIN ANALYZE` en Supabase muestra index scan en home y dashboard; `makemigrations --check` limpio después.
- **Verificación:** `python manage.py test apps.website` + `python manage.py makemigrations --check --dry-run`.

### `#MED-04` / `#MED-05` / `#TOOL-01` / `#TOOL-07` — ver §5; sus DoD son autocontenidos.

---

## §8 · RUTA CRÍTICA

```
GATE SEGURIDAD ✅ CERRADO (2026-08-20)   LANZAMIENTO CACHIMBA
AUD-01 ✅ → AUD-02 ✅ → AUD-03 ✅ → AUD-04 ✅   RC-01 → RC-06b ─┐
   │                                        RC-18 ──────────┼→ RC-08 (publicar Etapa 1)
   ▼ ESTAMOS AQUÍ                                           │
AUD-05/06/07 → PAY-03 (sandbox E2E)                         ▼
                                      RC-09 → RC-10 → RC-11 → RC-12 → RC-13
                                                                  │
              MEDIANO: MED-02 (aislamiento) ∥ MED-01 (async) ∥ AUD-11 (Tailwind)
                                                                  ▼
                                      RC-14 → RC-15 → RC-16 → RC-17 (cierre)
```

**Riesgo 1 — publicar con los P0 abiertos.** ✅ **Cerrado (2026-08-20).** `#AUD-03` (cross-tenant) ya no existe en el código de dashboard/login; sigue pendiente `#MED-02` para convertir el aislamiento del resto del ORM en suite automática.
**Riesgo 2 — el material del cliente.** `#RC-01`/`#RC-06b` dependen del usuario, no de código; son lo único que bloquea `#RC-08` una vez pasado el gate.
**Riesgo 3 — tocar Render sin reparar `render.yaml`.** ✅ **Cerrado (2026-08-20).** Falta solo confirmar contra el dashboard real de Render qué configuración quedó efectivamente activa (acción del usuario).

---

## Batería de validación inmediata (estado al 2026-08-20, post gate de seguridad)

```bash
python manage.py test apps                              # 35 tests · OK (1 skip) ✅
python manage.py makemigrations --check --dry-run       # sin pendientes ✅
python manage.py check --deploy --settings=config.settings.production
python manage.py check_tenant_setup ranchocachimba      # [OK] tema/dominio ✅ (sesión RC)
python manage.py test_isolation                         # manual, hasta #MED-02
python -m ruff check apps/ config/                      # 135 preexistentes fuera de lo tocado — #AUD-10
python -m ruff check <archivos tocados en el gate>      # limpio ✅
```

Dependencias de desarrollo nuevas (`requirements-dev.txt`): `ruff`, `bandit`, `coverage`, `pyyaml`. Instalar con `pip install -r requirements-dev.txt` antes de retomar.
