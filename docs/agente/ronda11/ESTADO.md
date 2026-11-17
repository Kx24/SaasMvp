# Ronda 11 — estado

Rama `agent/ronda11` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-56` | `COMP-02` | Ordenar el árbol de temas | ✅ DONE | 818 | 2.75 |
| `BOLT-57` | `COMP-01` | Componente cta compartido (1 de 7) | ⏳ TODO |  |  |
| `BOLT-58` | `COMP-01` | Componente about compartido (2 de 7) | ⏳ TODO |  |  |
| `BOLT-59` | `COMP-01` | Componente services compartido (3 de 7) | ⏳ TODO |  |  |
| `BOLT-60` | `COMP-01` | Componente contact compartido (4 de 7) | ⏳ TODO |  |  |
| `BOLT-61` | `COMP-01` | Componente footer compartido (5 de 7) | ⏳ TODO |  |  |
| `BOLT-62` | `COMP-01` | Componente navbar compartido (6 de 7) | ⏳ TODO |  |  |
| `BOLT-63` | `COMP-01` | hero_ctas y hero_overlay_theme compartidos; cierre (7 de 7) | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-56`: Migración 0031: es solo de datos. Hay que ensayarla en una rama de Neon antes de desplegar. Cambia Client.template del tenant con slug PLATFORM_TENANT_SLUG, y la reversa devuelve a 'themes/default' todos los clientes con 'themes/andesscale'.
- `BOLT-56`: Carpetas y archivos borrados: templates/themes/electricidad/ completa (base.html, landing/home.html y 4 componentes), templates_library/ (2 .gitkeep) y themes/default/components/about.html y contact.html (vacíos).
- `BOLT-56`: Abrir la home de la plataforma en el navegador. Se verificó que el HTML sea idéntico a la fixture, pero la fixture se generó en este mismo cambio y no se puede comprobar que sea anterior al movimiento.
- `BOLT-56`: THEME_CHOICES ahora incluye 'themes/andesscale', y por eso aparece en el onboarding (apps/orders/forms.py, con la etiqueta 'Plataforma'). Confirmar que un cliente no pueda elegirlo, o que Plan.available_themes lo filtre.
- `BOLT-56`: test_docs_theme_choices.py excluye 'themes/andesscale' de la comparación con las guías de agente, una decisión del dev que el spec no cubría.
- `BOLT-56`: El cambio en tests/e2e/a11y.spec.js (esperar animaciones finitas antes de axe) quedó fuera del alcance de la card. No cambia umbrales ni selectores.

## Hallazgos incidentales

- `BOLT-56`: themes/servelec/components/stats.html usa rgba(255,255,255,0.5) sobre #0f3320, con contraste estimado ~4,4:1 (cálculo manual, sin medir), cerca del mínimo AA de 4,5:1. No se tocó porque cambiaría el aspecto del sitio.
- `BOLT-56`: Dos tests de smoke de formularios de contacto fallaron con --repeat-each=4. El dev supone que es el límite anti-spam por email repetido y no lo comprobó. Una corrida normal pasa los 14 tests.
- `BOLT-56`: El dev no comprobó si el flake de a11y de Servelec ocurre también en el código original.
- `BOLT-56`: Líneas de CLAUDE.md que quedaron desfasadas: la mención a templates/{tema} como ruta de andesscale, y el texto que lista los temas sin themes/andesscale. Esta card no toca CLAUDE.md.
- `BOLT-56`: Comentarios obsoletos que citan themes/electricidad en apps/website/tests/test_contact_submit.py, apps/website/tests/test_navbar_cta.py y static/css/input.css.
