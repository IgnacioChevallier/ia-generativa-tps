"""Tests de la lógica de agente.py que no necesita un LLM: cómo se arma el registro de una
pregunta (respuesta, contextos, herramientas, usage) a partir de los mensajes del agente."""
import sys
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agente import formatear_log, registrar  # noqa: E402


def mensajes_de_ejemplo():
    return [
        HumanMessage("¿Hay camas en pediatría y me puedo quedar?"),
        AIMessage("", tool_calls=[
            {"name": "consultar_camas", "args": {"sector": "pediatria"}, "id": "c1"},
            {"name": "buscar_documentos", "args": {"consulta": "acompañante en pediatría"}, "id": "c2"},
        ], usage_metadata={"input_tokens": 500, "output_tokens": 40, "total_tokens": 540},
            response_metadata={"token_usage": {"cost": 0.00003}}),
        ToolMessage('{"datos": {"libres": 7}}', tool_call_id="c1", name="consultar_camas"),
        ToolMessage("Madre, padre o tutor 24 horas", tool_call_id="c2", name="buscar_documentos"),
        AIMessage("Hay 7 camas libres y pueden quedarse las 24 horas.",
                  usage_metadata={"input_tokens": 700, "output_tokens": 30, "total_tokens": 730},
                  response_metadata={"token_usage": {"cost": 0.00004}}),
    ]


def test_registrar_extrae_respuesta_contextos_y_herramientas():
    r = registrar("A10", mensajes_de_ejemplo())
    assert r["id"] == "A10"
    assert r["respuesta"] == "Hay 7 camas libres y pueden quedarse las 24 horas."
    assert r["contextos"] == ['{"datos": {"libres": 7}}', "Madre, padre o tutor 24 horas"]
    assert r["herramientas"] == ["consultar_camas", "buscar_documentos"]


def test_registrar_suma_usage_de_cada_llamada_al_modelo():
    r = registrar("A10", mensajes_de_ejemplo())
    assert [u["prompt_tokens"] for u in r["usos"]] == [500, 700]
    assert r["costo"] == 0.00007


def test_registrar_sin_herramientas():
    r = registrar("X", [HumanMessage("hola"), AIMessage("Hola")])
    assert r["herramientas"] == [] and r["contextos"] == []


def test_formatear_log_incluye_llamadas_argumentos_y_resultados():
    r = registrar("A10", mensajes_de_ejemplo())
    md = formatear_log({"id": "A10", "pregunta": "¿Hay camas?"}, r)
    assert "consultar_camas" in md and '"sector": "pediatria"' in md
    assert '{"datos": {"libres": 7}}' in md
    assert "500" in md and "0.00003" in md
