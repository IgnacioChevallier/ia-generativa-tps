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
- `recuperar.py` — parte 1. La configuración ganadora queda fija en `CONFIG`; `buscar(pregunta)`
  es lo que usan las herramientas de las partes 2 y 3.
- `hospital.py` — las seis herramientas (partes 2 y 3), sin LangChain ni MCP: las envuelve
  `agente.py` (parte 2) y `servidor_mcp.py` (parte 3), sin duplicar su lógica.
- `agente.py` / `servidor_mcp.py` + `agente_mcp.py` — parte 2 y parte 3. El servidor
  precarga el encoder de la parte 1 en el hilo principal antes de `mcp.run()` (ver
  SPEC.md): necesario en Windows, donde el primer import de `torch` desde un hilo
  secundario puede colgarse sin error.
- `experimentos/` — grilla de la parte 1 (`correr.py`) con un `.eval.json` por configuración;
  `experimentos/inspector/` — capturas de MCP Inspector probando el servidor (parte 3).
- `tests/` — tests propios: `python3 -m pytest tests/`.
- `atencion.py` — parte 4.

## Reglas no negociables

1. **No modificar** `evaluar/evaluar.py`, `api/`, `datos/` ni `atencion/test_atencion.py`:
   la cátedra corre sus propias copias. Si un test no pasa, se cambia nuestro código.
2. **`atencion.py` usa solo NumPy** (lo exige el test).
3. **Todo en Python.** Las partes 2 y 3 con LangChain; el servidor MCP con FastMCP del SDK
   oficial `mcp` 1.x, sin LangChain.
4. **Nunca commitear `.env`** (tiene la `OPENROUTER_API_KEY`).
5. **La parte 5 se resuelve a mano, sin IA.** No generar sus cuentas ni sus respuestas.
6. **Cada configuración de la parte 1 que se reporte** tiene que tener su `.eval.json` en
   `experimentos/`, generado por `evaluar/evaluar.py` sin modificar.

## Cómo correr

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt "torch==2.2.2" "numpy<2" "transformers<4.50" "sentence-transformers<6"
python3 atencion/test_atencion.py atencion.py      # parte 4: 14 tests
pip install pytest && python3 -m pytest tests/     # parte 1: tests propios
python3 recuperar.py --preguntas datos/preguntas_recuperacion_dev.jsonl --salida resultados.jsonl
```

Las versiones fijadas son por la Mac Intel (x86_64): PyTorch no publica wheels para esa
plataforma después de 2.2.2 (que soporta hasta Python 3.12), y transformers 5 no carga con
ese torch. Además, desde la 4.50, transformers se niega a leer pesos `.bin` con torch < 2.6, y
`BAAI/bge-m3` (el encoder de la parte 1) solo publica `pytorch_model.bin`: con 4.49 carga.
En Apple Silicon o Linux alcanza con `pip install -r requirements.txt`.

## Commits

Historia limpia: un commit por unidad de trabajo real, con mensaje que explica el cambio.
TDD: los tests de la cátedra (o uno propio, si no hay) primero, después el código.
