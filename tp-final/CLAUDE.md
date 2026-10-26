# CLAUDE.md

Instrucciones de proyecto para trabajar en este TP con un asistente de código.
Consigna completa: [task/mission.md](task/mission.md). Manual del kit (contrato de
`entrega.py`, comandos de práctica y del buscador): [task/README.md](task/README.md).

## Qué es esto

TP final, "el agente de admisión de guardia": un agente sobre un modelo libre chico
(Gemma 4 E4B u otro de hasta 8B parámetros) que completa la ficha de admisión de 8 campos
usando cinco herramientas. Partes: curado del historial (1), buscador RAG sobre las normas
(2), optimización de prompt antes de entrenar (3), entrenamiento (4) y recursos y
producción (5). Entrega: viernes 20 de noviembre de 2026.

## Estructura

Esta carpeta es la raíz de la entrega: los comandos del kit se corren **desde acá**
(`tp-final/`), porque asumen `normas/`, `practica/`, `rag/` y `admision/` al lado.

- `task/mission.md`, `task/README.md` — la consigna y el manual del kit.
- `admision/`, `normas/{original,b,c}/`, `practica/`, `historial/historial.csv`,
  `rag/consultas_dev.jsonl`, `pyproject.toml` — archivos de la cátedra, copiados sin cambios.
- `uv.lock` — sale de `uv sync`.
- `curado/` — Parte 1: `oraculo.py` (la ficha correcta, validada contra las 150 fichas de práctica),
  `clasificar.py`, `costumbres.py`, `trayectorias.py` y `generar_datos.py` (datos de entrenamiento).
- `buscador.py` + `buscador_expansiones.json` — Parte 2. `entrega.py` es lo único que llama la cátedra.
- `experimentos/` — grilla del buscador y consultas propias; los resultados quedan en `experimentos/rag/`.
- `tests/` — `uv run python -m unittest discover -s tests -t .` (sin dependencias nuevas).
- `INFORME.md`, `README.md`, `costumbres.md`, `historial_clasificado.csv` — entregables. Qué genera cada archivo: README.
- `datos/` — se regenera con `curado.generar_datos` (determinista); en git solo van `SHA256SUMS` y lo chico.

Los generadores escriben con `\n` aunque se corran en Windows: si agregás uno, pasá `newline="\n"` al escribir.

Entorno: `uv sync`, y todo con `uv run ...`. Si hay otro `VIRTUAL_ENV` activo (p. ej. el de
`rag-mcp-transformers/`), uv lo ignora y usa `.venv/` de esta carpeta.

## Reglas no negociables

1. **No modificar** `admision/`, `normas/`, `practica/`, `historial/` ni `rag/`: la cátedra
   corre con su propia copia de `admision` y con un test secreto de otros casos y normas.
2. **Nada de números de las normas en el código ni en los pesos**: en el test cambian. Lo
   que cambia lo trae el buscador, que se arma siempre con la carpeta que recibe.
3. **En operación, el agente no llama a servicios externos.** Los modelos pagos solo se
   usan para programar o generar datos.
4. **Nunca optimizar el prompt sobre el test**, solo sobre práctica o casos generados.
5. **Dependencias fijadas** en `pyproject.toml` + `uv.lock`; todo debe entrar en una A100
   de 40 GB.
6. **Auditabilidad:** todo archivo generado sale de un script del repo, y cada número del
   informe dice qué comando, punto de control y prompt lo producen.
7. **Nunca commitear `.env`** (tokens de Hugging Face y W&B).
