# TP final: el agente de admisión de guardia

Consigna: [task/mission.md](task/mission.md). Manual del kit de la cátedra: [task/README.md](task/README.md). Resultados y
decisiones: [INFORME.md](INFORME.md). **Estado: Partes 1 y 2 hechas; Partes 3, 4 y 5 pendientes** (ver el informe).

## Entorno

```bash
uv sync
```

Todo se corre desde esta carpeta. No hace falta ninguna clave para lo que está hecho. Las Partes 3 y 4 van a necesitar un
`.env` con `HF_TOKEN` y la clave de W&B (hay un `.env.example` sin valores cuando lleguen); el `.env` nunca se sube.

## Qué hay y de dónde sale cada archivo

| Archivo | Lo genera | Qué es |
|---|---|---|
| `curado/oraculo.py` | (código) | calcula la ficha correcta con las normas y las costumbres |
| `historial_clasificado.csv` | `uv run python -m curado.clasificar` | `id,tipo` de las 2.000 filas del historial |
| `curado/detalle_clasificacion.jsonl`, `curado/resumen_clasificacion.json` | `uv run python -m curado.clasificar` | motivo de cada clasificación y cuentas por norma |
| `costumbres.md` | `uv run python -m curado.costumbres` | las costumbres del hospital, con las filas que las respaldan |
| `datos/trayectorias_*.jsonl`, `datos/conversaciones_*.jsonl`, `datos/versiones_sinteticas.json`, `datos/resumen_generacion.json`, `datos/SHA256SUMS` | `uv run python -m curado.generar_datos` | datos de entrenamiento (no están en git: se regeneran, determinista; `cd datos && sha256sum -c SHA256SUMS`) |
| `buscador.py`, `buscador_expansiones.json` | (código y datos escritos a mano) | el buscador de las normas |
| `entrega.py` | (código) | `construir_buscador`; `construir_agente` todavía no existe |
| `datos/consultas_propias.jsonl` | `uv run python -m experimentos.consultas_propias` | 41 consultas propias para el buscador |
| `experimentos/rag/*.json` | `experimentos/rag_grilla.py` y `admision.evaluar_rag` (ver abajo) | cada variante del buscador que se midió |

## Comandos

```bash
# Tests (el oráculo contra las 150 fichas de práctica, la clasificación, el buscador, las trayectorias)
uv run python -m unittest discover -s tests -t .

# Oráculo contra las fichas esperadas de la cátedra
uv run python -m curado.validar_oraculo

# Evaluación del buscador (obligatoria, usa las normas originales)
uv run python -m admision.evaluar_rag --entrega entrega.py --normas normas/original --consultas rag/consultas_dev.jsonl

# Grilla de variantes del buscador
uv run python -m experimentos.rag_grilla
uv run python -m experimentos.rag_grilla --consultas datos/consultas_propias.jsonl --salida experimentos/rag/grilla_propias.json
uv run python -m experimentos.rag_grilla --ajustar-bm25
```

Los cuatro generadores (`curado.clasificar`, `curado.costumbres`, `curado.generar_datos`, `experimentos.consultas_propias`)
escriben sus archivos con saltos de línea `\n` en cualquier sistema operativo, para que los hashes coincidan.

## Pendiente para entregar

Un caso de ejemplo con `admision.correr`, la evaluación completa de los 50 casos con las normas original, b y c, el
diagrama de cómo se conectan el agente, las herramientas, el buscador y el modelo, y el `.env.example`: dependen del
agente (Partes 3 y 4).
