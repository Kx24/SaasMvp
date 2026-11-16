# BOLT-46 — `TOOL-04`: pulido de la CI y de las dependencias de desarrollo

> **Permiso especial de esta card (dueño, 2026-11-15):** puede editar `.github/workflows/ci.yml`
> y `requirements-dev.txt`. Nada más de `.github/`.

## Contexto verificado (2026-11-15)

- `.github/workflows/ci.yml`: `on: push:` (sin filtro) + `pull_request: branches: [develop, main]`
  → cada push a una rama con PR abierto corre la CI dos veces.
- `requirements-dev.txt`: `pip-audit` sin versión; el resto fijado (`ruff==0.16.4`,
  `bandit==1.7.*`, `coverage==7.*`, `pyyaml==6.0.*`, `django-extensions==4.1`, `ipython==9.8.0`).
- La CI usa Python `3.11`; Render usa `PYTHON_VERSION=3.11.0`.
- `Procfile`: `web: gunicorn config.wsgi:application` (verificado en Render con `gunicorn` 27 el
  2026-11-15: arranca).
- `django_extensions` solo se agrega a `INSTALLED_APPS` en `config/settings/development.py:33`.

## Qué hacer

1. **Doble ejecución:** limita el trigger `push` a `branches: [develop, main, 'agent/**']` y deja
   `pull_request` para `develop` y `main`; con el `concurrency` existente basta. Objetivo: un push
   a una rama `agent/*` corre la CI una vez; un PR la corre una vez por actualización. Explica en
   un comentario del YAML por qué.
2. **`pip-audit` fijado:** fija la versión que hoy resuelve (`pip-audit==<versión instalada>`,
   consulta `python -m pip show pip-audit`). No agregues ni actualices otras dependencias.
3. **Python:** deja un comentario en el YAML que diga que Render fija `3.11.0` y la CI usa el
   último parche de `3.11` a propósito (o fija el mismo parche si `actions/setup-python` lo
   ofrece sin coste). No cambies la versión mayor/menor.
4. **`django_extensions`:** agrega un test que afirme que `config.settings.production` y
   `config.settings.base` no lo incluyen en `INSTALLED_APPS`, y que ningún comando de
   `build.sh` / `Procfile` depende de él (lee los archivos; no los modifiques).
5. Valida el YAML (`python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"`).

## No tocar

`build.sh`, `Procfile`, `render.yaml`, `requirements.txt`, los pasos del job (gate, aislamiento,
ruff, pip-audit) y sus variables ficticias.

## DoD

- [ ] La CI no se duplica; `pip-audit` con versión fija; test de `django_extensions` verde.
- [ ] `python scripts/gatekeeper.py --strict` verde.
- [ ] Cierre documental (`TOOL-04`). En `revisar_humano`: el diff del workflow, porque el dueño
      debe confirmar en GitHub que el primer push corre la CI una sola vez.
