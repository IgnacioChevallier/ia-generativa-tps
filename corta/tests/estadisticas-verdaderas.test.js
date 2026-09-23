// Deriva de SPEC.md §6 — "qué cuenta como las estadísticas dicen la verdad", puntos 1 a 4.
// El test de concurrencia (punto 3) expone el problema de lecturas/escrituras no atómicas
// de links.json descripto en SPEC.md §4.4: se espera que arranque en rojo.
'use strict';

const { test, describe, before, after, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const { BASE_URL, iniciarServer, detenerServer, seedLinks, leerLinksActuales } = require('./helpers/testServer');

describe('Las estadísticas dicen la verdad', () => {
  before(iniciarServer);
  after(detenerServer);

  beforeEach(async () => {
    await seedLinks([
      { codigo: 'ver', url: 'https://www.ejemplo.com/verdad', clicks: 0, creado: '2026-01-01T00:00:00.000Z' },
    ]);
  });

  test('un click contado = un redirect exitoso: N GET secuenciales -> clicks == N', async () => {
    const n = 8;
    for (let i = 0; i < n; i++) {
      await fetch(BASE_URL + '/ver', { redirect: 'manual' });
    }
    const res = await fetch(BASE_URL + '/api/links/ver/stats');
    const { clicks } = await res.json();
    assert.equal(clicks, n);
  });

  test('un código inexistente jamás suma un click', async () => {
    for (let i = 0; i < 5; i++) {
      await fetch(BASE_URL + '/no-existe', { redirect: 'manual' });
    }
    const res = await fetch(BASE_URL + '/api/links/ver/stats');
    const { clicks } = await res.json();
    assert.equal(clicks, 0);
  });

  test('consultar /stats repetidas veces no altera el contador', async () => {
    await fetch(BASE_URL + '/ver', { redirect: 'manual' });
    for (let i = 0; i < 20; i++) {
      await fetch(BASE_URL + '/api/links/ver/stats');
    }
    const res = await fetch(BASE_URL + '/api/links/ver/stats');
    const { clicks } = await res.json();
    assert.equal(clicks, 1);
  });

  test('N GET concurrentes al mismo código resultan en clicks incrementado en exactamente N (sin pérdidas por condición de carrera)', async () => {
    const n = 20;
    await Promise.all(
      Array.from({ length: n }, () => fetch(BASE_URL + '/ver', { redirect: 'manual' }))
    );
    const res = await fetch(BASE_URL + '/api/links/ver/stats');
    const { clicks } = await res.json();
    assert.equal(clicks, n, 'no debería haberse perdido ningún click por escrituras concurrentes');
  });

  test('los números de /stats son siempre los mismos que hay persistidos en disco', async () => {
    await fetch(BASE_URL + '/ver', { redirect: 'manual' });
    await fetch(BASE_URL + '/ver', { redirect: 'manual' });
    const res = await fetch(BASE_URL + '/api/links/ver/stats');
    const { clicks } = await res.json();
    const persistido = (await leerLinksActuales()).find((l) => l.codigo === 'ver');
    assert.equal(clicks, persistido.clicks);
  });
});
