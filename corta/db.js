'use strict';

const { Pool } = require('pg');

// La imagen postgres-ssl de Railway exige TLS incluso para conexiones dentro de la red
// privada; el certificado es autofirmado (no hay CA pública detrás), por eso
// rejectUnauthorized: false en vez de validar contra una CA.
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

async function initSchema() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS links (
      codigo TEXT PRIMARY KEY,
      url TEXT NOT NULL,
      clicks INTEGER NOT NULL DEFAULT 0,
      creado TIMESTAMPTZ NOT NULL DEFAULT now()
    )
  `);
}

module.exports = { pool, initSchema };
