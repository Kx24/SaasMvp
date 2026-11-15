# BOLT-27 — `SEC-10`: dependencias al día y `pip-audit`

## Contexto verificado (2026-11-14)

- `requirements.txt` es un `pip freeze` que mezcla producción con herramientas de desarrollo:
  `ipython` y su árbol (`asttokens`, `decorator`, `executing`, `ipython_pygments_lexers`, `jedi`,
  `matplotlib-inline`, `parso`, `prompt_toolkit`, `pure_eval`, `Pygments`, `stack-data`,
  `traitlets`, `wcwidth`, `colorama`) y `django-extensions` (está en `INSTALLED_APPS`,
  `config/settings/base.py:79`).
- `djangorestframework==3.15.1` está instalado y **nadie lo importa** (`git grep rest_framework`
  vacío en `apps` y `config`).
- `Django==5.2.6` y `gunicorn==21.2.0` están atrasados.
- `requirements-dev.txt` hace `-r requirements.txt` y agrega `ruff`, `bandit`, `coverage`, `pyyaml`.
- Python local: 3.13.7. `render.yaml` declara `PYTHON_VERSION` en tres servicios (líneas 40, 171, 229).

## Decisiones del dueño (2026-11-15) — prevalecen sobre cualquier otra instrucción de este spec

1. **`pillow` puede subir de mayor** (11 → 13): es la única excepción a "no cambiar de mayor" y lo
   único que impide un `pip-audit` limpio. Tras subirlo corre los tests de subidas
   (`apps.website.tests.test_upload_validation`) y los de render de imágenes; si algo se rompe por
   la API de pillow, corrígelo en el código que lo usa, sin debilitar tests.
2. **Python NO se cambia.** Render y la CI usan 3.11 y producción funciona. No toques
   `PYTHON_VERSION` de `render.yaml`. El test de versiones solo verifica que los tres servicios de
   `render.yaml` declaren el mismo `PYTHON_VERSION` y que coincida con el `python-version` de
   `.github/workflows/ci.yml` (léelo con `yaml`); **no** lo compares con el intérprete local.
3. Ignora el punto 6 de "Qué hacer" (igualar Python local).
4. La CI (`.github/workflows/ci.yml`) ya ejecuta `pip-audit`: debe quedar verde con este cambio.
5. Tras actualizar versiones, corre `npx playwright test` tú mismo (esta card sube Django y
   pillow: el e2e es la prueba de humo real) y deja el resultado en el informe.

## Dependencia autorizada

`pip-audit` (solo en `requirements-dev.txt`). Tienes red para `pip`. Mover `django-extensions`
e `ipython` de un archivo al otro también está autorizado.

## Qué hacer

1. Test nuevo `apps/core/tests/test_requirements.py` (lee los archivos, no instala nada):
   - `requirements.txt` no contiene `djangorestframework`, `ipython` ni su árbol, ni
     `django-extensions`.
   - `requirements-dev.txt` contiene `pip-audit`, `django-extensions` e `ipython`.
   - La versión de Django fijada es 5.2.x, con x mayor o igual al último parche que
     `python -m pip index versions Django` muestre hoy (deja el número en el test).
   - Todas las líneas de `requirements.txt` están fijadas con `==`.
   - `PYTHON_VERSION` vale lo mismo en los tres servicios de `render.yaml` y su mayor.menor
     coincide con el `python-version` de `.github/workflows/ci.yml`.
2. Mueve `django-extensions` e `ipython` a `requirements-dev.txt` (solo los paquetes de primer
   nivel; el árbol transitivo se resuelve solo). Como `django_extensions` está en
   `INSTALLED_APPS`, sácalo de `base.py` y agrégalo solo en `development.py` (y en `e2e.py` si lo
   necesita), de modo que producción no lo requiera.
3. Quita `djangorestframework`.
4. Actualiza Django al último 5.2.x y `gunicorn` a la última estable; reinstala
   (`python -m pip install -r requirements-dev.txt`) y corre la suite.
5. `python -m pip_audit -r requirements.txt`: sin vulnerabilidades conocidas. Si alguna exige
   subir otro paquete (por ejemplo `requests`, `urllib3`, `pillow`, `certifi`), súbelo dentro del
   mismo mayor. Si la corrección exige cambiar de versión mayor, no lo hagas: repórtalo.
6. (Anulado por las decisiones del dueño: no tocar Python.)
7. `check --deploy --settings=config.settings.production` necesita variables: no lo corras. Los
   tests de `apps/core/tests/test_production_settings.py` ya cubren ese import.

## No tocar

`build.sh`, `Procfile`. No cambies de mayor ningún paquete salvo `pillow`. No agregues paquetes fuera de
`pip-audit`.

## Tests de rojo

`apps.core.tests.test_requirements`

## DoD

- [ ] `python -m pip_audit -r requirements.txt` limpio, **sin avisos restantes** (pega el
      resumen en el informe). Si queda alguno que no puedes corregir, declara
      `RESULTADO: BLOQUEADA` con el paquete y el aviso.
- [ ] Django en el último 5.2.x; gunicorn actualizado; DRF y herramientas de desarrollo fuera de
      producción.
- [ ] Suite y Playwright verdes con las versiones nuevas.
- [ ] Cierre documental (`SEC-10`). En DECISIONES, lista cada paquete con versión anterior → nueva.
