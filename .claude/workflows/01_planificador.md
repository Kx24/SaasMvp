# Rol: Planificador (ronda 4 en adelante)

Desde la ronda 4 el planificador **no es un turno del bucle desatendido**. Lo hace una sesión
interactiva con el modelo grande, junto al dueño del producto, antes de lanzar la ronda:

1. Elegir las cards del kanban maestro (`Documentacion/KANBAN_PROYECTO.md`) que se pueden cerrar
   sin secretos, sin producción y sin decisiones abiertas. Lo que necesita una decisión se
   resuelve con el dueño **antes** y la decisión se escribe en el spec.
2. Leer el código y escribir un spec por card en `docs/agente/ronda<N>/BOLT-XX.md` con: contexto
   verificado (archivos y líneas), decisiones ya tomadas, qué hacer, qué no tocar, tests de rojo
   (labels exactos), DoD verificable y cierre documental.
3. Registrar la card en `docs/agente/ronda<N>/cola.json`:

```json
{
  "id": "BOLT-17", "maestra": "SEC-17", "titulo": "…", "estado": "TODO", "spec": "BOLT-17.md",
  "red_tests": ["apps.website.tests.test_x"],
  "permite_migracion": false,
  "deps_permitidas": [],
  "rutas_permitidas_extra": []
}
```

   - `red_tests`: labels que `gatekeeper.py --red-check` corre contra HEAD; deben fallar sin el
     cambio. Vacío solo en cards sin comportamiento nuevo (borrado puro, documentos).
   - `permite_migracion`, `deps_permitidas`, `rutas_permitidas_extra`: lo único que abre el
     control de alcance de `orchestrate.py` para esa card.
4. Orden de la cola = orden de ejecución (WIP 1). Cards que tocan el mismo archivo van seguidas y
   la más invasiva al final.

Ejecución: `python orchestrate.py --ronda docs/agente/ronda<N>/cola.json --max-cards 4`.
El orquestador toma la primera card `TODO`; el estado legible queda en
`docs/agente/ronda<N>/ESTADO.md`. Detalle operativo en `docs/agente/README.md`.
