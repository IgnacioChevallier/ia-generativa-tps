require('dotenv/config');
const express = require('express');
const { generarCodigo } = require('./utils');
const db = require('./db');

const app = express();
app.use(express.json());
app.use(express.static('public'));

const PORT = process.env.PORT || 3000;

function esUrlValida(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

// Inserta con un código nuevo hasta que uno no choque contra la PRIMARY KEY (codigo).
// La unicidad la garantiza la constraint de la tabla, no un chequeo previo en JS: bajo
// escrituras async concurrentes, "leer códigos en uso y después insertar" tiene una
// ventana de carrera que "insertar y reintentar si choca" no tiene.
async function crearLinkConCodigoUnico(url) {
  for (let intento = 0; intento < 10; intento++) {
    const codigo = generarCodigo();
    const { rows } = await db.pool.query(
      `INSERT INTO links (codigo, url) VALUES ($1, $2)
       ON CONFLICT (codigo) DO NOTHING
       RETURNING codigo, url, clicks, creado`,
      [codigo, url]
    );
    if (rows.length > 0) return rows[0];
  }
  throw new Error('No se pudo generar un código único después de varios intentos');
}

// crear un link corto
app.post('/api/links', async (req, res) => {
  const url = typeof req.body.url === 'string' ? req.body.url.trim() : '';
  if (!url) {
    return res.status(400).json({ error: 'Falta la url' });
  }
  if (!esUrlValida(url)) {
    return res.status(400).json({ error: 'La url no es una URL http(s) válida' });
  }
  try {
    const link = await crearLinkConCodigoUnico(url);
    res.json({ codigo: link.codigo, corta: '/' + link.codigo });
  } catch (err) {
    console.error('Error creando link:', err);
    res.status(500).json({ error: 'No se pudo crear el link' });
  }
});

// estadísticas de un link (solo lectura)
app.get('/api/links/:codigo/stats', async (req, res) => {
  try {
    const { rows } = await db.pool.query(
      'SELECT codigo, url, clicks, creado FROM links WHERE codigo = $1',
      [req.params.codigo]
    );
    if (rows.length === 0) {
      return res.status(404).json({ error: 'No existe ese link' });
    }
    const link = rows[0];
    res.json({ codigo: link.codigo, url: link.url, clicks: link.clicks, creado: link.creado.toISOString() });
  } catch (err) {
    console.error('Error leyendo stats:', err);
    res.status(500).json({ error: 'No se pudieron leer las estadísticas' });
  }
});

// redirigir al destino
app.get('/:codigo', async (req, res) => {
  try {
    // UPDATE ... RETURNING hace la lectura + el incremento en una sola operación atómica
    // de la base: N requests concurrentes al mismo código nunca pisan un incremento entre sí
    // (ver SPEC.md §4.4 — reemplaza el argumento de "Node es single-threaded" de cuando
    // esto vivía en links.json).
    const { rows } = await db.pool.query(
      'UPDATE links SET clicks = clicks + 1 WHERE codigo = $1 RETURNING url',
      [req.params.codigo]
    );
    if (rows.length === 0) {
      return res.status(404).send('No existe ese link');
    }
    res.redirect(302, rows[0].url);
  } catch (err) {
    console.error('Error redirigiendo:', err);
    res.status(500).send('Error interno');
  }
});

async function main() {
  await db.initSchema();
  app.listen(PORT, function () {
    console.log('Corta escuchando en el puerto ' + PORT);
  });
}

main().catch((err) => {
  console.error('No se pudo iniciar Corta:', err);
  process.exit(1);
});
