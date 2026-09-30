"""Agente de la parte 3: igual que agente.py, pero las herramientas no están en este
archivo — las descubre en `servidor_mcp.py` por MCP (`tools/list`) y las llama por MCP
(`tools/call`), con `langchain-mcp-adapters`. Ningún código propio para la API ni el
recuperador: eso vive solo en el servidor.

python3 agente_mcp.py --preguntas datos/preguntas_agente_dev.jsonl --salida respuestas_mcp.jsonl

Requiere OPENROUTER_API_KEY (en el entorno o en `.env`) y la API levantada
(`python3 api/servidor.py`). Por cada corrida escribe un log `.md` en `logs/`, igual que
agente.py.
"""
import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from agente import BASE_URL, LOGS, MODELO, PROMPT, cargar_env, formatear_log, registrar

RAIZ = Path(__file__).parent


async def crear_agente():
    cliente = MultiServerMCPClient({
        "hospital": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(RAIZ / "servidor_mcp.py")],
            # Sin esto, el SDK de MCP arranca el subproceso con un entorno restringido
            # (sin las variables que huggingface_hub necesita para descargar el encoder
            # de la parte 1) y la carga de sentence-transformers se cuelga sin error.
            "env": dict(os.environ),
        },
    })
    tools = await cliente.get_tools()
    modelo = ChatOpenAI(
        model=MODELO,
        base_url=BASE_URL,
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0,
        extra_body={"usage": {"include": True}},
    )
    return create_agent(modelo, tools, system_prompt=PROMPT)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preguntas", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ids", help="solo estos ids, separados por coma (para depurar)")
    args = ap.parse_args()

    cargar_env()
    preguntas = [json.loads(l) for l in Path(args.preguntas).read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.ids:
        preguntas = [p for p in preguntas if p["id"] in args.ids.split(",")]
    agente = await crear_agente()

    LOGS.mkdir(exist_ok=True)
    log = LOGS / f"agente_mcp_{time.strftime('%Y%m%d_%H%M%S')}.md"
    secciones = [f"# Corrida del agente MCP (parte 3)\n\nModelo: `{MODELO}`. Preguntas: `{args.preguntas}`.\n"]
    total = 0.0
    with open(args.salida, "w", encoding="utf-8") as f:
        for p in preguntas:
            try:
                res = await agente.ainvoke({"messages": [HumanMessage(p["pregunta"])]},
                                            config={"recursion_limit": 14})
                r = registrar(p["id"], res["messages"])
            except Exception as e:  # una pregunta que falla no tira la corrida entera
                r = {"id": p["id"], "respuesta": "", "contextos": [], "herramientas": [],
                     "pasos": [], "usos": [], "costo": 0.0}
                secciones.append(f"## {p['id']}: ERROR `{type(e).__name__}: {e}`\n")
            total += r["costo"]
            f.write(json.dumps({k: r[k] for k in ("id", "respuesta", "contextos", "herramientas")},
                                ensure_ascii=False) + "\n")
            f.flush()
            secciones.append(formatear_log(p, r))
            print(f"{p['id']} {r['herramientas']} USD {r['costo']:.6f}")
    secciones.append(f"---\n\nCosto total de la corrida: USD {round(total, 6)}\n")
    log.write_text("\n".join(secciones), encoding="utf-8")
    print(f"log: {log} costo total: USD {total:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
