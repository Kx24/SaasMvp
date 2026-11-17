# Ronda 9 — estado

Rama `agent/ronda9` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-48` | `LEY-03` | Plazos de Order, PaymentLog y EmailOutbox | ✅ DONE | 662 | 0 |
| `BOLT-49` | `LEY-02` | Canal y registro de solicitudes de derechos (1 de 2) | ✅ DONE | 682 | 1.38 |
| `BOLT-50` | `LEY-02` | Exportar, suprimir y bloquear datos de una persona (2 de 2) | ⏳ TODO |  |  |
| `BOLT-51` | `OPS-04` | Alerta de créditos de Cloudinary | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-48`: Commit manual d1c25b2: el gate pasó al 2.º intento (e2e falló una vez y no se reprodujo) pero el validador no alcanzó a correr; la ronda se cortó a las 04:51.
- `BOLT-48`: BOLT-45 (LEY-08) rescatada del stash de la ronda 8 en 1baa89f, con conflictos resueltos a mano en base.py y SEGURIDAD.md; no pasó por el validador.
- `BOLT-49`: Migración 0024_data_subject_request: modelo nuevo, reversible, sin tocar datos existentes.
- `BOLT-49`: Textos visibles al público: formulario /privacidad/solicitud/, acuse de recibo y aviso al tenant (templates/emails/data_request_*, templates/legal/data_request.html).
- `BOLT-49`: Cambio en los cuerpos legales privacy_tenant_body y privacy_platform_body (enlace al formulario). PRIVACY_POLICY_VERSION no se tocó.
- `BOLT-49`: La identidad del solicitante no se verifica en el formulario: la respuesta va al correo indicado, por lo que alguien podría pedir datos ajenos. Conviene definir cómo se verifica antes de entregar datos en la parte 2.
- `BOLT-49`: Decisiones del dev que el spec no cubría: admin con campos de solo lectura y sin alta manual, y rate limit de 3 envíos cada 10 min por IP, que solo cuenta los envíos válidos.
- `BOLT-49`: El aviso del dashboard enlaza al superadmin. Confirmar que los roles con `view_contacts` que no son staff puedan abrir esa ruta, porque si no verán un enlace que no les sirve.

## Hallazgos incidentales

- `BOLT-49`: El enlace 'Gestionar' del aviso del dashboard tiene la ruta /superadmin/website/datasubjectrequest/ escrita a mano en vez de usar `reverse`.
- `BOLT-49`: Si una solicitud cerrada vuelve a un estado abierto, `resolved_at` conserva el valor anterior. No hay lógica que lo limpie.
