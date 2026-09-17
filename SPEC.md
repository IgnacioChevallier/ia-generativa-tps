# SPEC.md

Qué se construyó, concretamente. La consigna completa está en
[task/mission.md](task/mission.md); esto describe la implementación.

## Componentes

### `openrouter.py` — cliente único de OpenRouter

Un solo punto de entrada (`chat(model, messages, *, effort=None, json_schema=None,
max_tokens=16000, timeout=300)`) para los 4 modelos del TP, todos contra el mismo
endpoint (`POST /api/v1/chat/completions`), cambiando solo el `model` id:

| Slot | Modelo | Parámetro que ejercita |
|---|---|---|
| 1 | `openai/gpt-5.6-luna` | `reasoning: {effort}` |
| 2 | `anthropic/claude-haiku-4.5` | `cache_control: {type: "ephemeral"}` en los mensajes `system` (marcado automático por `_mark_cache`) |
| 3 | `google/gemini-3.7-flash` | `response_format: {type: "json_schema", ...}` |
| 4 | `deepseek/deepseek-v4-flash-0731` | ninguno especial — el modelo barato del ejercicio 2 |

`parse_usage()` aplana el `usage` de la respuesta a un dict fijo: `prompt_tokens`,
`completion_tokens`, `cached_tokens`, `reasoning_tokens`, `cost`, `cache_discount`. Los
campos que no vienen en la respuesta quedan en 0, nunca faltan.

La API key sale de `OPENROUTER_API_KEY` en el entorno, o de un archivo `.env` junto a este
archivo (no versionado — ver `.gitignore`).

### `chat_interface.py` — interfaz de chat (ejercicio 1)

REPL de terminal, sin UI gráfica (no lo pide la consigna). Al arrancar, elige uno de los 4
modelos; `/model` cambia de modelo y **arranca una conversación nueva** (mensajes, effort
y schema se resetean — no se arrastra estado entre modelos). Comandos: `/effort`,
`/schema`, `/system`, `/file` (para prompts largos guardados en `.txt`), `/exit`.

Después de cada respuesta imprime el usage completo (`prompt/completion/cached/reasoning
tokens` + costo) y lo agrega al log de la conversación en curso.

### Logs — `logs/<modelo>_<timestamp>.md`

Un archivo por conversación, creado al elegir modelo (no al mandar el primer mensaje).
Cada turno (`user`, `assistant`, `system`, o `error`) se agrega en el momento, en orden
cronológico — no se editan después. Formato: encabezado con modelo y hora de inicio, y un
bloque `## <rol>` por turno; los turnos `assistant` incluyen la línea `**Usage:** ...` con
los 5 campos de usage.

Este log es la única evidencia de auditoría de la misión: sin log, esa corrida no cuenta
(regla de admisibilidad de `task/rubric.md`).

### `vida.py` — el target del ejercicio 2

Juego de la vida de Conway, un solo archivo, sin dependencias externas. Interfaz fija:
`python3 vida.py <archivo_estado_inicial> <generaciones>`, grilla rectangular
(`#`/`.`), mundo finito sin wrap-around, `generaciones=0` devuelve el estado inicial tal
cual. Generado en 1 prompt contra `deepseek/deepseek-v4-flash-0731` (slot 4) a través de
`chat_interface.py` — es texto idéntico, carácter por carácter, al bloque de código de
`logs/deepseek_deepseek-v4-flash-0731_20260916_211821.md` (la conversación ganadora, ver
`informe.md`). No se edita a mano: cualquier cambio necesario se hace reescribiendo el
prompt y corriendo de nuevo.

### `prompt_conway_intento1.txt`

El prompt usado en el ejercicio 2, con los 6 componentes de la clase (rol, contexto,
instrucciones, restricciones, ejemplos, input). El bloque estático (todo menos el input)
se mandó idéntico en los 3 intentos, para intentar forzar cache por prefijo — ver en
`informe.md` por qué no hubo cache real disponible para este modelo.

### `task/`

Material de la cátedra, sin modificar: `mission.md` (consigna), `rubric.md` (rúbrica) y
`tests/test_vida.py` (los 9 tests, invocados como `python3 task/tests/test_vida.py
vida.py`).

### `informe.md`

El informe de los 3 ejercicios: trabajo previo (router, mapa de 7 proveedores,
`supported_parameters`), los 3 intentos del ejercicio 2 con su tabla de usage y los
hallazgos (caching no disponible en DeepSeek/OpenRouter, varianza del razonamiento), y la
cuenta final del ejercicio 3 (tokens, costo, reconciliación contra el gasto real de la
cuenta, conclusión).

## Qué no se construyó

- Sin interfaz gráfica ni web — la consigna es explícita en que no hace falta.
- Sin persistencia más allá de los logs `.md` — no hay base de datos ni historial cargable
  entre corridas del REPL.
- Sin manejo de reintentos automáticos ante error de la API: `chat_interface.py` muestra
  el error, lo deja en el log, y no reenvía el mensaje fallido (evita mandar el mismo
  prompt dos veces por accidente y contaminar el conteo de "prompts en la conversación").
