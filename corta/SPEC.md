# SPEC.md — Corta

> Documento vivo. Se escribió leyendo el código heredado (sin documentación propia, sin
> `README`, sin tests) y se va a actualizar cada vez que el entendimiento del proyecto
> cambie — sobre todo a medida que se resuelvan los "TODO" y preguntas abiertas que dejó
> el desarrollador anterior. Cuando algo acá quede desactualizado por una decisión nueva,
> se edita esta sección, no se agrega un parche al final.

## 1. Qué es Corta

Acortador de URLs interno de la empresa. Node.js + Express. Un usuario pega una URL
larga, recibe un código corto, y visitar `/<codigo>` lo debería llevar al destino
original, contando el click.

**Storage (desde Milestone 5):** Postgres, vía la variable de entorno `DATABASE_URL`
(`db.js`), corriendo como servicio separado en Railway. Antes de Milestone 5 persistía
todo en un archivo `links.json` en disco — ver §8 para la migración y el motivo del
cambio. El server escucha en `process.env.PORT` (Railway lo inyecta en producción; local
cae a `3000`).

## 2. Inventario heredado — qué archivo es cuál

Estado al recibir la carpeta, sin git ni README (ver §8 para lo que cambió en Milestone 2):

| Archivo | Estado | Nota |
|---|---|---|
| `server.js` | **Activo.** Es el que arranca `npm start` (`main`/`scripts.start` en `package.json`). | Fuente de verdad del comportamiento actual. |
| `utils.js` | Activo. | Genera el código corto (`generarCodigo`). |
| ~~`index_v2_FINAL.js`~~ | Muerto. Versión intermedia de `server.js`: mismo endpoint pero sin validar `url`, sin guardar `creado`, y devuelve `{ codigo }` en vez de `{ codigo, corta }`. No estaba referenciado por `package.json`. | **Borrado en Milestone 2.** |
| ~~`server_OLD.js`~~ | Muerto. Comentario propio decía "VERSION VIEJA - no usar". Endpoint distinto (`/acortar`), sin manejo de 404 (crasheaba con `link.url` si `link` era `undefined`). | **Borrado en Milestone 2.** |
| ~~`test.js`~~ | Script manual (`node test.js` con el server levantado), no era una suite de tests automatizada. Probaba solo el happy path de crear+redirigir. | **Borrado en Milestone 2**, reemplazado por la batería TDD en `tests/`. |
| `links.json` | Fue la base de datos real hasta Milestone 5 (8 links con clicks acumulados). | **Migrado a Postgres y borrado en Milestone 5** — ver §8. Sus 8 registros viven ahora en la tabla `links`, sembrados por `scripts/seed-legacy-links.js`. |
| ~~`links_backup_marzo.json`~~ | Backup manual y desactualizado (clicks más bajos, solo 3 links) de marzo. No lo leía ningún código. | **Borrado en Milestone 2** — no aporta como referencia histórica, es ruido. |
| ~~`notas.txt`~~ | Notas sueltas del dev anterior. Incluía **una credencial de Postgres en texto plano** (decía que el server "YA NO EXISTE", pero la password quedó igual). | **Borrado en Milestone 2**, ver §7. Lo accionable (TODOs, decisiones) ya está en este SPEC. |
| `public/index.html` | Activo. Formulario de acortar. | — |
| `public/stats.html` | Maquetado, **no funcional**. Muestra datos hardcodeados (`123` clicks) y no llama a ningún endpoint. | Es el encargo de Milestone 4. |
| `public/estilos.css` | Activo, usado por `index.html` y `stats.html`. | — |
| ~~`public/estilos_viejos.css`~~ | No referenciado por ningún HTML. | **Borrado en Milestone 2.** |
| `public/logo.png` | Antes `logo (1).png` (nombre con espacio, sufijo típico de descarga duplicada). Usado por `index.html`. | **Renombrado en Milestone 2.** |
| `package.json` | `axios` solo se usaba en `test.js` (ya borrado). `moment` y `lodash` no se usaban en ningún archivo — confirmado por búsqueda en el código, coincide con la nota del dev anterior ("sacar moment... lodash tampoco me acuerdo para qué era"). | **Limpiado en Milestone 2**, queda solo `express`. |

## 3. Endpoints actuales

### 3.1 `POST /api/links` — crear un link corto

**Body esperado:** `{ "url": "<string>" }`

