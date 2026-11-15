# Ronda 7 — estado

Rama `agent/ronda7` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-33` | `LEY-01` | Política de privacidad publicada y versionada (1 de 2) | ✅ DONE | 379 | 0.7 |
| `BOLT-34` | `LEY-01` | Consentimiento probado; sin user-agent (2 de 2) | ✅ DONE | 390 | 0.94 |
| `BOLT-35` | `DASH-04` | Roles con efecto en el dashboard | ⏳ TODO |  |  |

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

## Hallazgos incidentales

- `BOLT-33`: Los enlaces "Términos" y "Cookies" del footer de andesscale siguen en href="#" (templates/andesscale/components/footer.html:196-197). Quedan fuera de alcance y no tienen fila en el kanban.
- `BOLT-33`: Los dos cuerpos legales conservan la frase "REVISAR CON ABOGADO" dentro de un bloque {% comment %}. No se renderiza, pero está en el archivo.
- `BOLT-33`: El dev no corrió Playwright ni el rojo; los cubrió el gate del orquestador.
