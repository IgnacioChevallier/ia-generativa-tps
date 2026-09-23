// Arranca/para el server.js real como subproceso y siembra/lee el estado directamente en
// Postgres (antes escribía links.json a mano). Caja negra igual que antes: no requiere que
// server.js exporte nada, solo que respete DATABASE_URL y PORT por variables de entorno.
'use strict';

const { spawn } = require('node:child_process');
const path = require('node:path');
require('dotenv/config');
const { Pool } = require('pg');

const ROOT = path.join(__dirname, '..', '..');
const BASE_URL = 'http://localhost:3000';

const TEST_DATABASE_URL = process.env.TEST_DATABASE_URL || process.env.DATABASE_URL;
if (!TEST_DATABASE_URL) {
  throw new Error(
    'Falta TEST_DATABASE_URL (o DATABASE_URL) en el entorno. Los tests necesitan una ' +
    'Postgres real para correr — ver README.md.'
  );
}

// Ver la nota de ssl: en db.js — la imagen postgres-ssl de Railway exige TLS.
const pool = new Pool({ connectionString: TEST_DATABASE_URL, ssl: { rejectUnauthorized: false } });

let proceso = null;

async function esperarListo(intentos = 50) {
  for (let i = 0; i < intentos; i++) {
    try {
      await fetch(BASE_URL + '/__healthcheck_no_deberia_existir__');
      return;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  }
  throw new Error(
    'El server no respondió en ' + BASE_URL + ' a tiempo. ' +
    '¿Hay otro proceso ocupando el puerto 3000?'
  );
}

async function iniciarServer() {
  await pool.query(
    'CREATE TABLE IF NOT EXISTS links (' +
    'codigo TEXT PRIMARY KEY, ' +
    'url TEXT NOT NULL, ' +
    'clicks INTEGER NOT NULL DEFAULT 0, ' +
    'creado TIMESTAMPTZ NOT NULL DEFAULT now()' +
    ')'
  );

  proceso = spawn('node', ['server.js'], {
    cwd: ROOT,
    stdio: ['ignore', 'ignore', 'pipe'],
    env: { ...process.env, DATABASE_URL: TEST_DATABASE_URL, PORT: '3000' },
  });

  let stderr = '';
  proceso.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
  proceso.on('exit', (code) => {
    if (code !== null && code !== 0 && stderr) {
      console.error('server.js terminó con error:\n' + stderr);
    }
  });

  await esperarListo();
}

function detenerServer() {
  if (proceso) {
    proceso.kill();
    proceso = null;
  }
}

// Reemplaza todo el contenido de la tabla por `links`. Como server.js consulta la base
// en cada request (sin cache), alcanza para fijar un estado conocido por test sin
// reiniciar el proceso.
async function seedLinks(links) {
  await pool.query('DELETE FROM links');
  for (const link of links) {
    await pool.query(
      'INSERT INTO links (codigo, url, clicks, creado) VALUES ($1, $2, $3, $4)',
      [link.codigo, link.url, link.clicks, link.creado]
    );
  }
}

async function leerLinksActuales() {
  const { rows } = await pool.query('SELECT codigo, url, clicks, creado FROM links ORDER BY creado');
  return rows.map((row) => ({ ...row, creado: row.creado.toISOString() }));
}

module.exports = { BASE_URL, iniciarServer, detenerServer, seedLinks, leerLinksActuales, pool };