**Comportamiento actual (corregido en Milestone 3):**
- Si falta `url`, es `""` o es solo espacios en blanco (se hace `trim()`), responde
  `400 { error: 'Falta la url' }`.
- `url` se valida con el constructor nativo `URL` de Node, restringiendo `protocol` a
  `http:`/`https:`. Si no parsea o el esquema no es http(s) (`javascript:`, `data:`,
  `ftp:`, strings sin esquema como `"asdf"`), responde `400 { error: 'La url no es una
  URL http(s) válida' }` — mensaje distinto al de "falta la url" (ver §4.2).
- Genera un código de 3 caracteres (`[a-z0-9]{3}`, ver §3.3) y lo **verifica contra los
  códigos ya existentes en `links.json`**, regenerando en loop hasta encontrar uno libre
  (ver §4.1 — ya no puede haber colisión).
- Guarda `{ codigo, url, clicks: 0, creado: <ISO 8601 actual> }` al final del array y
  reescribe `links.json` completo. La lectura + escritura sigue siendo síncrona
  (`readFileSync`/`writeFileSync`) sin ningún `await` en el medio, lo cual —al ser Node
  single-threaded— evita que se intercalen dos requests a mitad de operación; ver §4.4.
- Responde `200 { codigo, corta: '/' + codigo }`.

### 3.2 `GET /:codigo` — redirigir al destino

**Comportamiento actual (corregido en Milestone 3):**
- Busca en `links.json` el primer link cuyo `codigo` matchee (`Array.find`; si hubiera
  datos heredados con códigos duplicados se queda con el más viejo, pero ya no puede
  generarse ningún duplicado nuevo desde §3.1).
- Si no existe: `404` con el texto `"No existe ese link"` (se mantuvo texto plano acá,
  ver §8 sobre formato de error).
- Si existe: incrementa `clicks` en 1, reescribe `links.json`, y responde con un
  redirect HTTP real `302 Location: <link.url>` (`res.redirect(302, link.url)`) — el
  navegador efectivamente "te lleva" al destino, cumpliendo el criterio de éxito del
  Milestone 3. Se eligió `302` sobre `301` para no cachear permanentemente un redirect
  cuyo código podría necesitar reasignarse o corregirse más adelante.
- Nota de alcance: el matching de Express (`/:codigo`) es de un solo segmento de path, así
  que no colisiona con `/api/links` (dos segmentos). Sí colisiona con cualquier archivo
  estático de `public/` si el código generado coincidiera con un nombre de archivo — poco
  probable con códigos de 3 caracteres alfanuméricos, pero queda como caso borde de baja
  prioridad.

### 3.3 Generación de código (`utils.js`)

- Alfabeto: `abcdefghijklmnopqrstuvwxyz0123456789` (36 caracteres), longitud fija 3.
- Espacio total: 36³ = 46.656 combinaciones posibles.
- **No usa `crypto`, usa `Math.random()`** — no es criptográficamente fuerte, pero para
  códigos cortos públicos no sensibles esto es aceptable; no se considera un bug de
  seguridad en este contexto (no protege nada secreto).
- Antes de Milestone 3, con links ya existentes y sin control de colisiones, la
  probabilidad de choque crecía con cada alta (§4.1). Ya no es posible: `POST /api/links`
  regenera hasta encontrar un código libre.

### 3.4 `GET /api/links/:codigo/stats`

Encargo explícito dejado en `notas.txt` y confirmado por `mission.md`. Se adelantó la
implementación del endpoint en Milestone 3 porque el propio criterio de éxito de ese
milestone (§6, "las estadísticas dicen la verdad") depende de poder consultar stats de
forma fiable — la parte de Milestone 4 que queda pendiente es sólo conectar
`public/stats.html` a este endpoint (ver abajo).

**Response actual (200, link existente):**
```json
{
  "codigo": "a3k",
  "url": "https://www.austral.edu.ar/ingenieria/",
  "clicks": 42,
  "creado": "2026-03-02T14:11:09.000Z"
}
```

**Casos borde:**
- Código inexistente → `404 { error: 'No existe ese link' }` (acá sí en JSON, a
  diferencia de `GET /:codigo` — ver §8 sobre por qué no se unificó el formato).
- El endpoint es de solo lectura: **consultarlo no incrementa `clicks`** (implementado
  como un `leerLinks()` sin escritura posterior). Solo cuenta como "click" un
  `GET /:codigo` que redirige de verdad (ver §6).

