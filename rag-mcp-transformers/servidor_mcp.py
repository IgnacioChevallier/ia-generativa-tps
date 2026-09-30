"""Servidor MCP de la parte 3: expone las seis herramientas de hospital.py por stdio.

python3 servidor_mcp.py

Sin LangChain, con FastMCP del SDK oficial `mcp` (1.x). Cada herramienta se registra
aplicando `mcp.tool()` a las funciones de hospital.py (equivalente a decorarlas ahí mismo
con `@mcp.tool()`, sin repetir sus firmas): así el servidor queda sin código propio para
consultar la API ni el recuperador, y hospital.py sigue siendo el único lugar donde viven
las herramientas.

Para inspeccionarlo con cualquier cliente MCP, sin ningún LLM:
npx @modelcontextprotocol/inspector python3 servidor_mcp.py
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")  # bge-m3 ya está cacheado: sin esto, cargarlo
# se cuelga esperando un chequeo de actualización contra HuggingFace Hub que acá no responde.

from mcp.server.fastmcp import FastMCP

import recuperar  # precarga en el hilo principal (ver _precargar_encoder más abajo)
from hospital import HERRAMIENTAS

mcp = FastMCP("hospital")

for _herramienta in HERRAMIENTAS:
    mcp.tool()(_herramienta)


def _precargar_encoder():
    """FastMCP llama a las herramientas desde un hilo del executor, no el principal. torch
    se cuelga en Windows si el primer import de un módulo pesado (con DLLs de C) pasa por un
    hilo secundario (loader lock de Windows). Importar y cargar el encoder acá, en el hilo
    principal y antes de `mcp.run()`, evita que la primera llamada a buscar_documentos
    dispare esa carga desde el hilo equivocado."""
    recuperar.buscar("precarga")


if __name__ == "__main__":
    _precargar_encoder()
    mcp.run()
