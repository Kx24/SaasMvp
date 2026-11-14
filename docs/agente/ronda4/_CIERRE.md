# Cierre documental (común a todas las cards de la ronda 4)

Va en el mismo cambio que el código. Tres ediciones, nada más:

1. `Documentacion/KANBAN_PROYECTO.md`: borra la fila de la card maestra de su tabla (o acótala si
   el spec dice "parcial"). Si la card aparece en las tablas del "Plan de ejecución", deja el ID
   pero agrégale ` ✅`. No reescribas otras secciones ni "Retomar aquí".
2. `Documentacion/historico/KANBAN_HISTORICO.md`: agrega **una línea** al final de la sección de
   cards cerradas que corresponda al prefijo, con el formato de las líneas vecinas:
   `- **\`<MAESTRA>\` <título>** (2026-11-14, \`BOLT-XX\`): <qué quedó hecho, una frase>.`
3. Si descubriste un hallazgo incidental que **no** arreglaste, agrégalo como fila nueva en la
   tabla del prefijo que corresponda en `KANBAN_PROYECTO.md` (ID siguiente libre, prioridad y
   esfuerzo estimados, "Hallado por `BOLT-XX`").

No toques `docs/kanban_agente.md` (histórico de las rondas 1–3) ni `docs/agente/` (el estado de
la ronda lo escribe el orquestador).
