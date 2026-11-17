# KANBAN — AndesScale SaaS

> **Única fuente de verdad del trabajo pendiente.** Lo hecho: [`historico/KANBAN_HISTORICO.md`](historico/KANBAN_HISTORICO.md). Mapa de documentos: [`INDEX.md`](INDEX.md).
> Respaldo de este plan: [`AUDITORIA_PLATAFORMA_2026-11.md`](AUDITORIA_PLATAFORMA_2026-11.md) (plataforma), [`SEGURIDAD.md`](SEGURIDAD.md) (chequeo de seguridad y ley), [`ARQUITECTURA.md`](ARQUITECTURA.md) (cómo funciona).
> **Regla de tamaño:** ~300 líneas máximo. Al cerrar una card: una línea en el histórico y se borra de acá. El detalle largo va a su propio archivo.

---

## 🌙 Retomar aquí (actualizado 2026-11-16)

**Foco del trimestre (nov 2026 – feb 2027), sin captar clientes:** ① consolidar la plataforma (módulos reutilizables + dashboard profesional estilo Instagram/Gmail), ② ciberseguridad, ③ Ley 21.719.

**Decisiones vigentes:** composición de página `MOD-00` opción A ahora, B después (`MOD-02`). Seguridad y ley primero (la ley rige el 1-dic-2026). Matriz de roles de `DASH-04` confirmada, el editor sigue por defecto.

