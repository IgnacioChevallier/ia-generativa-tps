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

La interfaz es `chat_interface.py` sobre el cliente único `openrouter.py`. Hay un log de
prueba por cada uno de los 4 modelos en `logs/` (`*_20260915_*.md`), cada uno con rol,
mensaje y el usage de cada respuesta.

### Slot 2 — cache hit explícito (`cache_control`)

Claude Haiku 4.5 no cachea prompts chicos (mínimo ~4096 tokens), así que la prueba manda un
contexto estático grande como mensaje `system`, marcado con `cache_control: ephemeral` en
`_mark_cache()`. Dos pasadas del mismo contexto
(`logs/anthropic_claude-haiku-4.5_20260915_204816.md`):

| Pasada | `prompt_tokens` | `cached_tokens` | Costo |
|---|---|---|---|
| 1ª | 9035 | 0 | $0.011511 |
| 2ª | 9088 | **9023** (99%) | **$0.001097** |

El costo de entrada baja 10 veces con el cache hit. Es el único caching que el TP pudo
demostrar funcionando (ver el hallazgo de DeepSeek en el ejercicio 2).

### Slot 1 — efecto del nivel de esfuerzo

El `reasoning.effort` se fija con `/effort` y queda registrado en el log como bloque
`## config`, para que cada corrida sea auditable. Mismo prompt (un problema de teoría de
números que obliga a razonar), cada corrida en una conversación nueva para que el contexto
no contamine el resultado:

| Nivel | Log | `reasoning_tokens` | Costo |
|---|---|---|---|
| `minimal` | `openai_gpt-5.6-luna_20260917_173647.md` | 399 | $0.000503 |
| `minimal` | `openai_gpt-5.6-luna_20260917_173655.md` | 658 | $0.000814 |
| `minimal` | `openai_gpt-5.6-luna_20260917_173702.md` | 784 | $0.000965 |
| `high` | `openai_gpt-5.6-luna_20260917_173710.md` | 468 | $0.000586 |
| `high` | `openai_gpt-5.6-luna_20260917_173717.md` | 818 | $0.001006 |
| `high` | `openai_gpt-5.6-luna_20260917_173725.md` | 633 | $0.000785 |

**Hallazgo: con este modelo el efecto del `effort` existe, pero es más chico que el ruido
entre corridas idénticas.** En las 3+3 corridas logueadas de arriba las medianas quedan
prácticamente iguales (658 en `minimal` contra 633 en `high`): el efecto no se ve. Para
decidir si existía se repitió el mismo prompt hasta n=8 por nivel (las corridas extra se
hicieron llamando a `chat()` directo, sin pasar por la interfaz, y por eso no tienen log —
su costo está contabilizado en el ejercicio 3):

| Nivel | n | Mediana | Media | Rango |
|---|---|---|---|---|
| `minimal` | 8 | 484 | 553 | 327 – 934 |
| `high` | 8 | 649 | 641 | 468 – 838 |

Recién con n=8 aparece la señal: `high` razona ~1,3 veces más que `minimal` en mediana.
Pero los rangos se superponen casi por completo, así que **una sola corrida por nivel puede
dar el resultado invertido** — de hecho el primer par que se corrió dio `minimal`=934 contra
`high`=516. La conclusión práctica es que en este modelo el `effort` es una preferencia
estadística, no un dial determinístico, y que medirlo con una corrida por nivel no sirve.
Esto es coherente con lo que se ve en el ejercicio 2 con DeepSeek, donde dos corridas
idénticas con `effort=high` dieron 1071 y 14356 tokens de razonamiento.

### Slot 3 — salidas estructuradas

`/schema <json>` fija un `response_format` de tipo `json_schema`. La prueba está en
`logs/google_gemini-3.7-flash_20260915_204826.md`, donde la respuesta sale como
`{"primos":15}` en vez de texto libre. Ese log es anterior al cambio que hace que el
schema también quede escrito en el log como bloque `## config`, así que ahí se ve el
efecto del schema pero no el schema en sí.

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

**Por qué el `cached_tokens > 0` del intento 1 no es evidencia de corridas previas sin
entregar.** La lectura natural de un cache hit en el primer intento es que hubo requests
anteriores que calentaron el cache y no se entregaron. Los propios datos del repo la
descartan:

