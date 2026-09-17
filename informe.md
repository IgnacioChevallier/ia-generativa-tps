# Informe — Misión: el prompt mínimo

## Trabajo previo obligatorio

### 1. Qué es un router de modelos

Un router es una capa intermedia que, para un mismo request, decide a qué modelo o
proveedor enviarlo (por costo, latencia, disponibilidad, o qué funcionó mejor en tareas
parecidas), sin que quien llama tenga que elegir el `model` id a mano. El **Auto Router**
de OpenRouter (`openrouter/auto`) resuelve esto concretamente: elige según qué modelo usó
el mercado de OpenRouter para tareas similares en los últimos 7 días. Resuelve tanto "no
sé cuál modelo conviene para esta tarea" como el fallback automático cuando un proveedor
se cae o se satura.

### 2. Mapa de los 7 proveedores

Modelo más avanzado de cada proveedor conocido, según el catálogo de OpenRouter
(`GET /api/v1/models`) y el ranking de `/discover` (Artificial Analysis intelligence
index), consultado el 2026-09-16:

| Proveedor | Modelo insignia | Precio in/out (USD por millón de tokens) | Contexto | Benchmark |
|---|---|---|---|---|
| OpenAI | `gpt-6-astra` | $10 / $50 | 1.050.000 | 53/100 — 1° puesto (empatado) |
| Anthropic | `claude-fable-5.1` | $10 / $50 | 1.000.000 | 53/100 — 1° puesto (empatado); 82 en índice de coding |
| Qwen | `qwen3.8-max-0902` | $2 / $6 | 1.000.000 | 53/100 — 3° puesto |
| Grok (xAI) | `grok-4.6` | $2 / $6 | 500.000 | 44/100 — 4° puesto |
| Gemini (Google) | `gemini-3.8-flash` | $0,75 / $3,75 | 1.048.576 | 41/100 — 5° puesto |
| Kimi (Moonshot AI) | `kimi-k3` | $3 / $15 | 1.048.576 | no listado en `/discover` al momento de la consulta |
| DeepSeek | `deepseek-v4-flash-0731` | $0,06 / $0,12 | 1.310.720 | no compite en el ranking absoluto; aparece como "best value" (percentil 72 de inteligencia al precio más bajo de la tabla) |

**Hallazgo.** El modelo insignia de DeepSeek según `/discover` es exactamente
`deepseek-v4-flash-0731` — el mismo que la consigna asigna al slot 4 del ejercicio 1. No
es casualidad: es la razón por la que la consigna lo elige como "el escalón barato" del
ejercicio 2.

### 3. Comparación de `supported_parameters`

Fichas comparadas: los 4 modelos del ejercicio 1, vía `GET /api/v1/models`.

| Parámetro | GPT-5.6 Luna (OpenAI) | Claude Haiku 4.5 (Anthropic) | Gemini 3.7 Flash (Google) | DeepSeek V4 Flash 0731 |
|---|---|---|---|---|
| `reasoning_effort` | Sí | No (solo `reasoning` con `max_tokens` como presupuesto) | Sí | Sí |
| `response_format` / salidas estructuradas | Sí | Sí | Sí | Sí |
| `temperature`, `top_p`, `top_k` | No, ninguno | Sí, los tres | Sí `temperature`/`top_p` (no `top_k`) | Sí los tres, más `top_a`, `min_p`, `repetition_penalty` |
| `tools` / `tool_choice` | Sí | Sí | Sí | Sí |
| Otros parámetros propios | `seed` | `stop` | `seed`, `stop` | `frequency_penalty`, `presence_penalty`, `logit_bias`, `logprobs`, `parallel_tool_calls` |

**Hallazgo.** GPT-5.6 Luna solo expone perillas de razonamiento, sin sampling clásico (ni
siquiera `temperature`). DeepSeek es, de los 4, el que soporta el superset más amplio de
la API estilo OpenAI.

---

## Ejercicio 1 — Interfaz de chat, cuatro modelos

_(cubierto por `openrouter.py` y `chat_interface.py`; logs de prueba en `logs/`)_

## Ejercicio 2 — El target en 1 prompt

### El prompt

Se diseñó con los 6 componentes de la clase (rol, contexto, instrucciones, restricciones,
ejemplos, input), con todo el bloque salvo el input idéntico en los tres intentos para
forzar el cache por prefijo. El texto completo queda en `prompt_conway_intento1.txt` y,
tal cual se mandó, en cada log de `logs/deepseek_deepseek-v4-flash-0731_*`. Los ejemplos
cubren los 5 casos clave del contrato: oscilador, naturaleza muerta, muerte por soledad,
nacimiento por 3 vecinas, y borde sin wrap-around (el más propenso a errores, porque es
donde un modelo suele asumir wrap por defecto).

