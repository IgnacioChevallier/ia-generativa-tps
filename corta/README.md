# Corta

Acortador de URLs interno de la empresa. Node.js + Express, persiste en PostgreSQL
(ver `SPEC.md` §1 y §9 — antes de Milestone 5 persistía en un archivo `links.json`).

## Cómo correr

Necesitás una Postgres real (local o el proxy público de la de Railway) y su URL en
`DATABASE_URL`. Copiá `.env.example` a `.env` y completá el valor real ahí (`.env` está
en `.gitignore`, nunca se commitea):

```bash
cp .env.example .env   # completar DATABASE_URL con una Postgres real
npm install
npm start        # http://localhost:3000
npm test         # batería de tests (node --test) — usa la misma DATABASE_URL
```

**Ojo con los tests:** cada suite hace `DELETE FROM links` antes de sembrar sus propios
datos de prueba. Correr `npm test` contra la base de producción borra los links reales
— para eso está pensado tener un `DATABASE_URL` de desarrollo/tests separado del de
producción (Railway usa la interna en prod; ver `SPEC.md` §9).

## Estructura

```
server.js              punto de entrada (npm start). Define los endpoints.
utils.js                generación del código corto.
db.js                   pool de Postgres y creación del schema (tabla `links`).
scripts/seed-legacy-links.js  migración única de los links heredados (ya corrida).
public/
  index.html              formulario para acortar una URL.
  stats.html              consulta de estadísticas de un link (maqueta, ver SPEC.md §3.4).
  estilos.css             estilos de ambas páginas.
  logo.png                logo usado en index.html.
tests/                    batería TDD derivada de SPEC.md.
  helpers/testServer.js     arranca/para server.js como subproceso; siembra/lee contra Postgres.
SPEC.md                 comportamiento esperado de cada endpoint, casos borde, decisiones.
```

## Estado del proyecto

Este repo se heredó sin documentación de un desarrollador anterior. `SPEC.md` es la
fuente de verdad sobre qué hace cada endpoint hoy, qué bugs tiene y qué falta. Corré
`npm test` para ver qué comportamiento esperado todavía no se cumple.

## Qué se sacó al ordenar el repo (y por qué)

La carpeta original tenía archivos muertos, duplicados y una nota con una credencial
en texto plano. Se eliminaron antes del primer commit:

- `index_v2_FINAL.js`, `server_OLD.js` — versiones viejas de `server.js`, no referenciadas
  por `package.json`.
- `test.js` — script manual, reemplazado por la suite en `tests/`.
- `links_backup_marzo.json` — backup manual y desactualizado de `links.json`.
- `notas.txt` — notas sueltas del dev anterior; contenía una credencial de Postgres en
  texto plano. Lo accionable (TODOs, decisiones) ya está incorporado a `SPEC.md`.
- `public/estilos_viejos.css` — no lo referenciaba ningún HTML.
- `public/logo (1).png` → renombrado a `public/logo.png` (nombre de descarga duplicada).
- `axios`, `lodash`, `moment` del `package.json` — sin uso en el código activo.