1. **La hipótesis predice lo contrario de lo que se observa.** Si una corrida previa
   hubiera dejado el prefijo estático cacheado, los intentos 2 y 3 — que mandan ese mismo
   prefijo, carácter por carácter, 27 y 32 minutos después — tendrían que haber pegado en
   ese cache también, y con más razón. Dieron `cached=0` los dos. Un cache que solo existe
   para la primera corrida y desaparece para las dos siguientes no es un cache.
2. **El 100% es aritméticamente imposible para un cache por prefijo.** El intento 1
   reporta `cached=911` sobre `prompt=911`. Un cache por prefijo solo puede cubrir el
   prefijo repetido, nunca el mensaje entero, porque el final del prompt es contenido que
   el proveedor no vio nunca. Un hit genuino tiene que ser parcial.
3. **La anomalía aparece también donde no puede haber prefijo.** El primer turno de esa
   misma conversación es un `hola` de chequeo de conectividad, el primer mensaje de una
   conversación nueva, y reporta `cached=65` de `prompt=85`. No hay ningún turno anterior
   del que pueda venir ese prefijo.
4. **El gasto no logueado que sí existe en este repo usó otro prompt.** El smoke test de
   `openrouter.py` (documentado en el ejercicio 3) le manda a este modelo la pregunta de
   los números primos, no el prompt de Conway ni `hola`, así que no puede ser el origen de
   un prefijo cacheado para ninguno de los dos.

Lo consistente con las cuatro observaciones es que el `cached_tokens` de ese request lo
reportó mal el proveedor que atendió esa llamada, no que exista una corrida escondida.

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

### Tokens y costo por intento

Desglose turno por turno de los 3 intentos del ejercicio 2 (fuente: `logs/deepseek_deepseek-v4-flash-0731_2026091*.md`). El intento 1 incluye un turno extra (`hola`, chequeo de conectividad sin querer en la misma conversación) que se cuenta aparte porque no es parte del prompt de Conway.

| Intento | Turno | `prompt_tokens` (entrada) | `completion_tokens` (salida, incluye razonamiento) | `cached_tokens` | `reasoning_tokens` | Costo |
|---|---|---|---|---|---|---|
| 1 | `hola` (conectividad) | 85 | 37 | 65 | 22 | $0.000005 |
| 1 | prompt Conway | 911 | 9684 | 911 | 9264 | $0.000978 |
| 1 — **subtotal** | | **996** | **9721** | **976** | **9286** | **$0.000983** |
| 2 — **ganador** | prompt Conway | 813 | 1699 | 0 | 1071 | $0.000355 |
| 3 | prompt Conway | 892 | 14699 | 0 | 14356 | $0.005093 |
| **Total (3 intentos)** | | **2701** | **26119** | **976** | **24713** | **$0.006431** |

`completion_tokens` incluye los `reasoning_tokens`: por ejemplo, en el intento 2 los 1699 tokens de salida se componen de 1071 de razonamiento + 628 de código/texto de respuesta.

### Tokens de pensamiento y facturación

`deepseek/deepseek-v4-flash-0731` sí devuelve `reasoning_tokens` en los tres intentos (a diferencia de la serie *o* de OpenAI, que la consigna advierte que puede razonar sin exponerlos). Se facturan como parte de `completion_tokens`, al precio de salida del modelo ($0,12 por millón de tokens): no hay una tarifa separada para razonamiento en OpenRouter para este modelo. Esto explica por qué el intento 3 (14356 tokens de razonamiento) costó 14 veces más que el intento 2 (1071 tokens) con el mismo prompt — el gasto está dominado casi por completo por cuánto decide razonar el modelo, no por el tamaño del prompt.

### Tokens cacheados y ahorro

Ahorro real: **$0**. Como se documentó en el hallazgo del ejercicio 2, los 28 proveedores que sirven este modelo detrás de OpenRouter tienen `supports_implicit_caching: false`, así que no hay caching disponible para `deepseek/deepseek-v4-flash-0731` con el catálogo vigente al 2026-09-16, sin importar cómo se diseñe el prompt. Los 976 `cached_tokens` del intento 1 son una anomalía puntual del usage de ese request (no reproducible en los intentos 2 y 3, con el mismo prefijo estático), no un ahorro genuino — por eso no se cuenta como ahorro real.

### Gasto total en USD vs. dashboard de OpenRouter

