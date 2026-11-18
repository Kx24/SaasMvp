# Ronda 12 — estado

Rama `agent/ronda12` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-64` | `DASH-06` | Token --primary inexistente en el dashboard | ✅ DONE | 848 | 0.81 |
| `BOLT-65` | `TOOL-08` | test_gatekeeper sin falsos rojos | ✅ DONE | 849 | 0.82 |
| `BOLT-66` | `DEUDA-12` | Residuos de las rondas 10 y 11 | ✅ DONE | 852 | 0.55 |
| `BOLT-67` | `SEC-15` | Runbook de incidentes y rotación de secretos | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-64`: El dev modificó `apps/core/tests/test_docs_theme_choices.py`, que el spec no mencionaba, para que la suite pasara: CLAUDE.md cita `themes/andesscale` y el test lo excluía. Confirmar que ese criterio (CLAUDE.md compara con el conjunto completo, SKILL.md sin andesscale) es el que quieres.
- `BOLT-64`: Decidir si `--primary-rgb` merece su propia card, porque el fondo del ícono sigue sin el color de marca.
- `BOLT-65`: Un valor no entero en GATEKEEPER_TEST_TIMEOUT_S cae silenciosamente al valor por defecto de 900 s, sin avisar.
- `BOLT-65`: El módulo nuevo apps/core/gatekeeper_runner.py es código de herramienta dentro de apps/core: decisión del dev para que el rojo no se evalúe sobre archivos de test copiados.
- `BOLT-66`: Se borraron `templates/themes/default/components/hero_overlay.html` y `templates/themes/servelec/components/hero_overlay.html`. Conviene verificar a mano que ninguna home de tema los resuelve por nombre dinámico: el grep del validador no encontró referencias.
- `BOLT-66`: El dev modificó `test_component_footer.normalize_html` para neutralizar `© 2024` porque la fixture default no es editable. Es un ajuste del test, no del contenido; revisar si se prefiere regenerar la fixture.
- `BOLT-66`: Decidir si se abre una card para `Plan.get_available_themes_list` (devuelve `['default']`); el dev no la creó.
- `BOLT-66`: El dev no corrió Playwright pese a tocar `templates/`; el gate sí ejecutó e2e y pasó.

## Hallazgos incidentales

- `BOLT-64`: `index.html` línea 23 usa `var(--primary-rgb, 59, 130, 246)` para el fondo del ícono. Ese token tampoco existe, así que siempre cae al azul por defecto en vez del color de marca. Queda fuera del alcance de la card y sin registrar.
- `BOLT-66`: `Plan.get_available_themes_list` (apps/orders/models.py:206) devuelve `['default']`, un slug inválido, cuando `available_themes` no es una lista. Es el mismo bug que se arregla en la vista, pero queda sin cubrir y sin fila en el kanban.
- `BOLT-66`: El caso (b) del test se corrigió tras el primer intento (404 por el host) y no se volvió a correr contra el código original; el red-check del gate sí lo confirmó en rojo (2 fallos).
