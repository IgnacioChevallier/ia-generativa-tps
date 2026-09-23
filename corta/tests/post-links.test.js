// Deriva de SPEC.md §3.1 (POST /api/links) y §4.2 (URLs inválidas), §3.3 (generación de
// código) y §5 (contrato de datos).
'use strict';

const { test, describe, before, after, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const { BASE_URL, iniciarServer, detenerServer, seedLinks, leerLinksActuales } = require('./helpers/testServer');

describe('POST /api/links', () => {
  before(iniciarServer);
  after(detenerServer);
  beforeEach(() => seedLinks([]));

  test('400 si falta la url', async () => {
    const res = await fetch(BASE_URL + '/api/links', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    assert.equal(res.status, 400);
    const body = await res.json();
    assert.ok(body.error, 'debe informar un error');
  });

  test('400 si la url es un string vacío', async () => {
    const res = await fetch(BASE_URL + '/api/links', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: '' }),
    });
    assert.equal(res.status, 400);
  });

  test('400 si la url es solo espacios en blanco', async () => {
    const res = await fetch(BASE_URL + '/api/links', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: '    ' }),
    });
    assert.equal(res.status, 400);
  });

  test('400 si la url no tiene esquema (no es una URL absoluta)', async () => {
    const res = await fetch(BASE_URL + '/api/links', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'no-es-una-url' }),
    });
    assert.equal(res.status, 400);
  });

  test('400 si la url usa un esquema que no es http/https', async () => {
    for (const url of ['javascript:alert(1)', 'ftp://ejemplo.com/archivo', 'data:text/plain,hola']) {
      const res = await fetch(BASE_URL + '/api/links', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      assert.equal(res.status, 400, `esperaba 400 para "${url}"`);
    }
  });

  test('200 y forma correcta de respuesta para una url http(s) válida', async () => {
    const res = await fetch(BASE_URL + '/api/links', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://www.ejemplo.com/pagina' }),
    });
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(typeof body.codigo, 'string');
    assert.equal(body.corta, '/' + body.codigo);
  });

  test('el código generado tiene 3 caracteres [a-z0-9]', async () => {
    const res = await fetch(BASE_URL + '/api/links', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://www.ejemplo.com/pagina' }),
    });
    const { codigo } = await res.json();
    assert.match(codigo, /^[a-z0-9]{3}$/);
  });

  test('el link persistido arranca en clicks: 0 y con creado en ISO 8601 seteado por el server', async () => {
    const antes = new Date();
    const res = await fetch(BASE_URL + '/api/links', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://www.ejemplo.com/pagina' }),
    });
    const { codigo } = await res.json();
    const links = await leerLinksActuales();
    const link = links.find((l) => l.codigo === codigo);
    assert.ok(link, 'el link debe quedar persistido');
    assert.equal(link.clicks, 0);
    assert.equal(link.url, 'https://www.ejemplo.com/pagina');
    const creado = new Date(link.creado);
    assert.ok(!Number.isNaN(creado.getTime()), 'creado debe ser una fecha ISO válida');
    assert.ok(creado.getTime() >= antes.getTime() - 1000, 'creado debe ser reciente, seteado por el server');
  });

  test('un campo "creado" enviado por el cliente se ignora (lo setea el server)', async () => {
    const res = await fetch(BASE_URL + '/api/links', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://www.ejemplo.com/pagina', creado: '1999-01-01T00:00:00.000Z' }),
    });
    const { codigo } = await res.json();
    const link = (await leerLinksActuales()).find((l) => l.codigo === codigo);
    assert.notEqual(link.creado, '1999-01-01T00:00:00.000Z');
  });

  test('crear muchos links seguidos nunca produce códigos repetidos (SPEC §4.1)', async () => {
    const cantidad = 150;
    for (let i = 0; i < cantidad; i++) {
      const res = await fetch(BASE_URL + '/api/links', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: `https://www.ejemplo.com/pagina-${i}` }),
      });
      assert.equal(res.status, 200);
    }
    const links = await leerLinksActuales();
    const codigos = links.map((l) => l.codigo);
    const codigosUnicos = new Set(codigos);
    assert.equal(
      codigosUnicos.size,
      codigos.length,
      'no debería haber dos links con el mismo código'
    );
  });
});