Modelo: `deepseek/deepseek-v4-flash-0731`, `reasoning.effort = high` en los tres intentos.

### Los tres intentos

| Intento | Hora | Prompts en la conversación | Tests | `cached_tokens` | `reasoning_tokens` | Costo |
|---|---|---|---|---|---|---|
| 1 | 2026-09-16 20:51 | 2 (incluye un `hola` de chequeo de conectividad, sin querer en la misma conversación) | 9/9 ✅ | 65/85 → 911/911 (100%, ver hallazgo) | 22 + 9264 | $0.000983 |
| 2 — **ganador** | 2026-09-16 21:18 | 1 | 9/9 ✅ | 0 | 1071 | $0.000355 |
| 3 | 2026-09-16 21:23 | 1 | 9/9 ✅ | 0 | 14356 | $0.005093 |

**Conversación ganadora: intento 2** (`logs/deepseek_deepseek-v4-flash-0731_20260916_211821.md`).
Un solo prompt, los 9 tests pasan con el script tal cual salió del chat, y es el más
barato de los tres. `vida.py` en la raíz del repo es exactamente ese código, sin
modificar a mano.

Los intentos 1 y 3 no fueron descartados por fallar (los tres pasaron los 9 tests) — se
conservan sus logs porque sirvieron para investigar el comportamiento del caching (ver
hallazgo abajo) y quedan como evidencia adicional, no como intentos quemados en el sentido
de la consigna.

### Hallazgos

**El caching automático de DeepSeek no está disponible en ningún proveedor que lo sirve en
OpenRouter, al momento de esta entrega.** El bloque estático se mandó idéntico, carácter
por carácter, en los tres intentos, y en los intentos 2 y 3 (cada uno en una conversación
nueva e independiente) `cached_tokens` dio 0 en ambos — incluso mandando el intento 3
apenas 4 minutos después del 2, lo que descarta que el cache haya expirado por tiempo.

Para confirmar la causa, se consultó el endpoint de OpenRouter que lista los proveedores
que sirven este modelo: `GET https://openrouter.ai/api/v1/models/deepseek/deepseek-v4-flash-0731/endpoints`.
Devuelve ~28 hosts distintos (Fireworks, DeepInfra, Together, Novita, OpenInference,
Inceptron, entre otros) entre los que OpenRouter reparte las requests sin que el
usuario elija cuál — y **los 28 tienen `"supports_implicit_caching": false`**. Es decir,
ningún proveedor detrás de OpenRouter soporta hoy el caching automático por prefijo que
describe la consigna para este modelo. Esto explica por completo los intentos 2 y 3 (0
cache es el comportamiento correcto dado que no hay caching disponible), y sugiere que el
`cached=911/911` (100%) del intento 1 fue una anomalía puntual del usage reportado por
ese request en particular, no un cache real — no puede haber cache genuino si la
infraestructura entera lo tiene deshabilitado.

**Conclusión del hallazgo:** con el catálogo de proveedores de OpenRouter vigente al
2026-09-16, es imposible demostrar `cached_tokens > 0` de forma reproducible con
`deepseek/deepseek-v4-flash-0731`, independientemente de cómo se diseñe el prompt — la
limitación es de la infraestructura del proveedor, no del diseño del prompt ni de la
ejecución del ejercicio.

**El razonamiento varió muchísimo con el mismo prompt y el mismo `effort=high`.** Entre
los intentos 2 y 3, `reasoning_tokens` fue de 1071 a 14356 (13 veces más) con el prompt
exactamente igual — el costo pasó de $0.000355 a $0.005093 por esa sola razón. El nivel de
esfuerzo de razonamiento de DeepSeek parece no ser determinístico ni estable entre
llamadas idénticas.

**El código generado fue distinto en cada intento** (nombres de variables, estructura de
validación) a pesar del prompt idéntico — esperable en un modelo generativo, pero confirma
que no hubo ningún tipo de respuesta cacheada o reusada, solo el prompt de entrada.

## Ejercicio 3 — La cuenta final

_Pendiente  tabla de tokens/costos consolidada de los 3
intentos de arriba, reconciliación contra el dashboard de OpenRouter, y conclusión de tres
líneas. Los datos crudos de cada intento ya están en la tabla del ejercicio 2 y en sus
logs — falta sumar totales y contrastar contra el dashboard de actividad de la cuenta._
