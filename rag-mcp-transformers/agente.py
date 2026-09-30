"""Agente de la parte 2: responde preguntas de pacientes con dos fuentes, los documentos del
hospital (recuperador de la parte 1) y la API del estado del día.

  python3 agente.py --preguntas datos/preguntas_agente_dev.jsonl --salida respuestas.jsonl

Requiere OPENROUTER_API_KEY (en el entorno o en `.env`) y la API levantada
(`python3 api/servidor.py`). Por cada corrida escribe un log `.md` en `logs/` con las
llamadas a herramientas y el usage de cada llamada al modelo.
"""
import argparse
import json
import os
import time
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

from hospital import HERRAMIENTAS

MODELO = "deepseek/deepseek-v4-flash-0731"
BASE_URL = "https://openrouter.ai/api/v1"
LOGS = Path(__file__).parent / "logs"

PROMPT = """Sos el asistente del Hospital Provincial Arroyo Claro. Contestás preguntas de \
pacientes y familiares en español rioplatense, con claridad y en pocas líneas.

Tenés dos fuentes y ninguna otra:
- Documentos del hospital (buscar_documentos): normas y procedimientos que casi no cambian.
- La API del hospital (consultar_*): el estado de hoy (camas, guardia, turnos, farmacia, espera).

Cómo trabajar:
1. Para cada pregunta, llamá a las herramientas antes de contestar. Nunca contestes de memoria.
2. Si la pregunta mezcla las dos cosas (por ejemplo "¿hay lugar y me puedo quedar?", "¿cuál es \
el primer turno y qué tengo que llevar?", "¿tienen el remedio y qué necesito para retirarlo?"), \
llamá a la herramienta de la API y también a buscar_documentos.
3. Contestá solo con lo que devolvieron las herramientas. No agregues datos, cifras, horarios \
ni consejos que no aparezcan ahí. Si una herramienta no trae el dato, decilo.
4. Si una herramienta devuelve un error con opciones válidas, corregí el argumento y \
volvé a llamarla.
5. Respondé todo lo que se preguntó, con los números y fechas exactos (y el día y la hora \
si los hay). No menciones las herramientas ni el proceso: contestá directo."""


def cargar_env():
    env = Path(__file__).with_name(".env")
    if env.exists():
        for linea in env.read_text(encoding="utf-8").splitlines():
            k, _, v = linea.partition("=")
            if k.strip() and not k.startswith("#"):
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("Falta OPENROUTER_API_KEY (en .env o en el entorno)")


def crear_agente():
    modelo = ChatOpenAI(
        model=MODELO,
        base_url=BASE_URL,
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0,
        extra_body={"usage": {"include": True}},  # OpenRouter devuelve el costo real
    )
    tools = [StructuredTool.from_function(f) for f in HERRAMIENTAS]
    return create_agent(modelo, tools, system_prompt=PROMPT)


def registrar(pid, mensajes):
    """Resume los mensajes de una corrida del agente en un registro."""
    contextos, herramientas, pasos, usos = [], [], [], []
    respuesta = ""
    for m in mensajes:
        if isinstance(m, AIMessage):
            um = m.usage_metadata or {}
            costo = (m.response_metadata.get("token_usage") or {}).get("cost") or 0.0
            uso = {"prompt_tokens": um.get("input_tokens", 0),
                   "completion_tokens": um.get("output_tokens", 0), "costo": costo}
            usos.append(uso)
            pasos.append({"tipo": "modelo", **uso})
            for tc in m.tool_calls:
                herramientas.append(tc["name"])
                pasos.append({"tipo": "llamada", "id": tc["id"], "nombre": tc["name"], "args": tc["args"]})
            if not m.tool_calls:
                respuesta = m.text
        elif isinstance(m, ToolMessage):
            texto = m.content if isinstance(m.content, str) else json.dumps(m.content, ensure_ascii=False)
            contextos.append(texto)
            pasos.append({"tipo": "resultado", "id": m.tool_call_id, "nombre": m.name, "contenido": texto})
    return {"id": pid, "respuesta": respuesta, "contextos": contextos, "herramientas": herramientas,
            "pasos": pasos, "usos": usos, "costo": round(sum(u["costo"] for u in usos), 8)}


def formatear_log(pregunta, r):
    """Sección del log `.md` de una pregunta."""
    lineas = [f"## {pregunta['id']}: {pregunta['pregunta']}", ""]
    n = 0
    for p in r["pasos"]:
        if p["tipo"] == "modelo":
            n += 1
            lineas.append(f"**Llamada {n} al modelo**: {p['prompt_tokens']} tokens de entrada, "
                          f"{p['completion_tokens']} de salida, costo USD {p['costo']:.6f}")
        elif p["tipo"] == "llamada":
            lineas.append(f"- Herramienta `{p['nombre']}` con argumentos "
                          f"`{json.dumps(p['args'], ensure_ascii=False)}`")
        else:
            lineas += [f"  Resultado de `{p['nombre']}`:", "", "  ```", *[f"  {l}" for l in p["contenido"].splitlines()],
                       "  ```"]
        lineas.append("")
    lineas += [f"**Respuesta:** {r['respuesta']}", ""]
    if "respuesta_referencia" in pregunta:
        lineas += [f"*Referencia:* {pregunta['respuesta_referencia']}", ""]
    lineas += [f"Costo de la pregunta: USD {r['costo']:.6f}", ""]
    return "\n".join(lineas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preguntas", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ids", help="solo estos ids, separados por coma (para depurar)")
    args = ap.parse_args()

    cargar_env()
    preguntas = [json.loads(l) for l in Path(args.preguntas).read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.ids:
        preguntas = [p for p in preguntas if p["id"] in args.ids.split(",")]
    agente = crear_agente()

    LOGS.mkdir(exist_ok=True)
    log = LOGS / f"agente_{time.strftime('%Y%m%d_%H%M%S')}.md"
    secciones = [f"# Corrida del agente (parte 2)\n\nModelo: `{MODELO}`. Preguntas: `{args.preguntas}`.\n"]
    total = 0.0
    with open(args.salida, "w", encoding="utf-8") as f:
        for p in preguntas:
            try:
                res = agente.invoke({"messages": [HumanMessage(p["pregunta"])]},
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
            print(f"{p['id']}  {r['herramientas']}  USD {r['costo']:.6f}")
    secciones.append(f"---\n\nCosto total de la corrida: USD {round(total, 6)}\n")
    log.write_text("\n".join(secciones), encoding="utf-8")
    print(f"log: {log}  costo total: USD {total:.6f}")


if __name__ == "__main__":
    main()
