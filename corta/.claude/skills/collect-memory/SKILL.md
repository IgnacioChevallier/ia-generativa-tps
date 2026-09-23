---
name: collect-memory
description: Revisa la conversación en curso de la misión Corta y actualiza CLAUDE.md con el estado de los milestones (hechos, a medias, decisiones tomadas) y las preferencias de equipo expresadas (convenciones, reglas, gustos). Usar al cerrar cada sesión de trabajo para que la siguiente arranque con el contrato al día.
---

# /collect-memory

Cierra una sesión de trabajo sobre Corta dejando `CLAUDE.md` al día, para que
la próxima sesión no dependa de que alguien repita lo ya explicado.

## Paso 1 — Revisar la conversación en curso

Repasar la sesión actual (no el código ni `git log`, eso ya es legible por su
cuenta) buscando dos cosas distintas:

1. **Avances de la misión** — qué milestone(s) se completaron, cuáles quedaron
   a medias y por qué, y qué decisiones no triviales se tomaron (algo que no
   se explica solo leyendo el diff: un trade-off, una razón de seguridad, un
   "se decidió X en vez de Y y esto es por qué").
2. **Preferencias del equipo** — reglas o gustos que la persona expresó
   explícitamente sobre cómo trabajar (convenciones de commits, tono,
   herramientas preferidas, qué prefiere que se le pregunte antes de hacer).
   Solo lo que se dijo en la conversación, no se infiere del código.

Ignorar: detalles de una sola vez que no se van a repetir, y cualquier cosa
que ya esté documentada en `SPEC.md`, `README.md` o el propio `CLAUDE.md`.

## Paso 2 — Ubicar el archivo

```bash
find . -maxdepth 1 -iname "CLAUDE.md" -o -maxdepth 1 -iname "AGENTS.md"
```

Si no existe ninguno, crear `CLAUDE.md` en la raíz del repo.

## Paso 3 — Actualizar in place, no acumular

`CLAUDE.md` tiene tres secciones fijas. Editar la sección correspondiente
cada vez — nunca agregar una entrada nueva al final tipo changelog. El
archivo debe reflejar el estado **actual**, no un historial de sesiones (para
eso ya está `git log -- CLAUDE.md`).

```markdown
# CLAUDE.md — Corta (memoria del agente)

## Estado de los milestones
- Milestone 1 (trackear desde el principio): hecho / a medias / pendiente — nota breve.
- Milestone 2 (ordenar): ...
- Milestone 3 (corregir errores): ...
- Milestone 4 (stats.html funcional): ...
- Milestone 5 (producción): ...
- Extra: trabajo en equipo: ...
- Extra: memoria del agente: ...

## Decisiones tomadas
- Decisión — por qué se tomó, qué alternativa se descartó.

## Preferencias del equipo
- Preferencia — contexto de cuándo aplica.
```

Si un milestone pasa de "a medias" a "hecho", reemplazar la línea entera, no
agregar una nota al lado. Si una decisión queda obsoleta por una decisión
posterior, se reemplaza, no se tacha.

## Paso 4 — Mostrar el diff y confirmar

Antes de escribir, mostrar qué se va a agregar/cambiar/borrar de cada sección
y por qué. Aplicar solo lo que la persona confirme.

## Paso 5 — Commitear solo CLAUDE.md

```bash
git add CLAUDE.md
git commit -m "collect-memory: <resumen de una línea de la sesión>"
```

Un commit separado, solo con `CLAUDE.md` — así la historia de git de ese
archivo por sí sola muestra la evolución de la misión sin mezclarse con
commits de código.
