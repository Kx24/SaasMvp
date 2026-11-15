# CLAUDE.md

Guía operativa para trabajar en este repo con Claude Code. La fuente única de verdad del *trabajo pendiente* es `Documentacion/KANBAN_PROYECTO.md` — este archivo es sobre *cómo* trabajar, no *qué* falta.

## Qué es esto

SaaS multi-tenant en Django: un mismo despliegue sirve varios sitios de clientes (tenants), cada uno resuelto por dominio. Stack: Django 5.2, Neon (Postgres) en producción vía `dj_database_url`, Cloudinary para media, Tailwind (por CDN, ver `#AUD-11`), Render para hosting.

## Comandos frecuentes

```bash
# Servidor de desarrollo (config.settings ya cae en development por defecto,
# salvo que DJANGO_ENVIRONMENT=production esté seteado)
python manage.py runserver 8000

# Suite completa (el número vigente de tests: ver Documentacion/KANBAN_PROYECTO.md)
python manage.py test apps -v 1

# Un solo módulo/test
python manage.py test apps.orders.tests.test_webhooks -v 2

# Aislamiento multi-tenant real (#MED-02) — lo corren el gate y la CI
python manage.py test apps.tenants.tests_isolation

# Lint (set conservador: pyflakes + pycodestyle + isort, ver ruff.toml)
python -m ruff check apps/ config/

# Migraciones pendientes
python manage.py makemigrations --check --dry-run

# Salud de settings de producción (no la corras sin saber qué env vars tenés)
python manage.py check --deploy --settings=config.settings.production

# Provisioning de un tenant nuevo (dev)
python manage.py provision_tenant <slug> --industry=<rubro> --theme=<theme>
python manage.py check_tenant_setup <slug>          # gate de QA, no modifica nada
python manage.py list_tenants
```

Dependencias de desarrollo (`ruff`, `bandit`, `coverage`, `pyyaml`) en `requirements-dev.txt`, separado de `requirements.txt`.

## Arquitectura multi-tenant — lo que hay que saber antes de tocar código

**Resolución de tenant:** `apps/tenants/middleware.py` inyecta `request.client` según el `Host` header (allowlist dinámica de dominios, ver `Domain` model). `localhost` es `SYSTEM_DOMAIN` (bypass, `request.client = None`), no un tenant real — no confundir con "usa el primer cliente activo" (ese comportamiento no existe hoy, hay un test con skip documentando la duda en `apps/tenants/tests.py`).

**Resolución de templates:** `apps/tenants/template_loader.py::TenantTemplateLoader`. Dado `template_name` (ej. `'landing/home.html'`), busca en este orden:
1. `templates/{tenant.template}/{template_name}` — `tenant.template` es el campo `Client.template` (`THEME_CHOICES`: `'themes/default'`, `'themes/servelec'`), o `tenant.slug` si `template` no está seteado. (`'themes/ranchocachimba'` existe solo en `feature/RanchocachimbaEtapa1`, no en esta rama.)
2. `templates/{template_name}` — fallback global, así es como resuelven `base.html`, `templates/components/*.html`, `templates/emails/*.html`, etc. compartidos entre temas.

Las vistas llaman `apps.core.template_resolver.render_tenant_template(request, template_path, context)` — **no** arman la ruta a mano (`f'tenants/{slug}/...'`); eso ya no existe, lo resuelve el loader.

Antes de escribir un componente nuevo: revisar si ya existe en 2+ temas (`themes/servelec`, `themes/default`, `andesscale`; `ranchocachimba` solo en `feature/RanchocachimbaEtapa1`); si es así, generalizarlo a `templates/components/` en vez de duplicarlo. Contrato completo y precedente real (`components/media_collection.html`, parámetro `mode` + slots de override por ruta de template) en `docs/design-system.md`.

**Brand tokens por tenant:** `ClientSettings` (color primario/secundario/accent, fuentes, logo) se inyecta como CSS custom properties — no hay valores de marca hardcodeados en JS/Tailwind config. Preferir utilidades Tailwind sobre `style=""` inline en templates nuevos (preferencia explícita del usuario).

**Managers (`apps/tenants/managers.py`):** `TenantAwareManager` **no filtra automáticamente por tenant** — el auto-filtro basado en `_current_client` se eliminó (`#MED-02`, 2026-08-22) porque nunca se seteaba en código de request real y era puro riesgo (atributo de clase compartido entre requests concurrentes). **Toda vista debe filtrar explícitamente** con `.filter(client=request.client)` o `Model.objects.for_client(client)`. No asumir que `Model.objects.all()` está scoped por tenant — no lo está.

**Autorización cross-tenant:** `apps/accounts/decorators.py::tenant_member_required` — exige que `request.user.profile.client == request.client` (o superuser). Todas las vistas de dashboard en `apps/website/views.py` lo usan; un `@login_required` solo no alcanza (ver `#AUD-03`).

**Cloudinary:** `apps/core/cloudinary_utils.py` centraliza upload/URLs/presets (`CLOUDINARY_PRESETS`, `get_cloudinary_url`, `upload_to_cloudinary`, `get_srcset_urls`). No armar URLs de Cloudinary a mano en templates/vistas.

**Emails transaccionales:** `apps/orders/services/email_service.py::EmailService`. Todo envío disparado dentro de un `transaction.atomic()` va envuelto en `transaction.on_commit(...)` (función local, no lambda, para capturar variables por valor) — nunca un `send_*` directo dentro de la transacción (`#AUD-06`: Django no revierte un SMTP ya enviado si la transacción hace rollback después). `EmailService._site_url(client)` resuelve la URL del sitio desde `Domain` primario, con fallback a `BASE_DOMAIN` — nunca hardcodear `.andesscale.cl`.

