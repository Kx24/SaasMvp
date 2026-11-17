# BOLT-51 — `OPS-04`: alerta de créditos de Cloudinary

> **Decisión del dueño (2026-11-15):** aviso al 70 % y alerta al 90 % de los créditos.

## Contexto verificado (2026-11-15)

- `apps/core/management/commands/cloudinary_usage.py` consulta el uso y lo imprime con colores;
  tiene umbrales escritos a mano (70 / 85 / 95) y **no avisa a nadie**. Cobertura 0 %.
- `CLOUDINARY_ALERT_THRESHOLDS` vivía en `cloudinary_settings.py`, borrado en `DEUDA-06`.
- No hay cron propio para esto; en Render solo se planifican `send_contact_digest` (semanal) y
  `send_pending_emails`.

## Qué hacer

1. Setting en `config/settings/base.py`:
   `CLOUDINARY_ALERT_THRESHOLDS = {'warning': 70, 'critical': 90}` y
   `PLATFORM_ALERT_EMAIL = config('PLATFORM_ALERT_EMAIL', default='')`.
2. `cloudinary_usage` usa esos umbrales (borra los números escritos a mano) y gana `--alert`:
   si el porcentaje de créditos supera `warning` o `critical`, envía **un** correo a
   `PLATFORM_ALERT_EMAIL` con el nivel, el porcentaje, usados/límite y qué hacer; por debajo de
   `warning` no envía nada. Sin `PLATFORM_ALERT_EMAIL` configurado, registra un warning en el log
   y termina sin error. Código de salida 0 siempre que la consulta funcione (un cron no debe
   fallar por una alerta).
3. Para no depender de un cron nuevo: `send_contact_digest` ejecuta la comprobación con alerta una
   vez por corrida (misma regla que la purga de `BOLT-48`: un fallo aquí se registra y no impide
   el digest; respeta `--dry-run`).
4. La API de Cloudinary se parchea en los tests; ninguna llamada real.
5. `Documentacion/ARQUITECTURA.md` (operación): la variable `PLATFORM_ALERT_EMAIL` y los umbrales.

## Tests de rojo

`apps.core.tests.test_cloudinary_usage_alert` (archivo nuevo con ese nombre exacto). Casos: 50 % →
sin correo; 75 % → correo "aviso"; 93 % → correo "alerta"; sin `PLATFORM_ALERT_EMAIL` → sin correo
y sin excepción; error de la API → mensaje claro y el digest sigue; `--dry-run` del digest no
envía la alerta; los umbrales salen del setting (cambiar el setting cambia el resultado).

## No tocar

`apps/core/cloudinary_utils.py` (subidas y URLs). `render.yaml`.

## DoD

- [ ] La plataforma recibe un correo al cruzar 70 % y 90 %.
- [ ] Cierre documental (`OPS-04`).
- [ ] En `revisar_humano`: hay que crear `PLATFORM_ALERT_EMAIL` en Render (web y crons).
