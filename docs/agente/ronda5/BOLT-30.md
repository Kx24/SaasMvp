# BOLT-30 — `SEC-12`: integración continua con el gate

## Contexto verificado (2026-11-14)

No existe `.github/workflows/`. El gate local es `scripts/gatekeeper.py --strict` (ruff en lo
tocado, suite con cobertura, `makemigrations --check`, y bandit y cobertura como trinquete contra
`scripts/gate_baseline.json`; el paso e2e solo corre si hay archivos cambiados respecto de HEAD,
así que en CI se omite solo). `requirements-dev.txt` trae las herramientas. `.env.example` lista
las variables; en desarrollo la suite corre con las de `.env`, y en CI no hay `.env`.

Esta card está autorizada a crear archivos bajo `.github/`.

## Qué hacer

1. `.github/workflows/ci.yml`:
   - Disparadores: `push` (todas las ramas) y `pull_request` hacia `develop` y `main`.
   - Un job en `ubuntu-latest`, Python igual al `PYTHON_VERSION` de `render.yaml`, con caché de pip.
   - Pasos: checkout → `pip install -r requirements-dev.txt` →
     `python scripts/gatekeeper.py --strict` →
     `python manage.py test apps.tenants.tests_isolation` (explícito aunque la suite lo incluya:
     es el gate de aislamiento) → `python -m ruff check apps/ config/` (repo completo: en CI el
     gate de ruff "en lo tocado" no ve nada) → `python -m pip_audit -r requirements.txt` (si
     `pip-audit` no está en `requirements-dev.txt`, instálalo en un paso propio).
   - Variables de entorno del job: valores **ficticios** para todo lo que `config.settings`
     (development) necesite para importar; averígualo leyendo `config/settings/base.py` y
     `development.py`, no adivines. Nunca un secreto real, nunca `secrets.*`.
   - `permissions: contents: read`. Acciones fijadas por versión mayor (`actions/checkout@v4`,
     `actions/setup-python@v5`).
   - `concurrency` por rama con `cancel-in-progress: true`.
2. Test nuevo `apps/core/tests/test_ci_workflow.py` (con `yaml.safe_load`; `pyyaml` está en dev):
   el workflow existe, dispara en `push` y `pull_request`, sus pasos ejecutan
   `gatekeeper.py --strict`, `tests_isolation`, `ruff check` y `pip_audit`, no usa `secrets.` y
   declara `permissions`. Si `yaml` no es importable, el test se salta con `skipUnless`.
3. Verifica localmente lo que puedas: que cada comando del workflow corre en tu entorno.
4. Documenta el control en `Documentacion/SEGURIDAD.md`. No toques `CLAUDE.md`.

## Aviso al dueño (ponlo en DECISIONES)

El primer resultado real del workflow se ve en GitHub Actions al hacer push de esta rama; si
falla por una variable de entorno faltante, se corrige en una card siguiente.

## Tests de rojo

`apps.core.tests.test_ci_workflow`

## DoD

- [ ] Workflow con los controles listados; sin secretos; permisos mínimos.
- [ ] Test de estructura verde.
- [ ] Cierre documental (`SEC-12`).