**Estado (2026-11-15):** rondas 3 a 7 del agente mergeadas en `main` (PR #3) y `develop` igualada a `main`. **Producción (Render `saasmvp`) sigue en el commit de agosto `1a5d3e2`**: el merge no se desplegó y Auto-Deploy debe quedar en Off hasta decidir. Cerradas: `LEY-01`, `DASH-04`, `SEC-06`, `SEC-10`, `SEC-14`, `CONS-04`/`05`/`06`/`07`, entre otras (detalle en `historico/KANBAN_HISTORICO.md` y `docs/agente/ronda*/`).
**Ensayo `OPS-07` hecho (2026-11-15):** rama de Neon `staging-ensayo` + servicio temporal `saasmvp-staging` desplegado desde `main` (5a2c734) con `./build.sh`. Build de 1 min, migraciones sin error, login, subida de imagen (`pillow` 13), `/privacidad/`, borrado de servicio y admin OK. Hallazgo: el Build Command de Render **no usaba `build.sh`** y sin él no se compila `output.css` (sitio sin estilos). Pendiente del ensayo: contacto con consentimiento y correo, checkout sandbox, portada de Servelec (`DEUDA-08`).
**Hecho en Render:** `FIELD_ENCRYPTION_KEY` creada y cargada, 2FA activo, Environment Group `saasmvp-shared`. **Aún sin crear:** crons `contact-digest` y `send-pending-emails` (`OPS-06`); sin el primero la purga de 365 días (`LEY-03`) no corre en producción.

**Pendiente tuyo, en orden:** ① cambiar el Build Command de `saasmvp` a `./build.sh` y hacer Manual Deploy de `main` (respaldo: rama de Neon `staging-ensayo`, o crear otra justo antes); ② probar en vivo login, `/privacidad/`, contacto y borrado de servicio; ③ crear los dos crons; ④ borrar `saasmvp-staging` y la rama de Neon; ⑤ activar protección de ramas en `main` y `develop`; ⑥ revisión legal de los textos de privacidad antes del 1-dic.

**Ritmo:** 2 días/semana × 4–5 h. Card que no entra en 2 h se parte. Rondas del agente: `orchestrate.py` + `claude -p` (Sonnet 5.5) sobre ramas `agent/*`; tú revisas el PR a `develop`.

**Rondas 8 y 9 (2026-11-16), en `agent/ronda8` y `agent/ronda9`, sin PR todavía:** ronda 8 con 12/12 (`CONS-11` cobertura al contrato: total 76 %, orders 92 %, tenants núcleo 100 %; `CONS-12`, `SEC-18`, `COMP-03`, `DEUDA-09`, `FLOW-04`, `TOOL-04`, `DOC-01`; `LEY-08` se rescató a mano del stash tras un timeout). Ronda 9: `LEY-03` (plazos de `Order`/`PaymentLog`/`EmailOutbox`) y `LEY-02` (formulario `/privacidad/solicitud/`, registro y comando `data_subject`). 697 tests. Detalle y puntos a revisar a mano en `docs/agente/ronda8/ESTADO.md` y `docs/agente/ronda9/ESTADO.md`; lo más sensible: `MercadoPagoError` sin envolver, reset de contraseña acotado al tenant, y `data_subject erase` (irreversible, usar `--dry-run`).

**▶️ Próximo:** `BOLT-51` (`OPS-04`) y ronda 10 (`CONS-08`, `CONS-09`, `BIZ-01`, `DASH-05`), luego ronda 11 (`COMP-02`, `COMP-01`). Tuyo: revisar y mergear los PR de las rondas 8 y 9 a `develop`; decidir `LEY-09` (verificación de identidad) antes de usar `data_subject export` con un titular real.

---

## 📖 Diccionario

### Prefijos de cards (activos)
| Prefijo | Significa | Ejemplo |
|---|---|---|
| `CONS` | **Consolidación**: ordenar y endurecer lo que ya existe, sin funcionalidad nueva | separar `views.py`, borrar rutas duplicadas |
| `COMP` | **Componentes**: piezas de template compartidas entre temas (`templates/components/`) | un solo `cta.html` para todos los temas |
| `MOD` | **Módulos**: funcionalidad que se activa por cliente o plan, con modelo + dashboard + componente público | Media, galería, testimonios |
| `DASH` | **Dashboard** del cliente: navegación, flujos, interacción, roles | flujo "Publicar" |
| `SEC` | **Ciberseguridad**: hallazgos y controles técnicos | admin por tenant, cifrado |
| `LEY` | **Ley 21.719** de datos personales: consentimiento, derechos, retención, contratos | página de política |
| `DB` | Base de datos: backups, índices, ramas de Neon | restore probado |
| `OPS` | Operación e infraestructura: Render, DNS, crons, monitoreo | cron de correos |
| `PAY` | Pagos (MercadoPago) | pasar a producción |
| `FLOW` | Flujo comercial y onboarding de clientes | autoservicio |
| `BIZ` | Negocio y contratos (puede no tocar código) | cláusulas |
| `MAIL` | Correo: entregabilidad y plantillas | SPF/DKIM |
| `PREV` | URL temporal `<slug>.andesscale.com` | wildcard |
| `DEUDA` | Deuda técnica sin urgencia | código muerto |
| `DOC` | Documentación | README |
| `TOOL` | Herramientas de desarrollo | escáneres |
| `RC` | Cliente Rancho Cachimba (en pausa) | landing |

**Prefijos históricos** (solo en el histórico, no crear cards nuevas): `AUD` auditoría 2026-08 · `MED` mediano plazo · `DS` design system · `BUG` · `BOLT` / `PILOT` piloto agéntico · `RC-BOLT` hero de Cachimba.

### Términos
| Término | Definición |
|---|---|
| **Tenant** | Un cliente con su sitio. En código: `Client`; en un request: `request.client` |
| **Tema** | Carpeta de templates que define el aspecto de un sitio (`themes/default`, `themes/servelec`) |
| **Componente** | Trozo de template reutilizable que se incluye con `{% include %}` |
| **Slot** | Hueco de un componente que un tema rellena pasando la ruta de otro template |
| **Módulo de funcionalidad** | Capacidad activable (galería, contacto, medios): datos + pantallas del dashboard + componente público |
| **Bloque de página** | Unidad visual de la home (hero, about, stats…). Hoy fija por tema |
| **Registro de módulos** | Lista central en código que declara cada módulo: nombre, flag, límites, URLs, entrada de menú, componente |
| **Preset** | Transformación de Cloudinary con nombre (`hero`, `thumbnail`…) |
| **Gate** | Verificaciones obligatorias antes de cerrar una card o desplegar |
| **DoD** | *Definition of Done*: condición verificable para dar una card por cerrada |
| **Hallazgo incidental** | Bug real encontrado fuera del alcance de la card; se arregla ahí y se anota |
| **P0–P3** | Prioridad: crítica · alta · media · baja |
| **S / M / L / XL** | Esfuerzo: <2 h · ~medio día · 1–2 días · >2 días (partir antes de empezar) |
| **D1, D2…** | Día de trabajo del plan (4–5 h), no día calendario. **Bloque A / B**: sus dos mitades |

---

## 🗓️ Plan de ejecución

### Fase 0 — Cerrar lo pendiente (D1)
| Día | Bloque A | Bloque B |
|---|---|---|
| D1 | `CONS-01` Push de `develop` + smoke test de producción | `SEC-10` ✅ Dependencias al día + `pip-audit` |

### Fase 1 — Seguridad y ley mínima (D2–D5, antes del 1-dic-2026)
| Día | Bloque A | Bloque B |
|---|---|---|
| D2 | `SEC-06` ✅ Credenciales SMTP/API cifradas | `SEC-06` ✅ (continúa: migración de datos y clave en Render) |
| D3 | `SEC-08` ✅ Un solo login (+ open redirect de `next`) | `CONS-04` ✅ Borrar rutas legacy |
| D4 | `LEY-01` ✅ Consentimiento en contacto y onboarding | `LEY-01` ✅ Página de política de privacidad (contenidos del art. 14 ter) |
| D5 | `SEC-14` ✅ + `SEC-17` ✅ Salidas sin escapar y comentarios DEBUG | `LEY-05` + `LEY-06` Registro de tratamientos y procedimiento de brechas (documentos) |

### Fase 2 — Consolidación (D6–D11, diciembre)
| Día | Bloque A | Bloque B |
|---|---|---|
| D6 | `DB-02` Backup de Neon con restore probado (+ `DB-03`) | `SEC-12` ✅ Integración continua con el gate |
| D7 | `CONS-02` ✅ Documentación al día (Neon, `CLAUDE.md`, README) | `DEUDA-08` ✅ Portada sin titular por defecto |
| D8 | `CONS-06` ✅ `TenantOwnedMixin` | `DASH-04` ✅ Roles con efecto |
| D9 | `SEC-05b` ✅ + `DEUDA-06` ✅ Restos del admin y código muerto | `CONS-07` ✅ Separar `views.py` |
| D10 | `CONS-08` ✅ Registro de módulos (opción A) | `CONS-08` ✅ (continúa) |
| D11 | `CONS-09` ✅ Menú del dashboard desde el registro | `CONS-05` ✅ Flags sin módulo |

### Fase 3 — Módulos y dashboard (~20 días, enero–febrero 2027)
Orden: `COMP-02` ✅ (1 d) → `COMP-01` (2 d) → `MOD-01` Media (5 d) → `DASH-01` (1 d) → `DASH-02` (4 d) → `DASH-03` (2 d) → `DASH-05` ✅ (1 d) → `LEY-02` ✅ + resto de `LEY-03` (2 d) → `LEY-04` + `LEY-07` (1 d) → `SEC-13` + `SEC-15` (2 d).
Después: `MOD-02` (opción B) y Rancho Cachimba — **no antes de marzo de 2027** (la meta anterior de mediados de febrero no cabe).

Las estimaciones no están medidas; recalibrar al cerrar cada fase.

---

## 🚧 Bloqueado — espera una decisión o insumo tuyo

| ID | Qué falta |
|---|---|
| `LEY-00` | Ubicar `Informe_Cumplimiento_Ley21719.md` (lo cita `MASTER_PLAN` §1.4, no está en el repo). Ya no bloquea: el texto de la ley está en `Documentacion/`. Sí conviene que un abogado revise la política (`LEY-01`) y el contrato (`LEY-07`) |
| `SEC-16` | Activar 2FA en Render, Neon, Cloudinary, Cloudflare, Zoho y GitHub; revisar qué cuentas `staff`/superuser existen en producción |
| `OPS-01` | Servelec: `servelec-ingenieria.cl` en NXDOMAIN (web **y correo** caídos), mitigado con `servelec.andesscale.com`. Definitivo: recuperar la clave NIC, o reactivar la zona en Bluehosting, o zona en Cloudflare + cambio de NS (A `@` 216.24.57.1, CNAME `www`, MX Zoho 10/20/50, SPF `v=spf1 include:zoho.com ~all`, DKIM). Confirmar en vivo los pasos de la mitigación |
| `PREV-00` | Decidir: wildcard `*.andesscale.com` (~US$29,78/mes) vs alta manual con `add_preview_domain` |
| `OPS-06` | Crear cron `send-pending-emails` en Render (pagado) para volver a `EMAIL_ASYNC=true`; tampoco existe `contact-digest` |
| `PAY-01` | MercadoPago a producción: `MP_*`, trámite SII, pasada manual en sandbox. Hoy apagado a propósito |
| `MAIL-01` | SPF/DKIM de Zoho; probar plantillas en Gmail/Outlook móvil |
| `SEC-09` | CSP en `/checkout/`; requiere sandbox de MercadoPago (después de `PAY-01`) |

---

## 📋 Cards

### `CONS` — Consolidación
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `CONS-01` | Push + smoke test de producción | P0 | S | Checklist del PR #2: login por tenant, login cruzado rechazado, contacto con correo real, links con `BASE_URL`, galerías, Tailwind, `check_tenant_setup` por tenant; deploy de Render en verde |
| `CONS-13` | Cobertura de lo que sigue en 0 % | P3 | M | Tests de vistas de `accounts`, admins, sitemaps y comandos de gestión (`audit_cloudinary_assets`, `check_cloudinary`, `verify_search_console`, `setup_*`, `seed_e2e_tenants`). Decidir antes si `create_tenant` se borra (parece muerto frente a `provision_tenant`) o se documenta. Hallado por `BOLT-39` |

### `COMP` — Componentes
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `COMP-01` | Generalizar componentes duplicados | P1 | L | `cta`, `about`, `services`, `contact`, `footer`, `navbar`, `hero_ctas`/`hero_overlay_theme` en `templates/components/` con el patrón de `media_collection` (parámetro `mode` + slots). Un componente por commit; a11y y guardia de tokens verdes |

### `MOD` — Módulos
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `MOD-01` | Módulo **Media** | P1 | XL (~5 d) | `MediaAsset` (imagen / video Cloudinary / embed YouTube-Vimeo), subida directa navegador→Cloudinary firmada, multi-archivo, límites por plan (`BIZ-01`). Unifica las 6 subidas del dashboard, que hoy llaman `cloudinary.uploader.upload` a mano con carpeta `{slug}/…` en vez de `upload_to_cloudinary` y `tenants/{slug}/…` (hallado por `BOLT-13`). Migra `Section.image`/`background_image`/`Service.image` al pool (~16 templates). DoD: subir 10 fotos y un video desde el celular; los 3 tenants renderizan igual |
| `MOD-02` | Orden y visibilidad de bloques (opción B) | P2 | L | El cliente reordena y oculta los bloques que su tema trae; cada `home.html` itera una lista en vez de includes fijos |

### `DASH` — Dashboard
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `DASH-01` | Navegación por tareas | P1 | M | Inicio (estado del sitio + qué sigue) · Publicar · Mensajes · Mi sitio · Ajustes, generado desde el registro |
| `DASH-02` | Flujo "Publicar" mobile-first | P1 | XL (~4 d) | Grilla de medios tipo Instagram sobre `MOD-01`. Una persona no técnica publica sin ayuda; probado con Servelec |
| `DASH-03` | Interacción con htmx | P2 | L | Guardar, ocultar y reordenar sin recargar; estados vacíos y de error. Servicios como patrón |
| `DASH-06` | Token `--primary` inexistente en el dashboard | P3 | S | `base.html` (avatar) e `index.html` usan `var(--primary)`, que el dashboard no define (solo `--color-primary`): el avatar y 3 elementos de `index.html` quedan sin color de marca. Cambiar a `var(--color-primary)` y cubrir con test. Hallado por `BOLT-55` |
| `DASH-07` | a11y del dashboard: pantallas sin cubrir y color de marca claro | P2 | M | `dashboard.spec.js` mide solo Inicio y Secciones; falta Marca, Portada, Galería, Mensajes y las pantallas de edición. Además `.btn-primary` y los botones "Editar" ponen texto blanco sobre el color de marca del tenant: con un primario claro no llegan a 4.5:1 (hoy pasa con `#0b5fa5`). Hallado por `BOLT-55` |

### `SEC` — Ciberseguridad (detalle y evidencia en `SEGURIDAD.md`)
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `SEC-13` | Endurecer `/superadmin/` | P1 | M | Segundo factor (TOTP) y rate limit en su login |
| `SEC-15` | Runbook de incidentes y rotación de secretos | P2 | S | Documento: qué hacer ante una fuga, cómo rotar cada secreto de `Inventario_Secretos.md`, a quién avisar (enlaza `LEY-06`) |

### `LEY` — Ley 21.719 (artículos y estado en `SEGURIDAD.md` §3; texto en `Ley-21719_13-DIC-2024.pdf`)
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `LEY-03` | Retención y purga (art. 14 d y principio de proporcionalidad) | P1 | M | Plazos y purga implementados (contactos 365 d, `Order`/`PaymentLog` 6 años, `EmailOutbox` 90 d; publicados en la política). Falta solo: cron en Render (`OPS-06`) para que corra en producción |
| `LEY-04` | Proveedores y transferencia internacional (art. 15 bis, 27–28) | P2 | S | DPA o cláusulas contractuales de Neon, Render, Cloudinary y Zoho archivados; listados en la política |
| `LEY-05` | Registro de tratamientos y bases de licitud (art. 13, 14, 14 quáter) | P1 | S | Documento por tratamiento: datos, finalidad, base de licitud, quién accede, conservación, proveedores. Decidido: IP sí, user-agent no |
| `LEY-06` | Procedimiento de brechas (art. 14 sexies) | P1 | S | Documento + plantilla de registro: detección, evaluación de riesgo, reporte a la Agencia, aviso al cliente responsable cuando AndesScale es encargado, aviso a titulares cuando corresponde |
| `LEY-07` | Contrato de encargo con clientes (art. 15 bis) | P1 | M | Cláusula con objeto, duración, finalidad, tipo de datos, categorías de titulares y obligaciones; autorización escrita de sub-encargados (Neon, Render, Cloudinary, Zoho); devolución o supresión al terminar (une con `BIZ-03`). Sin código; revisar con abogado |
| `LEY-09` | Cierre de `LEY-02`: verificación de identidad y huecos | P1 | M | Definir cómo se verifica al solicitante antes de entregar datos (hoy la respuesta va al correo que indica el formulario); un mensaje de un titular bloqueado no se abre por URL directa (`contacts.py`); backfill de `EmailOutbox.client` nulo para que `erase` los alcance; el aviso del dashboard usa `reverse` y solo se muestra a quien puede abrir `/superadmin/`; `resolved_at` se limpia al reabrir. Hallado por `BOLT-49` y `BOLT-50` |

### Negocio, datos y operación
| ID | Card | P | Esf. | Nota |
|---|---|---|---|---|
| `DB-02` | Backup de Neon con restore probado | P1 | M | Restore a una rama, documentado con tiempos |
| `DB-03` | `EXPLAIN ANALYZE` de consultas calientes en Neon | P3 | S | Junto a `DB-02` |
| `DEUDA-11` | `Client.max_pages` sin uso: decidir si se borra | P3 | S | No existe modelo de páginas, así que el límite no se aplica a nada (el default 10 sigue en `apps/tenants/models.py`). Borrarlo exige migración. Hallado por `BOLT-54` |
| `BIZ-02` | `Plan.renewal_price` y `Client.monthly_fee` alineados al modelo real | P2 | S | Pago único + mantención 12 meses + renovación anual (`MASTER_PLAN` §4.4). `Client.plan` es texto, no FK a `Plan`: decidir |
| `BIZ-03` | Cláusulas de mantención y fin de servicio | P2 | M | Sin código. `MASTER_PLAN` §4.5 |
| `FLOW-03` | Onboarding 100 % autoservicio | P2 | L | Depende de `PAY-01`; spec en `PAY-02` |
| `PAY-02` | Registro de fricciones del cobro manual | P3 | S | — |
| `TOOL-08` | `test_gatekeeper` sin falsos rojos | P2 | S | Sus tests lanzan el gate completo con tope fijo de 120 s y fallan por tiempo con la máquina cargada. Mitigado en las rondas del agente (`orchestrate.py` exporta `GATEKEEPER_TEST_RUN`); falta que no falle en la suite a mano. Hallado por `BOLT-44`, `46`, `47` |
| `DEUDA-10` | `check_tenant_setup` falla en un tenant recién provisionado | P2 | S | Da `[FAIL]` por falta de `SEOConfig('home')`: que `provision_tenant` lo cree o que el chequeo lo trate como aviso. Hallado por `BOLT-44` |
| `OPS-05` | Cache compartida, `/health/` real, Sentry | P3 | M | Antes de más de un proceso |
| `OPS-07` | Ensayo de despliegue antes de `develop` → `main` | P0 | M | **Ensayo hecho 2026-11-15** (ver Retomar aquí). Falta el deploy real de `main`: Build Command de `saasmvp` → `./build.sh`, Manual Deploy y pruebas en vivo; luego borrar `saasmvp-staging` y la rama `staging-ensayo`. Pendiente de probar: formulario de contacto con consentimiento y correo, checkout sandbox (en local con credenciales `TEST-`), portada de Servelec. Build medido: 1 min |

### `RC` — Rancho Cachimba ⏸️ (rama `feature/RanchocachimbaEtapa1`; no tocar sin pedido explícito)
| ID | Card | Depende de |
|---|---|---|
| `RC-01` | Inventario del material del cliente | Tú, en paralelo |
| `RC-18` | Acuerdo comercial y dominio `ranchocachimba.cl` | Tú |
| `RC-06b` | Pasada de diseño real del hero | `RC-01` |
| `RC-09` / `RC-10` | Landing por componente; sección del pastor | `COMP-01`, `MOD-01` |
| `RC-11` | Contenido real y media; favicon y `logo_footer` | `RC-01` |
| `RC-12` | Formulario de contacto + SMTP del tenant | `MAIL-01` |
| `RC-13` | SEO local + JSON-LD | `SEC-14` |
| `RC-21` | Pill "El oficio" oculto bajo el header fijo | — |
| `RC-22` | Integrar la rama a `develop` | Fase 3 terminada |
| `RC-08` | Publicar Etapa 1 | todo lo anterior |
| `RC-14`–`17` | QA + Lighthouse · Search Console · entrega · retrospectiva | `RC-08` |

### Congelado
`DB-01` rama de base por feature · `DB-04` pgvector · `TOOL-02` StackHawk/Strix · `TOOL-03` MCPs · marketing/GA4/Ads · sprints de venta (`MASTER_PLAN` §3.5).

---

## 🧪 Arnés de TDD (contrato, no sugerencia)

1. Toda card Backend/Database entrega un test que **falla sin el cambio** (rojo confirmado; si es de infra, reproducir con `git stash`).
2. Cobertura mínima, que nunca baja: `apps/orders/` ≥ 80 %, `apps/tenants/middleware.py` + `managers.py` ≥ 90 %, resto ≥ 70 %.
3. Antes de cerrar: `ruff check` en lo tocado, suite completa verde, `makemigrations --check --dry-run` limpio.
4. Un commit por card, con el ID en el mensaje. Nada se commitea en rojo.
5. Hallazgo incidental que bloquea el DoD: se arregla ahí y se anota en el commit y en el histórico.
6. Bucle: SPEC (rojo) → CODE (verde) → VERIFY → REPAIR (máx. 3 vueltas; a la 4ª, parar y reportar) → CLOSE.

| Verificación | Comando |
|---|---|
| Suite | `python manage.py test apps -v 1` |
| Aislamiento | `python manage.py test apps.tenants.tests_isolation` |
| Lint | `python -m ruff check apps/ config/` |
| Migraciones | `python manage.py makemigrations --check --dry-run` |
| Seguridad estática | `python -m bandit -r apps config -x "*/tests/*,*/migrations/*" -ll -q` |
| Producción | `python manage.py check --deploy --settings=config.settings.production` |
| E2E + a11y | `npx playwright test` |
| Tenant listo | `python manage.py check_tenant_setup <slug> [--check-dns]` |

## 🔗 Satélites
- **Ejecución agéntica (ronda 4 en adelante, 2026-11-14):** `docs/agente/README.md` (operación), `docs/agente/ronda<N>/` (specs, `cola.json`, `ESTADO.md`). `orchestrate.py --ronda …` corre cada card con Sonnet 5.5 y verifica con `scripts/gatekeeper.py --strict`. Las cards nuevas se crean acá; los specs los escribe la sesión de planificación.
- **Piloto agéntico, rondas 1–3 (histórico):** `docs/kanban_agente.md`, `docs/infoagente.md`, `docs/tratamiento_git.md`.
  **Ronda 3 (ejecutada 2026-11-12, 6/6 DONE, pendiente de PR):** `BOLT-11` `CONS-10` · `BOLT-12` `SEC-07` · `BOLT-13` `SEC-11` · `BOLT-14` `LEY-03` parcial · `BOLT-15` `SEC-05` · `BOLT-16` `CONS-03`, en la rama `agent/fase1-seguridad`. `orchestrate.py` no tiene agente conectado: se ejecuta con una sesión de Claude Code siguiendo `.claude/workflows/`.
- **Estrategia y negocio:** `MASTER_PLAN_Y_ARQUITECTURA.md`.
