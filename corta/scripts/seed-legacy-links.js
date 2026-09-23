// Migración de una sola vez: carga los links heredados de links.json (el "archivo de
// producción" de antes de Milestone 5) en la tabla `links` de Postgres. Idempotente:
// usa ON CONFLICT DO NOTHING, así correrlo dos veces no duplica ni pisa clicks reales.
'use strict';

const fs = require('fs');
const path = require('path');
require('dotenv/config');
const db = require('../db');

async function main() {
  const links = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'links.json'), 'utf8'));

  await db.initSchema();

  let insertados = 0;
  for (const link of links) {
    const { rowCount } = await db.pool.query(
      `INSERT INTO links (codigo, url, clicks, creado) VALUES ($1, $2, $3, $4)
       ON CONFLICT (codigo) DO NOTHING`,
      [link.codigo, link.url, link.clicks, link.creado]
    );
    insertados += rowCount;
  }

  console.log(`Migración terminada: ${insertados} de ${links.length} links insertados (los demás ya existían).`);
  await db.pool.end();
}

main().catch((err) => {
  console.error('Falló la migración:', err);
  process.exit(1);
});
