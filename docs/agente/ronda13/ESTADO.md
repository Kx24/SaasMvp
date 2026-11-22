# Ronda 13 — estado

Rama `agent/ronda13` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-68` | `DASH-09` | Fondo del ícono de mensajes con token de marca | ✅ DONE | 854 | 0.31 |
| `BOLT-69` | `DEUDA-13` | Plan.get_available_themes_list sin slug inválido | ✅ DONE | 859 | 0.35 |
| `BOLT-72` | `OPS-05` | Endpoint /health/ real (parte) | ✅ DONE | 870 | 0.43 |
| `BOLT-70` | `CONS-13` | Cobertura de comandos de gestión (1 de 2) | ✅ DONE | 907 | 0.62 |
| `BOLT-71` | `CONS-13` | Cobertura de vistas de accounts, sitemaps y admins (2 de 2) | ✅ DONE | 934 | 0.63 |

## Revisar a mano en el PR

- `BOLT-68`: Revisar en el navegador que el fondo del ícono de Contactos tome el color de marca del tenant (hoy lo cubre solo el test, no una prueba visual).
- `BOLT-69`: Cambio de comportamiento visible en el onboarding: un plan con available_themes que contenga solo slugs viejos (p. ej. 'default') ahora ofrece únicamente themes/default. Conviene revisar los datos reales de los planes en Neon.
- `BOLT-69`: Se modificaron dos tests existentes (test_onboarding_views, test_pay03_e2e_sandbox) para adaptarlos al nuevo slug; no se debilitó ninguna aserción.
- `BOLT-72`: Configurar en el dashboard de Render el Health Check Path = /health/ (render.yaml no sincroniza el servicio).
- `BOLT-72`: Cambio en apps/tenants/middleware.py: bypass de la ruta exacta /health/ antes de resolver Host (request.client = None). Revisar que sea aceptable.
- `BOLT-72`: Verificar tras el deploy que el health check no reciba 301 por SECURE_SSL_REDIRECT.
- `BOLT-72`: En el histórico se usó el formato de tabla de las filas vecinas, no la viñeta del spec.
- `BOLT-70`: Decidir si create_tenant se borra o se documenta (parece muerto frente a provision_tenant); quedó cubierto y anotado en el kanban.
- `BOLT-70`: El dev quitó un import sin uso en un test después de la corrida con cobertura. El gate (suite y ruff) corrió sobre el estado final y pasó, así que el riesgo es mínimo.
- `BOLT-71`: Archivos escogidos, cobertura antes → después: marketing/views_robots.py 14→90 %; marketing/views_verification.py 14→86 %; marketing/sitemaps.py 33→93 %; tenants/views.py 38→92 %; marketing/views_sitemap.py 41→88 %; marketing/admin.py 48→92 %.
- `BOLT-71`: El hallazgo de TenantSectionsSitemap no tiene fila en el kanban; conviene abrir una card para que no se pierda.
- `BOLT-71`: La decisión pendiente sobre create_tenant (borrar o documentar) ahora vive solo en el histórico, no en el kanban; considera reabrirla como card.
- `BOLT-71`: El dev no corrió makemigrations --check ni Playwright; el gate sí pasó migraciones (e2e no se ejecutó). No se tocaron modelos, templates ni estáticos.
- `BOLT-71`: Los tests de vistas de tenants y del admin usan HTTP_HOST='localhost' (dominio de sistema), porque 'testserver' da 404 en el middleware.
- `BOLT-71`: Los 'antes' de la tabla de cobertura salen de una medición que no omitía los archivos de test, y el dev no pudo verificarlos con el gate.

## Hallazgos incidentales

- `BOLT-69`: Otros fixtures de tests siguen con available_themes=['default'] (test_checkout_consent, test_checkout_views, test_onboarding, test_onboarding_views, core/test_data_subject_command). Hoy pasan, pero usan el slug inválido que ahora se filtra.
- `BOLT-72`: Con SECURE_SSL_REDIRECT=True en producción, un health check por HTTP plano sin X-Forwarded-Proto recibiría 301 (el dev no lo cambió). Render normalmente envía el proto correcto, pero conviene verificarlo tras el deploy.
- `BOLT-70`: audit_cloudinary_assets: cualquier CharField de cualquier modelo cuenta como referencia a un asset, así que un asset puede parecer referenciado por un valor que no es un public_id.
- `BOLT-70`: setup_cloudinary_folders usa cloudinary.api sin importarlo; funciona solo porque otro módulo lo importa antes.
- `BOLT-70`: Los conteos de tests por archivo del informe del dev (21/6/10) difieren de los que cuenta grep (19/6/12), pero el total de 37 coincide con el histórico.
- `BOLT-71`: TenantSectionsSitemap siempre devuelve vacío: Section no tiene campo slug ni existe la ruta website:section_detail, y los except lo ocultan. No se corrigió ni se abrió fila en el kanban.
- `BOLT-71`: create_tenant parece muerto frente a provision_tenant; la decisión de borrarlo o documentarlo quedó solo en la línea del histórico.