**Resuelto (Milestone 4):** `public/stats.html` consulta este endpoint desde el
`<form id="form-stats">` al enviarse, y muestra `clicks`, `url` y `creado` (con
`toLocaleString('es-AR', ...)`, no el ISO crudo). Un código inexistente (`404`) muestra
un mensaje de error en vez de números; cualquier otro fallo de red o del server muestra
un mensaje genérico.

## 4. Casos borde

### 4.1 Códigos repetidos

**Estado actual (reforzado en Milestone 5):** no puede ocurrir, en dos capas.

- **Milestone 3 (nivel aplicación):** `generarCodigoUnico()`/`crearLinkConCodigoUnico()`
  regenera con `generarCodigo()` hasta encontrar uno libre antes de persistir.
- **Milestone 5 (nivel base de datos):** `codigo` es `PRIMARY KEY` de la tabla `links`
  (`db.js`). `POST /api/links` inserta con `ON CONFLICT (codigo) DO NOTHING` y reintenta
  si no insertó nada — esto además cierra la ventana de carrera que el chequeo en JS solo
  (leer códigos en uso, después insertar) tendría bajo escrituras async concurrentes,
  algo que con el `links.json` síncrono no aplicaba (ver §4.4).

Con la constraint de la base, ya no es solo "poco probable" que existan dos filas con el
mismo `codigo`: es imposible insertarlas — verificado directamente en
`tests/duplicate-codes.test.js` (un `INSERT` duplicado explícito es rechazado por
Postgres). La respuesta a "¿qué pasa si dos URLs reciben el mismo código?" sigue siendo
**"no puede pasar, se resuelve en el momento de creación"**, ahora garantizado por la
base y no solo por la lógica de la app.

### 4.2 URLs inválidas

**Estado actual (resuelto en Milestone 3):**
- `url` ausente, vacía o solo espacios → `400 { error: 'Falta la url' }`.
- `url` no vacía pero no es una URL absoluta válida (falta esquema, esquema no-http(s),
  string no parseable) → `400 { error: 'La url no es una URL http(s) válida' }` — mensaje
  distinto al de "falta la url", para que el frontend pueda distinguir los dos casos.
- Implementado con el constructor nativo `URL` de Node, restringiendo `protocol` a
  `http:`/`https:`: rechaza `javascript:`, `data:`, `ftp:`, y cualquier string que no
  parsee como URL absoluta.

### 4.3 Links inexistentes

**Estado actual:** `GET /:codigo` con un código que no está en `links.json` devuelve
`404` con texto `"No existe ese link"`. No se cambió a JSON — ver §8, decisión de no
unificar el formato de error entre `GET /:codigo` (pensado para navegación directa del
browser) y el resto de la API.

### 4.4 Concurrencia / condiciones de carrera

**Estado hasta Milestone 4:** `leerLinks`/`guardarLinks` hacían lectura + escritura
completa y síncrona de `links.json` (`readFileSync`/`writeFileSync`), sin ningún lock
explícito. La atomicidad salía gratis porque Node es single-threaded y ninguno de los
handlers tenía un `await` entre leer y escribir: el event loop no podía intercalar otro
request a mitad de un `leerLinks() → modificar → guardarLinks()`.

**Estado actual (Milestone 5):** ese truco dejó de aplicar apenas los handlers pasaron a
ser `async` contra Postgres (`db.pool.query` sí cede el control del event loop mientras
espera la red). La atomicidad ahora la garantiza la base, no el single-thread de Node:

- `GET /:codigo` hace `UPDATE links SET clicks = clicks + 1 WHERE codigo = $1 RETURNING
  url` — lectura e incremento son una sola operación atómica de Postgres. N requests
  concurrentes al mismo código dan exactamente N incrementos, sin locks manuales,
  cubierto por el mismo test de 20 `GET` concurrentes (`tests/estadisticas-verdaderas.test.js`)
  que antes probaba el comportamiento del archivo.
- `POST /api/links` inserta con `INSERT ... ON CONFLICT (codigo) DO NOTHING RETURNING
  ...` y reintenta si no insertó nada — ver §4.1.

Este análisis vale mientras el storage sea esta tabla de Postgres. Si en el futuro se
introduce una capa de cache o un segundo proceso escribiendo por fuera de estas queries,
hay que revisar esta sección.

