# Ronda 13 — estado

Rama `agent/ronda13` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-68` | `DASH-09` | Fondo del ícono de mensajes con token de marca | ✅ DONE | 854 | 0.31 |
| `BOLT-69` | `DEUDA-13` | Plan.get_available_themes_list sin slug inválido | ✅ DONE | 859 | 0.35 |
| `BOLT-72` | `OPS-05` | Endpoint /health/ real (parte) | ⏳ TODO |  |  |
| `BOLT-70` | `CONS-13` | Cobertura de comandos de gestión (1 de 2) | ⏳ TODO |  |  |
| `BOLT-71` | `CONS-13` | Cobertura de vistas de accounts, sitemaps y admins (2 de 2) | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-68`: Revisar en el navegador que el fondo del ícono de Contactos tome el color de marca del tenant (hoy lo cubre solo el test, no una prueba visual).
- `BOLT-69`: Cambio de comportamiento visible en el onboarding: un plan con available_themes que contenga solo slugs viejos (p. ej. 'default') ahora ofrece únicamente themes/default. Conviene revisar los datos reales de los planes en Neon.
- `BOLT-69`: Se modificaron dos tests existentes (test_onboarding_views, test_pay03_e2e_sandbox) para adaptarlos al nuevo slug; no se debilitó ninguna aserción.

## Hallazgos incidentales

- `BOLT-69`: Otros fixtures de tests siguen con available_themes=['default'] (test_checkout_consent, test_checkout_views, test_onboarding, test_onboarding_views, core/test_data_subject_command). Hoy pasan, pero usan el slug inválido que ahora se filtra.
