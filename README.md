# AndesScale SaaS

SaaS multi-tenant en Django: un mismo despliegue sirve varios sitios de clientes (tenants), cada uno resuelto por dominio (`Domain`), con temas de templates y marca (`ClientSettings`) por tenant.

## Stack

- Django 5.2, Python 3 (`requirements.txt`; herramientas de desarrollo en `requirements-dev.txt`)
- Base de datos: Neon (Postgres) en producción vía `dj_database_url`; SQLite en desarrollo
- Media: Cloudinary (ver `docs/CLOUDINARY.md`)
- Frontend: Tailwind (build con `npm run build:css`) + htmx; E2E con Playwright
- Pagos: Mercado Pago; hosting: Render

## Cómo levantar

```bash
python -m venv env && env/Scripts/activate      # Linux/Mac: source env/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
npm install && npm run build:css                 # sin esto el sitio no tiene estilos
cp .env.example .env                             # completar variables
python manage.py migrate
python manage.py runserver 8000
```

El Django Admin vive en `/superadmin/`. `localhost` es el dominio del sistema (sin tenant); para un tenant nuevo:
`python manage.py provision_tenant <slug> --industry=<rubro> --theme=<theme>` y luego `python manage.py check_tenant_setup <slug>`.

## Tests y gate

```bash
python manage.py test apps -v 1                  # suite completa
python manage.py test apps.tenants.tests_isolation   # aislamiento multi-tenant
python -m ruff check apps/ config/               # lint
python scripts/gatekeeper.py --strict            # gate completo (lint, tests, migraciones, cobertura, bandit, Playwright)
```

La CI (`.github/workflows/ci.yml`) corre las verificaciones en GitHub Actions.

## Documentación

- `CLAUDE.md` — guía operativa del repo (arquitectura multi-tenant, gotchas, arnés de TDD, ramas).
- `Documentacion/INDEX.md` — mapa de toda la documentación vigente; `Documentacion/KANBAN_PROYECTO.md` — trabajo pendiente.
- `Documentacion/ARQUITECTURA.md`, `Documentacion/SEGURIDAD.md` — arquitectura y seguridad.
- `docs/agente/README.md` — ejecución agéntica desatendida (ramas `agent/*`).
