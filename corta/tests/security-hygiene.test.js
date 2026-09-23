// Deriva de SPEC.md §7 (higiene/seguridad) y §2 (código muerto que no debería estar
// enganchado). Regresión: si en algún refactor futuro alguien sirve la raíz del proyecto
// como estática, esto debería fallar y avisar.
'use strict';

const { test, describe, before, after, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const { BASE_URL, iniciarServer, detenerServer, seedLinks } = require('./helpers/testServer');

describe('Higiene y seguridad', () => {
  before(iniciarServer);
  after(detenerServer);
  beforeEach(() => seedLinks([]));

  test('notas.txt (con la credencial vieja) no se sirve por HTTP', async () => {
    const res = await fetch(BASE_URL + '/notas.txt', { redirect: 'manual' });
    assert.notEqual(res.status, 200);
  });

  test('links.json (la base de datos) no se sirve como archivo estático', async () => {
    const res = await fetch(BASE_URL + '/links.json', { redirect: 'manual' });
    if (res.status === 200) {
      const texto = await res.text();
      assert.doesNotMatch(texto, /"codigo"\s*:/, 'no debería devolver el contenido crudo de la base de datos');
    } else {
      assert.notEqual(res.status, 200);
    }
  });

  test('el endpoint viejo /acortar (de server_OLD.js) no está enganchado en el server activo', async () => {
    const res = await fetch(BASE_URL + '/acortar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://www.ejemplo.com' }),
      redirect: 'manual',
    });
    assert.notEqual(res.status, 200);
  });
});
