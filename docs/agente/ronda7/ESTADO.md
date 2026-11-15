# Ronda 7 — estado

Rama `agent/ronda7` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-33` | `LEY-01` | Política de privacidad publicada y versionada (1 de 2) | ✅ DONE | 379 | 0.7 |
| `BOLT-34` | `LEY-01` | Consentimiento probado; sin user-agent (2 de 2) | ✅ DONE | 390 | 0.94 |
| `BOLT-35` | `DASH-04` | Roles con efecto en el dashboard | ✅ DONE | 404 | 1.09 |

## Revisar a mano en el PR

- `BOLT-33`: Texto legal pendiente de revisión por abogado (privacy_*.html).
- `BOLT-33`: Los dos cuerpos legales: confirmar que son copia fiel de docs/agente/ronda7/textos/. El único cambio declarado es {# #} multilínea por {% comment %}. No pude verificar esto con diff.
- `BOLT-33`: check_tenant_setup: la falta de contact_email es solo [WARN], no falla. El spec admitía ambas opciones.
- `BOLT-33`: Cierre en el kanban: la fila D4 del plan de ejecución quedó sin ✅ porque LEY-01 sigue abierta (BOLT-34). La fila del histórico dice LEY-01 (parte).
- `BOLT-33`: Nuevo setting PLATFORM_TENANT_SLUG, configurable por env var (default 'andesscale'). Confirmar que coincide con el slug real del tenant de la plataforma en producción.
- `BOLT-34`: Las dos migraciones (website 0023 y orders 0003) borran de forma irreversible los user-agent ya guardados. Es lo que pidió el dueño.
- `BOLT-34`: Flujo de checkout: `accept_privacy` debe ser exactamente `true`, si no devuelve 400 `MISSING_CONSENT`. Conviene probarlo a mano con el sandbox de MercadoPago.
- `BOLT-34`: El onboarding no lleva checkbox por decisión del dueño. Solo tiene un aviso con enlace a la política. Revisar el texto del aviso, que es visible al cliente.
- `BOLT-34`: Los textos de consentimiento en los formularios de contacto y en el checkout son visibles al cliente. En `contact_form_dynamic.html` el `privacy_text` configurable de `FormConfig` convive con el checkbox nuevo.
- `BOLT-34`: Un POST clásico de contacto sin consentimiento devuelve JSON 400, igual que ya hacía con cualquier otro error de validación. Confirmar que ese comportamiento es aceptable para el formulario sin JS.
- `BOLT-35`: Matriz tal como quedó. `view_dashboard` (inicio, secciones, galería): owner, admin, editor y viewer. `view_contacts`, `edit_content` y `manage_contacts`: owner, admin y editor. `delete_content` (borrar servicios e imágenes) y `manage_branding`: owner y admin. Los 403 usan 'No tienes permiso para esta acción.'
- `BOLT-35`: Tests existentes que cambiaron de rol: ninguno. Los tests anteriores pasaron sin modificarse.
- `BOLT-35`: Decisión del dev fuera del spec: el panel 'Últimos contactos' del inicio se oculta, y no se consulta, para roles sin `view_contacts`. Los contadores agregados siguen visibles.
- `BOLT-35`: Cambio de permisos y de settings: nuevo context processor `apps.accounts.context_processors.dashboard_permissions` en `config/settings/base.py`.
- `BOLT-35`: El rojo confirmado es solo por ImportError (falta `apps.accounts.permissions`). No hay un rojo conductual aparte.
- `BOLT-35`: Revisar en el navegador que los botones de editar, borrar, marca y mensajes se oculten bien con un `viewer` y con un `editor`.

## Hallazgos incidentales

- `BOLT-33`: Los enlaces "Términos" y "Cookies" del footer de andesscale siguen en href="#" (templates/andesscale/components/footer.html:196-197). Quedan fuera de alcance y no tienen fila en el kanban.
- `BOLT-33`: Los dos cuerpos legales conservan la frase "REVISAR CON ABOGADO" dentro de un bloque {% comment %}. No se renderiza, pero está en el archivo.
- `BOLT-33`: El dev no corrió Playwright ni el rojo; los cubrió el gate del orquestador.
- `BOLT-35`: `templates/dashboard/gallery.html`: el `{% include ... with ... %}` multilínea del estado vacío no se renderiza y muestra la etiqueta cruda (preexistente, no tocado).
- `BOLT-35`: `dashboard_services` y `dashboard/services.html` parecen código muerto sin ruta. La vista sigue con `@tenant_member_required`.
- `BOLT-35`: El spec habla de 21 vistas, pero son 19 rutas más 2 alias de nombre (`create_service_dashboard`, `toggle_service`) que comparten función con otras vistas.
