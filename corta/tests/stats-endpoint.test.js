// Deriva de SPEC.md §3.4 — GET /api/links/:codigo/stats (Milestone 4, todavía no existe
// en el código heredado). Toda esta suite arranca en rojo hasta que se implemente.
'use strict';

const { test, describe, before, after, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const { BASE_URL, iniciarServer, detenerServer, seedLinks, leerLinksActuales } = require('./helpers/testServer');

describe('GET /api/links/:codigo/stats', () => {
  before(iniciarServer);
  after(detenerServer);

  beforeEach(async () => {
    await seedLinks([
      { codigo: 'a3k', url: 'https://www.ejemplo.com/algo', clicks: 42, creado: '2026-03-02T14:11:09.000Z' },
    ]);
  });

  test('200 con los datos reales de un código existente', async () => {
    const res = await fetch(BASE_URL + '/api/links/a3k/stats');
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.codigo, 'a3k');
    assert.equal(body.url, 'https://www.ejemplo.com/algo');
    assert.equal(body.clicks, 42);
    assert.equal(body.creado, '2026-03-02T14:11:09.000Z');
  });

  test('404 con un código inexistente', async () => {
    const res = await fetch(BASE_URL + '/api/links/nop/stats');
    assert.equal(res.status, 404);
  });

  test('consultar las stats es de solo lectura: no incrementa clicks', async () => {
    for (let i = 0; i < 10; i++) {
      await fetch(BASE_URL + '/api/links/a3k/stats');
    }
    const link = (await leerLinksActuales()).find((l) => l.codigo === 'a3k');
    assert.equal(link.clicks, 42, 'clicks no debe moverse por consultar /stats');
  });

  test('los números devueltos coinciden con lo persistido en disco', async () => {
    await seedLinks([
      { codigo: 'xyz', url: 'https://www.ejemplo.com/otra', clicks: 7, creado: '2026-05-01T10:00:00.000Z' },
    ]);
    const res = await fetch(BASE_URL + '/api/links/xyz/stats');
    const body = await res.json();
    const persistido = (await leerLinksActuales()).find((l) => l.codigo === 'xyz');
    assert.equal(body.clicks, persistido.clicks);
    assert.equal(body.url, persistido.url);
    assert.equal(body.creado, persistido.creado);
  });
});
