// Deriva de SPEC.md §4.1 — "¿qué pasa si dos URLs reciben el mismo código corto?".
// La respuesta esperada es "no puede pasar" (prevención en la creación).
//
// Antes de Milestone 5 (storage en links.json) esta suite también cubría la resiliencia
// ante datos heredados que ya tuvieran códigos duplicados en el archivo. Desde la
// migración a Postgres, `codigo` es PRIMARY KEY de la tabla `links` (ver db.js): un
// duplicado ya no es "poco probable", es imposible de insertar — la propia base lo
// rechaza. Por eso esos dos casos se reemplazan acá por un test que verifica esa
// constraint directamente, en vez de simular datos heredados que ya no pueden existir.
'use strict';

const { test, describe, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { BASE_URL, iniciarServer, detenerServer, seedLinks, pool } = require('./helpers/testServer');

describe('Códigos repetidos', () => {
  before(iniciarServer);
  after(detenerServer);

  test('POST /api/links nunca asigna un código que ya está en uso', async () => {
    await seedLinks([
      { codigo: 'zzz', url: 'https://www.ejemplo.com/ya-existe', clicks: 0, creado: '2026-01-01T00:00:00.000Z' },
    ]);

    const codigosNuevos = [];
    for (let i = 0; i < 30; i++) {
      const res = await fetch(BASE_URL + '/api/links', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: `https://www.ejemplo.com/nueva-${i}` }),
      });
      const { codigo } = await res.json();
      codigosNuevos.push(codigo);
    }

    assert.ok(!codigosNuevos.includes('zzz'), 'no debería reasignar un código ya ocupado');
  });

  test('la tabla `links` rechaza a nivel de base un codigo duplicado (PRIMARY KEY)', async () => {
    await seedLinks([
      { codigo: 'dup', url: 'https://www.ejemplo.com/version-vieja', clicks: 3, creado: '2026-01-01T00:00:00.000Z' },
    ]);

    await assert.rejects(
      pool.query(
        'INSERT INTO links (codigo, url, clicks, creado) VALUES ($1, $2, $3, $4)',
        ['dup', 'https://www.ejemplo.com/version-nueva', 0, '2026-02-01T00:00:00.000Z']
      ),
      /duplicate key value violates unique constraint/,
      'la constraint de la tabla debería impedir un segundo registro con el mismo codigo'
    );
  });
});