## 5. Contrato de datos (`links.json` / futura tabla)

Cada link es un registro con:

| Campo | Tipo | Descripción |
|---|---|---|
| `codigo` | string, 3 chars `[a-z0-9]` | Único. Identificador público en la URL corta. |
| `url` | string | Destino. Debe ser una URL absoluta `http(s)` válida (ver §4.2). |
| `clicks` | integer ≥ 0 | Contador de redirects exitosos. Nunca negativo, nunca decrece. |
| `creado` | string, ISO 8601 UTC | Timestamp de creación, seteado por el server, no por el cliente. |

## 6. Qué significa "las estadísticas dicen la verdad"

Este es el criterio de éxito explícito del Milestone 3, y **ya se cumple** — verificado
por `tests/estadisticas-verdaderas.test.js`, los 5 tests en verde. Definición operativa
que el test verifica:

1. **Un click contado = un redirect exitoso.** Solo `GET /:codigo` sobre un código
   existente incrementa `clicks`, y lo incrementa en exactamente 1. Un código inexistente
   no incrementa nada (ya es así).
2. **Consultar stats no altera stats.** `GET /api/links/:codigo/stats` es de solo lectura;
   llamarlo 100 veces seguidas no debe mover el contador.
3. **No se pierden ni se duplican increments bajo concurrencia razonable.** N requests
   simultáneos a `GET /:codigo` deben resultar en `clicks` incrementado exactamente en N
   (dentro de lo que la infraestructura elegida pueda garantizar — con `links.json` esto
   requiere serializar escrituras; con una base de datos, un `UPDATE` atómico lo resuelve
   gratis).
4. **Los números que devuelve `/stats` son los mismos que hay persistidos**, sin caché
   intermedio que pueda desincronizarse.
5. **Pendiente de decisión de equipo:** ¿un mismo usuario recargando la misma URL corta
   varias veces cuenta como varios clicks? Hoy sí (no hay deduplicación por IP/sesión/tiempo).
   Se documenta como decisión consciente, no como bug, salvo que el equipo decida lo
   contrario — en cuyo caso esta sección se actualiza.

## 7. Seguridad — hallazgo durante la lectura del código heredado

`notas.txt` contiene una credencial de base de datos en texto plano
(`postgres://corta:S3cr3taDeLaOficina2023@10.0.4.17:5432/corta`). El archivo dice que ese
server "ya no existe", pero:
- No hay forma de confirmar eso con certeza solo leyendo una nota.
- Aunque el server esté muerto, la contraseña pudo reutilizarse en otro lado.
- El archivo **no debe pushearse a un repo remoto** tal cual, ni siquiera en el primer
  commit "tal cual está" del Milestone 1 — este es exactamente el matiz que el enunciado
  de la misión pide poder defender. Decisión: extraer la credencial antes del primer
  commit (o si se decide preservar la nota histórica, redactar/reemplazar el secreto),
  y dejar constancia acá de la decisión tomada.

## 8. Preguntas abiertas / decisiones pendientes

- **Resuelto (Milestone 2):** `links_backup_marzo.json`, `index_v2_FINAL.js`,
  `server_OLD.js`, `test.js`, `public/estilos_viejos.css` y `notas.txt` se borraron por
  ser código muerto, duplicados o (en el caso de `notas.txt`) un riesgo de seguridad —
  ver README.md § "Qué se sacó al ordenar el repo". `public/logo (1).png` se renombró a
  `public/logo.png`. `package.json` quedó solo con `express` como dependencia.
- **Resuelto (Milestone 3):** `url` se valida con el constructor nativo `URL` (esquema
  `http:`/`https:` obligatorio); los códigos se generan únicos contra `links.json`
  regenerando en loop; `GET /:codigo` redirige de verdad con `302`; se implementó
  `GET /api/links/:codigo/stats` de solo lectura (adelantado desde Milestone 4 porque
  este mismo milestone depende de poder consultar stats de forma fiable, ver §3.4).
- **Resuelto (Milestone 3):** formato de error NO se unificó. `POST /api/links` y
  `GET /api/links/:codigo/stats` devuelven JSON `{ error }` (son endpoints de API
  pensados para ser consumidos por código). `GET /:codigo` sigue devolviendo texto plano
  en el 404 porque es la ruta que un browser visita directamente al pegar el link corto
  — un usuario ahí nunca ve JSON crudo de otra forma tampoco. Se documenta como decisión
  consciente; si en Milestone 4/5 aparece un cliente programático que necesite parsear
  ese 404, se revisita.
