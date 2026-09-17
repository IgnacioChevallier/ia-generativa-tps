# TP Prompting - Misión: el prompt mínimo

Interfaz de chat propia sobre 4 modelos vía [OpenRouter](https://openrouter.ai), usada para generar `vida.py` (juego de la vida de Conway) en la menor cantidad de prompts posible, midiendo tokens, caching y costo.

Consigna completa en [task/mission.md](task/mission.md) y [task/rubric.md](task/rubric.md). Informe final en [informe.md](informe.md)

## Setup

Requiere Python 3 (solo stdlib, sin dependencias) y una API key de OpenRouter:

```bash
echo 'OPENROUTER_API_KEY=sk-or-...' > .env    # junto a openrouter.py; está gitignoreado
```

## Cómo correr

```bash
python3 chat_interface.py                # interfaz de chat (ejercicio 1)
python3 openrouter.py                    # smoke test de los 4 slots, imprime usage
python3 task/tests/test_vida.py vida.py  # tests de la cátedra sobre el target
python3 vida.py archivos/glider.txt 4    # corre 4 generaciones de esa grilla y las imprime
```

Comandos dentro del chat: `/model`, `/effort <nivel>`, `/schema <json>`, `/system <texto>`,
`/file <ruta>`, `/exit`. Cambiar de modelo arranca conversación nueva (requisito de la
consigna). Cada conversación deja un log en `logs/`.

## Estructura


| Archivo                      | Qué es                                                                                       |
| ---------------------------- | -------------------------------------------------------------------------------------------- |
| `openrouter.py`              | Cliente único de OpenRouter: `MODELS` (los 4 slots) y `chat()`.                              |
| `chat_interface.py`          | REPL de la interfaz; muestra usage y escribe el log.                                         |
| `vida.py`                    | El target del ejercicio 2. **No se edita a mano**: es byte a byte el código del log ganador. |
| `logs/*.md`                  | Un log por conversación. Evidencia de auditoría: sin log, la corrida no cuenta.              |
| `prompt_conway_intento1.txt` | El prompt del ejercicio 2.                                                                   |
| `informe.md`                 | El informe de los 3 ejercicios (hallazgos, tokens, costos).                                  |
| `SPEC.md`                    | Qué hace cada componente y qué se decidió no construir.                                      |
| `CLAUDE.md`                  | Reglas de trabajo del repo.                                                                  |
| `archivos/`                  | Grillas de ejemplo para correr `vida.py`.                                                    |
| `task/`                      | Consigna, rúbrica y tests de la cátedra.                                                     |




## Los 4 modelos


| Slot | Modelo                            | Para qué                           |
| ---- | --------------------------------- | ---------------------------------- |
| 1    | `openai/gpt-5.6-luna`             | `reasoning.effort`                 |
| 2    | `anthropic/claude-haiku-4.5`      | `cache_control` explícito          |
| 3    | `google/gemini-3.7-flash`         | JSON Schema en `response_format`   |
| 4    | `deepseek/deepseek-v4-flash-0731` | barato; el usado en el ejercicio 2 |




## Grillas de ejemplo

Una línea por fila, `#` célula viva, `.` muerta, rectangular. El mundo es finito: fuera de
los bordes todo está muerto, sin wrap-around. Comportamiento verificado corriendo cada una:

| Archivo | Grilla | Qué hace |
|---|---|---|
| `archivos/bloque.txt` | 4×4 | Naturaleza muerta: no cambia nunca. |
| `archivos/blinker.txt` | 5×5 | Oscilador de período 2. |
| `archivos/sapo.txt` | 6×6 | Oscilador de período 2, más grande. |
| `archivos/glider.txt` | 8×8 | Nave: se desplaza una diagonal cada 4 generaciones, choca el borde y queda estática en la generación 23. |
| `archivos/pentadecatlon.txt` | 9×18 | Una fila de 10 células que se estabiliza en un oscilador de período 15. |

```bash
python3 vida.py archivos/blinker.txt 1    # el blinker se da vuelta
python3 vida.py archivos/glider.txt 4     # el glider bajó una diagonal
python3 vida.py archivos/bloque.txt 0     # con 0 generaciones imprime la grilla tal cual
```

## Secciones del informe

- Trabajo previo (router de modelos, mapa de proveedores, comparación de `supported_parameters`) 
- Ejercicio 1 (la interfaz) 
- Ejercicio 2 (el prompt, los tres intentos, hallazgos) 
- Ejercicio 3 (tokens, thinking, cache, gasto total vs. dashboard).