Suma de los logs de los 3 intentos del ejercicio 2: **$0.006431**.
Suma de los logs de prueba del ejercicio 1 (`logs/`): **$0.018385**. Se descompone en los
4 logs originales, uno por modelo (**$0.013726**, dominados por el primer turno de
Anthropic, `$0.011511` sin cache — la segunda pasada del mismo contexto muestra el cache
hit del slot 2: `cached=9023` de `9088`, y el costo baja a `$0.001097`), más los 6 logs de
la medición de `effort` del slot 1 (**$0.004659**), agregados el 2026-09-17.

**Total combinado (todos los logs del repo, ejercicios 1 y 2): $0.018385 + $0.006431 =
$0.024816.**

**Gasto real de la cuenta, consultado el 2026-09-17 vía `GET /api/v1/key`
(campo `usage`, acumulado desde la creación de la key): $0.067740.**

**Diferencia sin explicar por los logs: $0.042924 (63% del gasto real de la cuenta).**

La diferencia tiene dos partes, una identificada con precisión y otra estimada.

**Parte identificada: $0.009117.** Es la investigación del `effort` del slot 1 descrita en
el ejercicio 1. Para separar señal de ruido hubo que llevar el experimento a n=8 por nivel,
y esas corridas extra se hicieron llamando a `chat()` directo en vez de pasar por la
interfaz, así que no dejaron log. El número es exacto porque se consultó `GET /api/v1/key`
antes ($0.053964) y después ($0.067740) de esa tanda: la diferencia es $0.013776, de los
cuales $0.004659 sí quedaron logueados (las 6 corridas de la tabla) y $0.009117 no.

**Parte estimada: $0.033807.** Es el resto, anterior a esta medición. La hipótesis:
`openrouter.py` tiene un bloque `if __name__ == "__main__":`
que prueba los 4 slots en vivo (3 niveles de `effort`, 2 pasadas de cache, 1 llamada con
JSON Schema, 1 a DeepSeek) — corridas reales, con costo real, pero que **no pasan por
`chat_interface.py`** y por lo tanto no generan ningún log `.md`. Cada corrida de
`python3 openrouter.py` durante el desarrollo del ejercicio 1 gastó dinero sin dejar
registro. Es consistente en magnitud: una sola llamada con `effort=high` ya costó
`$0.005093` en el ejercicio 2 (intento 3); varias corridas de ese smoke test durante el
desarrollo explican fácilmente los `$0.0338` de diferencia.

Consultado el grupo, quien armó `openrouter.py` confirma que es probable ("puede ser que
haya ejecutado antes alguna prueba"), aunque sin recordarlo con precisión, y el grupo no
tiene acceso al login del dashboard de la cuenta (solo a la API key) para verificar la
lista de requests una por una. Con esto, la hipótesis queda corroborada por la persona
mejor posicionada para saberlo, aunque sin confirmación exacta de cuántas corridas ni
cuáles.

Esto no afecta la admisibilidad del ejercicio 2 (esos 3 intentos sí tienen su log completo
y están arriba), pero sí significa que el gasto total de la cuenta no es 100% reconstruible
solo a partir de `logs/` — las llamadas que no pasan por `chat_interface.py` son la fuente
de gasto no auditable de este repo.

**La lección, que vale para las dos partes:** toda llamada que no pasa por
`chat_interface.py` gasta plata sin dejar rastro auditable, y es fácil hacerlo sin querer
— nos volvió a pasar el 2026-09-17 mientras medíamos el `effort`, ya sabiendo del problema.
Si hubiera que rehacer el TP, el cambio sería que `chat()` escriba siempre una línea de
usage en un log común, sea quien sea que la llame, de modo que la contabilidad no dependa
de acordarse de usar la interfaz.

### Conclusión

El costo del ejercicio 2 estuvo dominado por la variabilidad del razonamiento, no por el prompt: entre dos corridas del mismo prompt con `effort=high`, `reasoning_tokens` varió 13 veces (1071 vs. 14356), y el caching que la consigna esperaba demostrar no está disponible en ningún proveedor de DeepSeek detrás de OpenRouter. Para bajar el costo sin perder el "1 prompt" cambiaríamos `reasoning.effort="high"` por `reasoning.max_tokens` con un tope explícito (por ejemplo 1500, apenas por encima de lo que usó el intento ganador): eso acota el gasto máximo por corrida sin necesitar que el caching funcione, algo que no depende del diseño del prompt sino de qué proveedores expone OpenRouter para este modelo.
