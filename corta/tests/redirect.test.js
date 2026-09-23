// Deriva de SPEC.md §3.2 (GET /:codigo) y del criterio de éxito del Milestone 3:
// "el link corto te lleva a destino".
'use strict';

const { test, describe, before, after, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const { BASE_URL, iniciarServer, detenerServer, seedLinks, leerLinksActuales } = require('./helpers/testServer');

describe('GET /:codigo', () => {
  before(iniciarServer);
  after(detenerServer);

  beforeEach(async () => {
    await seedLinks([
      { codigo: 'aaa', url: 'https://www.ejemplo.com/destino-1', clicks: 0, creado: '2026-01-01T00:00:00.000Z' },
      { codigo: 'bbb', url: 'https://www.ejemplo.com/destino-2', clicks: 5, creado: '2026-01-02T00:00:00.000Z' },
    ]);
  });

  test('404 con un código que no existe', async () => {
    const res = await fetch(BASE_URL + '/zzz', { redirect: 'manual' });
    assert.equal(res.status, 404);
  });

  test('un código existente redirige de verdad (302) al destino, no devuelve la url como texto', async () => {
    const res = await fetch(BASE_URL + '/aaa', { redirect: 'manual' });
    assert.ok(res.status >= 300 && res.status < 400, `esperaba un redirect, vino ${res.status}`);
    assert.equal(res.headers.get('location'), 'https://www.ejemplo.com/destino-1');
  });

  test('un GET exitoso incrementa clicks en exactamente 1', async () => {
    await fetch(BASE_URL + '/aaa', { redirect: 'manual' });
    const link = (await leerLinksActuales()).find((l) => l.codigo === 'aaa');
    assert.equal(link.clicks, 1);
  });

  test('varios GET seguidos incrementan clicks uno por uno', async () => {
    for (let i = 0; i < 4; i++) {
      await fetch(BASE_URL + '/bbb', { redirect: 'manual' });
    }
    const link = (await leerLinksActuales()).find((l) => l.codigo === 'bbb');
    assert.equal(link.clicks, 5 + 4);
  });

  test('un código inexistente no incrementa clicks de ningún link existente', async () => {
    await fetch(BASE_URL + '/zzz', { redirect: 'manual' });
    const links = await leerLinksActuales();
    assert.equal(links.find((l) => l.codigo === 'aaa').clicks, 0);
    assert.equal(links.find((l) => l.codigo === 'bbb').clicks, 5);
  });
});
