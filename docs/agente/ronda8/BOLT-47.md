# BOLT-47 — `DOC-01`: documentación al día tras las rondas 4 a 8

## Contexto verificado (2026-11-15)

Desfases conocidos (verifica cada uno con `git grep` antes de editar; puede haber más):

- `README.md`, `Documentacion/README.md` y `MASTER_PLAN` citan `OrderProcessor` y
  `cloudinary_settings.py`, borrados en `DEUDA-06` (`BOLT-25`).
- `Documentacion/INDEX.md` (líneas ~29 y ~54) referencia archivos movidos o borrados.
- `Documentacion/ARQUITECTURA.md` (~línea 57) describe `apps/website/views.py` como un archivo de
  1.099 líneas; desde `CONS-07` es el paquete `apps/website/views/`.
- `Documentacion/SEGURIDAD.md` dice que `SEC-14` tiene 21 avisos de bandit; hoy
  `bandit_medium_high` es 0 (`scripts/gate_baseline.json`).
- Novedades sin documentar o a medio documentar: roles del dashboard (`DASH-04`,
  `apps/accounts/permissions.py`), política de privacidad y consentimiento (`LEY-01`),
  credenciales cifradas y `FIELD_ENCRYPTION_KEY` (`SEC-06`), reintento por cuota del orquestador,
  y el hallazgo del ensayo `OPS-07`: **el Build Command de Render debe ser `./build.sh`** (compila
  Tailwind; sin él el sitio sale sin estilos).

## Qué hacer

1. Corrige cada desfase de la lista y los que encuentres con
   `git grep -n "OrderProcessor\|cloudinary_settings\|views\.py\|Supabase" -- '*.md'`.
   Regla: la documentación describe el código que existe hoy; lo histórico va a
   `Documentacion/historico/` o se borra.
2. `Documentacion/ARQUITECTURA.md`: sección de despliegue con el Build Command `./build.sh`, las
   variables obligatorias de producción (`SECRET_KEY`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`,
   `FIELD_ENCRYPTION_KEY`, `DATABASE_URL`) y la nota de que Render no se sincroniza desde
   `render.yaml`.
3. `Documentacion/SEGURIDAD.md`: estado real de cada hallazgo cerrado en las rondas 4 a 8
   (consulta `Documentacion/historico/KANBAN_HISTORICO.md`).
4. `docs/agente/README.md` **no** se puede editar (ruta protegida): si está desfasado, repórtalo.
5. Un test de documentación (`apps/core/tests/test_docs_vigentes.py`): ningún
   `.md` vigente fuera de `Documentacion/historico/` y `docs/` menciona `OrderProcessor`,
   `cloudinary_settings` ni `Supabase`; los enlaces relativos de `Documentacion/INDEX.md` apuntan
   a archivos que existen.

## Tests de rojo

`apps.core.tests.test_docs_vigentes` (archivo nuevo con ese nombre exacto: el orquestador confirma el rojo con esa etiqueta).

## No tocar

`CLAUDE.md`, `.claude/` (el skill `andesscale-saas` lo corrige el dueño a mano), `docs/agente/`,
`Documentacion/historico/`, los textos legales, y la sección "Retomar aquí" del kanban.

## DoD

- [ ] Ningún documento vigente describe código que no existe.
- [ ] Test de documentación verde.
- [ ] Cierre documental (`DOC-01`). En `revisar_humano`: lo que quedó para el dueño (`CLAUDE.md`,
      el skill, `docs/agente/README.md`).
