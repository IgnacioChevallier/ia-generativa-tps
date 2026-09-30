"""Tests del servidor MCP (parte 3) contra la API real, levantada en un puerto libre.

Usa el SDK oficial `mcp` como cliente (stdio), igual que haría cualquier cliente MCP —
no pasa por agente_mcp.py ni por LangChain."""
import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

RAIZ = Path(__file__).resolve().parent.parent
PUERTO = 8792

NOMBRES_ESPERADOS = ["buscar_documentos", "consultar_camas", "consultar_guardia",
                     "consultar_turnos", "consultar_farmacia", "consultar_espera"]


@pytest.fixture(scope="module", autouse=True)
def api():
    proc = subprocess.Popen([sys.executable, str(RAIZ / "api" / "servidor.py"), "--puerto", str(PUERTO)],
                            stdout=subprocess.DEVNULL)
    url = f"http://localhost:{PUERTO}"
    for _ in range(50):
        try:
            urllib.request.urlopen(f"{url}/espera", timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    yield url
    proc.terminate()


def _correr(coro):
    return asyncio.run(coro)


async def _con_sesion(api_url, hacer):
    params = StdioServerParameters(
        command=sys.executable, args=[str(RAIZ / "servidor_mcp.py")], cwd=str(RAIZ),
        env={**os.environ, "HOSPITAL_API_URL": api_url},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await hacer(session)


def test_expone_las_seis_herramientas_con_docstrings(api):
    async def hacer(session):
        return await session.list_tools()
    resultado = _correr(_con_sesion(api, hacer))
    nombres = [t.name for t in resultado.tools]
    assert nombres == NOMBRES_ESPERADOS
    assert all(t.description and len(t.description) > 80 for t in resultado.tools)


def test_consultar_camas_devuelve_libres(api):
    async def hacer(session):
        return await session.call_tool("consultar_camas", {"sector": "pediatria"})
    resultado = _correr(_con_sesion(api, hacer))
    texto = resultado.content[0].text
    assert json.loads(texto)["datos"]["libres"] == 7


def test_consultar_espera_sin_argumentos(api):
    async def hacer(session):
        return await session.call_tool("consultar_espera", {})
    resultado = _correr(_con_sesion(api, hacer))
    assert json.loads(resultado.content[0].text)["minutos_por_nivel"]["verde"] == 135


def test_sector_inexistente_devuelve_opciones(api):
    async def hacer(session):
        return await session.call_tool("consultar_camas", {"sector": "marte"})
    resultado = _correr(_con_sesion(api, hacer))
    d = json.loads(resultado.content[0].text)
    assert "error" in d and "pediatria" in d["opciones"]