- **Resuelto (Milestone 3):** `302` para el redirect de `GET /:codigo`, por la
  flexibilidad de no cachear permanentemente un código que podría reasignarse.
- ¿Deduplicación de clicks por usuario/tiempo? Por ahora, no (§6, punto 5).
- **Resuelto (Milestone 5):** motor elegido: **PostgreSQL**, corriendo como servicio
  separado en Railway (imagen `ghcr.io/railwayapp-templates/postgres-ssl:latest`,
  creada vía el MCP de Railway). `server.js` crea el schema si no existe al arrancar
  (`db.initSchema()` en `db.js`) — no hace falta correr una migración a mano para el
  schema en un ambiente nuevo.
- **Resuelto (Milestone 5):** los 8 links que vivían en `links.json` se migraron una
  sola vez a la tabla `links` con `scripts/seed-legacy-links.js` (idempotente,
  `ON CONFLICT DO NOTHING`), preservando `clicks` y `creado` originales. Después de
  correrlo, `links.json` se borró del repo — ya no lo lee nadie y dejarlo hubiera sido
  el mismo tipo de archivo muerto que Milestone 2 se encargó de sacar.
- **Pendiente (deuda técnica, ver §9):** el servicio de Postgres en Railway no tiene un
  volumen persistente adjunto todavía — se decidió avanzar sin él y agregarlo después
  (la herramienta de MCP disponible no expone creación de volúmenes; es un paso manual
  en el dashboard). Sin volumen, los datos sobreviven a un redeploy/restart de la **app**
  (que es el criterio de éxito de este milestone), pero se perderían si el **servicio de
  Postgres** se reinicia o redeploya.

## 9. Despliegue en Railway (Milestone 5)

- **Proyecto:** `corta`, dos servicios en el ambiente `production`: la app Node
  (`corta`, deployada desde este repo de GitHub) y `Postgres` (imagen Docker, no el
  template gestionado del marketplace — ver más abajo por qué).
- **Networking interno:** la app se conecta a Postgres por la red privada de Railway
  (`postgres.railway.internal`), no por una URL pública. `DATABASE_URL` en el servicio
  de la app queda seteado como variable de entorno en Railway, nunca en el código ni en
  un archivo commiteado (`.env` está en `.gitignore`; `.env.example` documenta la forma
  sin valores reales).
- **Por qué Docker image y no el template "Add PostgreSQL" del marketplace:** el
  template gestionado (el que aparece en el dashboard vía `+ New → Database`) provisiona
  automáticamente usuario/password/db y el volumen persistente, pero esa lógica vive en
  la configuración del template, no en la imagen en sí — el MCP de Railway disponible
  para esta misión no tiene una herramienta que dispare ese flujo, solo `create-service`
  con una imagen Docker cruda. Se replicó el resultado a mano: se creó el servicio con
  la misma imagen que usa el template (`postgres-ssl`) y se setearon
  `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`/`DATABASE_URL` por variables de
  entorno. Lo que **no** se pudo replicar por MCP fue el volumen — ver la deuda técnica
  en §8.
- **Riesgo conocido — tests contra la base de producción:** `tests/helpers/testServer.js`
  cae a `DATABASE_URL` si no hay un `TEST_DATABASE_URL` separado seteado, y cada suite
  hace `DELETE FROM links` en su `beforeEach`. Hoy (un solo ambiente de Railway, sin
  staging) eso significa que correr `npm test` apuntando al `.env` de producción borra
  los links reales. Mitigación mínima aplicada: el helper soporta `TEST_DATABASE_URL`
  para apuntar a una base distinta; queda como buena práctica pendiente crear esa
  segunda base si el proyecto sigue creciendo.
- **Acceso externo para desarrollo/tests locales:** para correr `npm test` y el script
  de migración desde una máquina fuera de Railway hace falta Public Networking (TCP
  Proxy) en el servicio de Postgres — igual que el volumen, esto se habilita a mano
  desde el dashboard (Settings → Networking → Public Networking del servicio Postgres;
  el MCP no expone esta acción). Una vez habilitado, Railway completa solo
  `DATABASE_PUBLIC_URL`; esa URL solo se usa localmente, nunca la lee la app en
  producción (que usa la interna).
