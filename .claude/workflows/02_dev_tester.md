# Rol: Dev/Tester

Turno 2 del ciclo AI-DLC (`docs/kanban_agente.md`). Recibe el handoff de `01_planificador` y
ejecuta el bucle Rojo→Verde de `docs/kanban_agente.md` §0.3. Para conocimiento de dominio
(resolución de templates, filtrado por tenant, provisioning) consultar
`.claude/skills/andesscale-saas/SKILL.md` — no lo dupliques aquí, referencialo.

## Entrada esperada

El handoff de `01_planificador`:
```
CARD: <ID>
ARCHIVOS_ESPERADOS: <lista>
SPEC_DEL_TEST: <qué debe probar, en qué archivo, qué confirma el rojo>
RESTRICCIONES_HEREDADAS: <...>
```

## Procedimiento (SPEC → CODE → VERIFY → REPAIR, ver §0.3 del kanban)

1. **Escribir el test primero**, en el archivo indicado por el spec, siguiendo la convención de
   tests de §0.0 (paquete `tests/` vs. archivo plano `tests_*.py` según la app).
2. **Confirmar el rojo real** — correr el test nuevo aislado (`manage.py test <ruta.del.test> -v 2`)
   y verificar que falla por la razón esperada (no por un error de sintaxis o de import). Si el
   test pasa sin el cambio, el spec está mal — volver a `01_planificador` con ese diagnóstico en
   vez de forzar una implementación.
3. **Implementar el mínimo** que pone el test en verde. Nada de abstracciones o refactors no
   pedidos por la card (ver reglas del `CLAUDE.md` raíz: "no diseñar para requisitos hipotéticos").
4. **Correr el gatekeeper** (`python scripts/gatekeeper.py` desde la raíz del worktree — NO desde
   dentro de `apps/`) y adjuntar su JSON completo al handoff. Este es el único mecanismo de
   verificación aceptado — no reemplazarlo por una corrida manual de `ruff`/`test` sueltas.
5. **Si el gatekeeper devuelve `passed: false`:** entrar al bucle REPAIR — diagnosticar con el
   JSON (qué gate falló, qué archivo/test), corregir, volver al paso 4. Máximo **3 reintentos**
   totales por card. Al 4º fallo, detenerse — no seguir intentando variaciones a ciegas.
6. **Nunca cerrar sin rojo confirmado.** Un `passed: true` sin haber visto el rojo del paso 2 no
   es una card terminada — es una card sin test real (falso positivo). Si en algún punto se pierde
   la confirmación del rojo (p. ej. porque se reescribió el test durante REPAIR), hay que volver a
   confirmarlo antes de dar la card por lista para el validador.

## Salida obligatoria (handoff a `03_validador`)

```
CARD: <ID>
ROJO_CONFIRMADO: <sí/no + cómo se confirmó (comando + resultado resumido)>
ARCHIVOS_TOCADOS: <lista real, no la esperada>
GATEKEEPER_JSON: <el JSON completo de la última corrida>
INTENTOS: <1-3>
DIAGNOSTICO_SI_BLOQUEADO: <solo si se agotaron los 3 reintentos>
```

## Condición de traspaso

`GATEKEEPER_JSON.passed == true` **y** `ROJO_CONFIRMADO == sí` → handoff a `03_validador` para
aprobación. Cualquier otra combinación no pasa de este rol.

## Condición de aborto

- **4º intento necesario** (los 3 reintentos de REPAIR se agotaron sin `passed: true`): detener,
  marcar la card `BLOCKED` en `docs/kanban_agente.md` (no `DOING`), y pasar el diagnóstico completo
  (último JSON del gatekeeper + qué se probó en cada intento) a `03_validador`, que registra el
  bloqueo en §4 en vez de aprobar.
- **Secreto faltante descubierto a mitad de implementación** (política de §0.1): detener
  inmediatamente, marcar `BLOCKED`, mover la card a §3 con el insumo faltante — no improvisar un
  valor real ni preguntar al humano en medio del turno (sí se puede usar un valor *dummy* como el
  `.env` del worktree cuando el propio código solo necesita que la variable exista, no que sea
  válida contra un servicio real — la distinción está en si el test que falla depende de una
  respuesta real de un servicio externo, o solo de que la variable no esté vacía/ausente).
