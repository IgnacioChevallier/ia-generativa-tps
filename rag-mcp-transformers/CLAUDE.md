# CLAUDE.md

Instrucciones de proyecto para trabajar en este TP con un asistente de código.
Consigna completa: [task/mission.md](task/mission.md). Qué se construyó: [SPEC.md](SPEC.md).

## Qué es esto

Misión "RAG, MCP y Transformers en el Hospital Arroyo Claro": un RAG vectorial (parte 1),
un agente con tool calling (parte 2), las mismas herramientas como servidor MCP (parte 3),
una capa de atención en NumPy (parte 4) y un bloque de transformer a mano (parte 5).

## Estructura

Esta carpeta es la raíz de la entrega: los comandos del enunciado se corren **desde acá**
(`rag-mcp-transformers/`), porque asumen `datos/`, `api/`, `evaluar/` y `atencion/` al lado.

- `task/mission.md` — la consigna.
- `datos/`, `api/`, `evaluar/`, `atencion/test_atencion.py`, `a_mano/ejercicio.md`,
  `requirements.txt` — archivos de la cátedra, movidos desde `task/` sin cambios.
- `atencion.py` — parte 4.

## Reglas no negociables

1. **No modificar** `evaluar/evaluar.py`, `api/`, `datos/` ni `atencion/test_atencion.py`:
   la cátedra corre sus propias copias. Si un test no pasa, se cambia nuestro código.
2. **`atencion.py` usa solo NumPy** (lo exige el test).
3. **Todo en Python.** Las partes 2 y 3 con LangChain; el servidor MCP con FastMCP del SDK
   oficial `mcp` 1.x, sin LangChain.
4. **Nunca commitear `.env`** (tiene la `OPENROUTER_API_KEY`).
5. **La parte 5 se resuelve a mano, sin IA.** No generar sus cuentas ni sus respuestas.

## Cómo correr

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt "torch==2.2.2" "numpy<2" "transformers<5" "sentence-transformers<6"
python3 atencion/test_atencion.py atencion.py      # parte 4: 14 tests
```

Las versiones fijadas son por la Mac Intel (x86_64): PyTorch no publica wheels para esa
plataforma después de 2.2.2 (que soporta hasta Python 3.12), y transformers 5 no carga con
ese torch. En Apple Silicon o Linux alcanza con `pip install -r requirements.txt`.

## Commits

Historia limpia: un commit por unidad de trabajo real, con mensaje que explica el cambio.
TDD: los tests de la cátedra (o uno propio, si no hay) primero, después el código.