## Gotchas que ya mordieron a alguien

- **Orden de `apps/orders/urls.py`:** el patrón `<slug:plan_slug>/` debe ir **al final**. Si algo nuevo lo empuja arriba de `process/`/`success/`/`error/`, Django lo captura primero y esas rutas dejan de existir silenciosamente (404 real). Esto rompió el checkout entero una vez (`#AUD-01`).
- **`redirect('nombre_de_url', ...)` en `apps/orders/urls_onboarding.py`:** ese `include()` **no tiene namespace** en `config/urls.py` — usar `redirect('onboarding_success', ...)`, no `redirect('orders:onboarding_success', ...)`. El namespace `orders:` sí existe para `apps/orders/urls.py` (checkout), pero no para onboarding. Confundir los dos generó un `NoReverseMatch` atrapado por un `except Exception` genérico que mostraba "hubo un error" a clientes cuyo sitio SÍ se había creado (`#PAY-03`).
- **`UserProfile` se crea por signal**, no a mano: `apps/accounts/models.py::create_or_update_user_profile` (`post_save` de `User`) ya hace `get_or_create`. Un `UserProfile.objects.create(user=...)` posterior choca con el `OneToOneField` → `IntegrityError`. Usar `update_or_create`.
- **`config/settings/production.py`** falla al *importar* (no al hacer request) si faltan `SECRET_KEY`, `EMAIL_HOST_USER` o `EMAIL_HOST_PASSWORD` — es intencional (`#AUD-07`/`#AUD-12`, mismo patrón para las tres). `DEBUG` es `False` fijo, sin override por env var. Si necesitás correr algo contra `config.settings.production` localmente, esas tres env vars son obligatorias.
- **Django Admin vive en `/superadmin/`**, no en `/admin/` (ver `config/urls.py`) — a propósito, para no chocar con rutas de tenant.

## El arnés de TDD (contrato, no sugerencia)

Detalle completo en `Documentacion/KANBAN_PROYECTO.md`, sección "Arnés de TDD". Resumen:

1. Toda card de Backend/Database entrega un test que **falla sin el cambio** (rojo confirmado, no asumido — si el bug es de configuración/infra, reproducir el rojo contra el estado original con `git stash` cuando aplique).
2. Cobertura mínima: `apps/orders/` ≥ 80%, `apps/tenants/middleware.py`+`managers.py` ≥ 90%, resto ≥ 70%. Nunca baja.
3. Antes de dar una card por cerrada: `ruff check` en los archivos tocados, suite completa en verde, `makemigrations --check --dry-run` limpio.
4. Un commit por card (o sub-entregable coherente). Nada se commitea con la suite en rojo.
5. `python scripts/gatekeeper.py --strict` corre todo lo anterior de forma determinista; el trinquete de cobertura y bandit vive en `scripts/gate_baseline.json`, y `--red-check` confirma que los tests nuevos fallan contra el código original.
6. Si al escribir el test aparece un bug real fuera del alcance original de la card (pasó varias veces: signal de `UserProfile`, namespace de `redirect`, `_current_client` muerto): arreglarlo ahí mismo si bloquea el DoD, documentarlo como "hallazgo incidental" en el commit y en el kanban — no ignorarlo ni abrir una card nueva para "después".

## Branches

- `main` — producción.
- `develop` — integración. Recibe trabajo vía cherry-pick o PR desde branches de feature; ver historial reciente para el patrón (varias cards de robustez transaccional y aislamiento llegaron por cherry-pick individual, no por merge de branch completa).
- `feature/RanchocachimbaEtapa1` — trabajo de Rancho Cachimba (tema, contenido, provisioning) **en pausa** por decisión del usuario (necesita tiempo de diseño/investigación) — no tocar sin que lo pida explícitamente.
- `agent/*` — ramas del agente desatendido; son el único destino de push automático. Ver `docs/agente/README.md`.
- Antes de asumir que una branch está actualizada en GitHub: correr `git status --short --branch` y `git log origin/<branch>..<branch> --oneline`. Ya pasó que trabajo de una sesión completa quedó sin pushear.

## Git y PRs

Push y PRs los hace el dueño desde PyCharm/GitHub.

- Antes de cerrar una tarea o cambiar de rama: `git status --short --branch` y `git log origin/<rama>..<rama> --oneline`. Si hay commits sin pushear, avisar explícitamente.
- Cherry-pick hacia `develop`: solo mostrando antes el diff exacto (`git show <sha>`) y con confirmación explícita del usuario, por commit (o por tanda ya aprobada).

## Dónde mirar primero

- `Documentacion/KANBAN_PROYECTO.md` — qué está hecho, qué falta, por qué, en qué orden. Sección **"🌙 Retomar aquí"** al inicio siempre tiene el estado más reciente.
- `apps/*/tests/` — el comportamiento esperado documentado como test vale más que el docstring de al lado.
- `Documentacion/INDEX.md` — mapa de toda la documentación vigente y qué quedó en `Documentacion/historico/`.
- `Documentacion/ARQUITECTURA.md` — cada tecnología y qué hace, apps, modelo de datos, flujos. `Documentacion/SEGURIDAD.md` — controles, hallazgos abiertos, Ley 21.719 y checklist por release.
- Skill `andesscale-saas` (`.claude/skills/andesscale-saas/SKILL.md`) — profundiza en resolución de templates, filtrado por tenant y provisioning; cárgalo para trabajo específico de tenants/temas en vez de releer este archivo entero.
- `.idea/runConfigurations/` — los comandos frecuentes de arriba como run configurations de PyCharm (IDE principal desde 2026-11). Intérprete: `env/Scripts/python.exe` de este checkout.
