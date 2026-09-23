# CLAUDE.md — Corta (memoria del agente)

> Generado y mantenido por la skill `/collect-memory`. Refleja el estado
> actual de la misión, no un changelog de sesiones — para eso está
> `git log -- CLAUDE.md`.

## Estado de los milestones

- **Milestone 1 (trackear desde el principio):** hecho. Repo creado en
  `github.com/luzlaura/corta`, primer commit con la carpeta heredada tal cual
  se recibió, excepto `notas.txt` (ver Decisiones).
- **Milestone 2 (ordenar):** hecho. Sin archivos muertos ni duplicados, sin
  dependencias sin uso, con `README.md` y `.gitignore`.
- **Milestone 3 (corregir errores):** hecho. `server.js` ahora valida `url`
  (constructor nativo `URL`, solo `http:`/`https:`), genera códigos únicos
  contra `links.json`, y `GET /:codigo` hace un redirect real (`302`). Los
  30 tests pasan. Se adelantó también el endpoint
  `GET /api/links/:codigo/stats` (ver Milestone 4) porque el criterio de
  éxito de este milestone depende de poder consultar stats de forma fiable.
- **Milestone 4 (stats.html funcional):** a medias. El endpoint
  `GET /api/links/:codigo/stats` ya existe y tiene tests propios en verde
  (se implementó en Milestone 3, ver arriba). Falta conectar
  `public/stats.html` — hoy sigue mostrando datos hardcodeados (`123`
  clicks) y no llama al endpoint.
- **Milestone 5 (producción en Railway):** pendiente, no empezado.
- **Extra — trabajo en equipo (colaboradores + tarea programada):** pendiente.
- **Extra — memoria del agente (`/collect-memory`):** hecho (esta skill y
  este archivo).

## Decisiones tomadas

- `notas.txt` nunca viajó al repo remoto: tenía una credencial de Postgres en
  texto plano. Lo accionable de esa nota ya está volcado en `SPEC.md` §7.
- El repo de verdad de esta misión es `github.com/luzlaura/corta`, standalone.
  El trabajo de Milestone 1 y 2 se había hecho por error dentro del monorepo
  de cátedra `talksmith-ing` (`missions/clase2/corta/`); se reconstruyó un
  commit de Milestone 2 sobre la historia real que ya estaba en GitHub en vez
  de sobrescribirla. Esa copia dentro de `talksmith-ing`, y la rama local
  `corta-standalone` que se había armado ahí, quedaron obsoletas y sin usar.
- El directorio de trabajo local para esta misión es `~/projects/corta`
  (clon directo de `github.com/luzlaura/corta`), no una carpeta dentro de
  `talksmith-ing`.
- Autenticación contra GitHub vía `gh` CLI (se instaló con Homebrew en esta
  sesión y se logueó de forma interactiva), no SSH ni token pegado a mano.
- No se agregó ningún lock para la concurrencia de escritura a `links.json`.
  Los handlers de `server.js` son 100% síncronos (sin `await` entre leer y
  escribir), lo que en un proceso Node single-threaded ya serializa las
  escrituras sin necesidad de un lock manual — verificado con el test de 20
  `GET` concurrentes. Ver SPEC.md §4.4 para el razonamiento completo; esto
  deja de valer si Milestone 5 migra a async I/O o a múltiples procesos.
- El formato de error de la API no se unificó a propósito: `POST /api/links`
  y `GET /api/links/:codigo/stats` devuelven JSON `{ error }`, pero
  `GET /:codigo` mantiene texto plano en el 404 porque es la ruta que un
  browser visita directamente (nunca ve JSON crudo de otra forma tampoco).

## Preferencias del equipo

- Comunicación informal, en español.
- Antes de una operación de git que pueda perder o reemplazar historial
  (`reset --hard`, reescribir una rama, etc.), explicar en criollo qué se va
  a hacer y por qué es seguro en ese caso puntual, y pedir confirmación
  explícita antes de correrlo — no alcanza con la explicación técnica sola,
  tiene que quedar claro en términos simples qué carpeta/commit se ve
  afectado y qué no se pierde.
- Ante una decisión con varias alternativas razonables (ej. orden de
  Milestone 3 vs. push, método de autenticación), preguntar en vez de asumir.
