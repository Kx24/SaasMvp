# Ronda 9 — estado

Rama `agent/ronda9` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-48` | `LEY-03` | Plazos de Order, PaymentLog y EmailOutbox | ✅ DONE | 662 | 0 |
| `BOLT-49` | `LEY-02` | Canal y registro de solicitudes de derechos (1 de 2) | ✅ DONE | 682 | 1.38 |
| `BOLT-50` | `LEY-02` | Exportar, suprimir y bloquear datos de una persona (2 de 2) | ✅ DONE | 697 | 0.87 |
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
- `BOLT-50`: erase es IRREVERSIBLE: borra los mensajes de contacto y los correos en cola (EmailOutbox) de la persona en ese tenant. Hacer siempre --dry-run antes.
- `BOLT-50`: Campos de Order anonimizados: buyer_name, buyer_phone, billing_rut, billing_razon_social y billing_direccion pasan a '[suprimido]'; ip_address pasa a None; email pasa a suprimido-<hash HMAC con SECRET_KEY>@invalid. billing_giro y billing_comuna NO se tocan. Anonimizar razon_social y direccion fue decisión del dev, no del spec.
- `BOLT-50`: Campos de PaymentLog: ip_address pasa a None. En raw_data, las claves de PII_KEYS (payer, email, first_name, last_name, name, phone, identification, ip, address, rut, cardholder y similares) pasan a '[suprimido]', y también cualquier string igual al correo. Montos, estados e ids de pago se conservan.
- `BOLT-50`: El hash del correo anonimizado depende de SECRET_KEY. Si la clave rota, el hash cambia, pero sigue sin ser reversible.
- `BOLT-50`: Migraciones: core 0002 (EmailOutbox.client, FK nula con SET_NULL) y website 0025 (BlockedSubject). Ninguna borra datos.
- `BOLT-50`: Las compras con Order.client nulo se asignan al tenant de plataforma (PLATFORM_TENANT_SLUG): confirmar que ese criterio es correcto.
- `BOLT-50`: Modelos con datos personales que quedaron fuera: cuentas auth.User y UserProfile; ClientSettings, Client.contact_email y los from_email y reply_to de configuración del tenant (datos del cliente, no de terceros); logs de aplicación y backups.
- `BOLT-50`: Los mensajes de contacto bloqueados siguen accesibles por URL directa de detalle (ver hallazgos).

## Hallazgos incidentales

- `BOLT-49`: El enlace 'Gestionar' del aviso del dashboard tiene la ruta /superadmin/website/datasubjectrequest/ escrita a mano en vez de usar `reverse`.
- `BOLT-49`: Si una solicitud cerrada vuelve a un estado abierto, `resolved_at` conserva el valor anterior. No hay lógica que lo limpie.
- `BOLT-50`: Las vistas de detalle y cambio de estado de un mensaje (contacts.py, vía tenant_object_or_404 por id) no excluyen titulares bloqueados. Un mensaje bloqueado sigue accesible por URL directa si se conoce el id.
- `BOLT-50`: EmailOutbox históricos quedan con client NULL. erase no los alcanza, porque filtra por client, y no hay backfill.
- `BOLT-50`: El filtro por correo en PaymentLog.raw_data depende de una lista fija de claves (PII_KEYS). Claves no previstas en payloads de Mercado Pago no se depuran.
- `BOLT-50`: Las cuentas de dashboard (auth.User y UserProfile) quedan fuera de esta card, como pedía el spec.
