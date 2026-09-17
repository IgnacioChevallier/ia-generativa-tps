# Informe — Misión: el prompt mínimo

## Trabajo previo

### 1. Qué hace un router de modelos

Decide a qué modelo mandar cada request (por costo, latencia, disponibilidad o qué anduvo
mejor en tareas parecidas) sin que quien llama elija el `model` id. El **Auto Router** de
OpenRouter (`openrouter/auto`) elige según qué usó el mercado de OpenRouter para tareas
similares en los últimos 7 días. Resuelve dos cosas: "no sé cuál modelo conviene" y el
fallback cuando un proveedor se cae.

### 2. Mapa de los 7 proveedores

Modelo insignia de cada proveedor, vía `GET /api/v1/models` y el ranking de `/discover`
(Artificial Analysis intelligence index), consultado el 2026-09-16:


| Proveedor          | Modelo insignia          | In/out (USD por millón) | Contexto  | Benchmark                                                 |
| ------------------ | ------------------------ | ----------------------- | --------- | --------------------------------------------------------- |
| OpenAI             | `gpt-6-astra`            | $10 / $50               | 1.050.000 | 53/100 — 1° (empatado)                                    |
| Anthropic          | `claude-fable-5.1`       | $10 / $50               | 1.000.000 | 53/100 — 1° (empatado); 82 en coding                      |
| Qwen               | `qwen3.8-max-0902`       | $2 / $6                 | 1.000.000 | 53/100 — 3°                                               |
| Grok (xAI)         | `grok-4.6`               | $2 / $6                 | 500.000   | 44/100 — 4°                                               |
| Gemini (Google)    | `gemini-3.8-flash`       | $0,75 / $3,75           | 1.048.576 | 41/100 — 5°                                               |
| Kimi (Moonshot AI) | `kimi-k3`                | $3 / $15                | 1.048.576 | no listado en `/discover`                                 |
| DeepSeek           | `deepseek-v4-flash-0731` | $0,06 / $0,12           | 1.310.720 | "best value": percentil 72 al precio más bajo de la tabla |


**Hallazgo.** El insignia de DeepSeek es exactamente el modelo que la consigna asigna al
slot 4 — por eso es "el escalón barato" del ejercicio 2.

### 3. Comparación de `supported_parameters`


| Parámetro                         | GPT-5.6 Luna | Claude Haiku 4.5                        | Gemini 3.7 Flash       | DeepSeek V4 Flash                                                 |
| --------------------------------- | ------------ | --------------------------------------- | ---------------------- | ----------------------------------------------------------------- |
| `reasoning_effort`                | Sí           | No (solo `max_tokens` como presupuesto) | Sí                     | Sí                                                                |
| Salidas estructuradas             | Sí           | Sí                                      | Sí                     | Sí                                                                |
| `temperature` / `top_p` / `top_k` | Ninguno      | Los tres                                | `temperature`, `top_p` | Los tres + `top_a`, `min_p`, `repetition_penalty`                 |
| `tools` / `tool_choice`           | Sí           | Sí                                      | Sí                     | Sí                                                                |
| Propios                           | `seed`       | `stop`                                  | `seed`, `stop`         | `frequency_penalty`, `presence_penalty`, `logit_bias`, `logprobs` |


**Hallazgo.** GPT-5.6 Luna solo expone perillas de razonamiento, sin sampling clásico (ni
`temperature`). DeepSeek soporta el superset más amplio de los cuatro.

---

## Ejercicio 1 — Interfaz de chat, cuatro modelos

`chat_interface.py` sobre el cliente único `openrouter.py`. Un log de prueba por modelo en
`logs/`, con rol, mensaje y usage por respuesta.

### Slot 2 — cache hit explícito (`cache_control`)

Haiku 4.5 no cachea prompts chicos (mínimo ~4096 tokens), así que la prueba manda un
`system` grande marcado con `cache_control: ephemeral`. Dos pasadas del mismo contexto:


| Pasada | `prompt_tokens` | `cached_tokens` | Costo         |
| ------ | --------------- | --------------- | ------------- |
| 1ª     | 9035            | 0               | $0.011511     |
| 2ª     | 9088            | **9023** (99%)  | **$0.001097** |


El costo de entrada baja 10×. Es el único caching que el TP pudo demostrar funcionando.

### Slot 1 — efecto del nivel de esfuerzo

`/effort` queda registrado en el log como bloque `## config`. Mismo prompt (teoría de
números), cada corrida en conversación nueva:


| Nivel     | `reasoning_tokens`            |
| --------- | ----------------------------- |
| `minimal` | 399 · 658 · 784 → mediana 658 |
| `high`    | 468 · 818 · 633 → mediana 633 |


**Hallazgo: el efecto existe pero es más chico que el ruido entre corridas idénticas.** En
esas 3+3 no se ve. Repitiendo hasta n=8 por nivel aparece la señal — `minimal` mediana 484 (rango 327–934), `high` mediana 649 (rango 468–838), ~1,3× — pero los rangos se superponen casi por completo, así que **una corrida por nivel puede dar el resultado invertido**: el primer par que corrimos dio `minimal`=934 contra `high`=516. El `effort` es una preferencia estadística, no un dial determinístico. (Las corridas de n=8 se hicieron llamando a `chat()` directo, sin log; su costo está en el ejercicio 3.)

### Slot 3 — salidas estructuradas

`/schema <json>` fija un `response_format` de tipo `json_schema`: en `logs/google_gemini-3.7-flash_20260915_204826.md` la respuesta sale como `{"primos":15}` en vez de texto libre. Ese log es anterior al cambio que registra el schema en el log.

---

## Ejercicio 2 — El target en 1 prompt

### El prompt

Diseñado con los 6 componentes de la clase, con todo salvo el input idéntico entre intento para forzar el cache por prefijo. Texto completo en `prompt_conway_intento1.txt`. Los ejemplos cubren los 5 casos clave del contrato: oscilador, naturaleza muerta, muerte por soledad, nacimiento por 3 vecinas y borde sin wrap-around (el más propenso a error, porque es donde un modelo suele asumir wrap por defecto).

Modelo: `deepseek/deepseek-v4-flash-0731`, `reasoning.effort = high` en los tres intentos.

### Los tres intentos


| Intento         | Hora  | Prompts                                                                    | Tests | `cached_tokens` | `reasoning_tokens` | Costo     |
| --------------- | ----- | -------------------------------------------------------------------------- | ----- | --------------- | ------------------ | --------- |
| 1               | 20:51 | 2 (incluye un `hola` de conectividad, sin querer en la misma conversación) | 9/9 ✅ | 65/85 → 911/911 | 22 + 9264          | $0.000983 |
| 2 — **ganador** | 21:18 | 1                                                                          | 9/9 ✅ | 0               | 1071               | $0.000355 |
| 3               | 21:23 | 1                                                                          | 9/9 ✅ | 0               | 14356              | $0.005093 |


**Ganador: intento 2** (`logs/deepseek_deepseek-v4-flash-0731_20260916_211821.md`). Un solo prompt, 9/9 tests, el más barato. `vida.py` es exactamente ese código, sin tocar a mano. Los otros dos también pasaron los 9 tests: se conservan como evidencia del comportamiento del caching, no como intentos fallidos.

### Hallazgos

**El caching automático de DeepSeek no está disponible en OpenRouter.** El prefijo estático se mandó idéntico en los tres intentos y dio `cached=0` en el 2 y el 3, incluso corriendo el 3 apenas 4 minutos después del 2 (descarta expiración). La causa está en `GET /api/v1/models/deepseek/deepseek-v4-flash-0731/endpoints`: devuelve ~28 hosts (Fireworks, DeepInfra, Together, Novita, entre otros) entre los que OpenRouter reparte sin que uno elija, y **los 28 tienen** `"supports_implicit_caching": false`. Es una limitación de infraestructura, no del diseño del prompt: con el catálogo vigente es imposible demostrar `cached_tokens > 0` de forma reproducible con este modelo.

**El `cached_tokens > 0` del intento 1 no es evidencia de corridas previas sin entregar.**
Tres observaciones lo descartan:

1. Si una corrida previa hubiera cacheado el prefijo, los intentos 2 y 3 — mismo prefijo,
  27 y 32 minutos después — habrían pegado también. Dieron 0 los dos.
2. `cached=911` sobre `prompt=911` es imposible para un cache por prefijo: el final del
  prompt es contenido nuevo, así que un hit genuino tiene que ser parcial.
3. Aparece también donde no puede haber prefijo: el `hola` inicial de esa conversación
  reporta `cached=65` de `prompt=85` siendo el primer mensaje.

Lo consistente es que ese proveedor reportó mal el `cached_tokens`, no que haya una corrida escondida.

**El razonamiento no es determinístico.** Entre los intentos 2 y 3, con el prompt idéntico
y el mismo `effort=high`, `reasoning_tokens` fue de 1071 a 14356 (13×), y el costo de $0.000355 a $0.005093 por esa sola razón. El código generado también fue distinto en cada intento, lo que confirma que no hubo respuesta reusada.

---

## Ejercicio 3 - La cuenta final

### Tokens y costo por intento


| Intento         | Turno  | Entrada  | Salida (incl. razonamiento) | `cached` | `reasoning` | Costo         |
| --------------- | ------ | -------- | --------------------------- | -------- | ----------- | ------------- |
| 1               | `hola` | 85       | 37                          | 65       | 22          | $0.000005     |
| 1               | Conway | 911      | 9684                        | 911      | 9264        | $0.000978     |
| 1 — subtotal    |        | **996**  | **9721**                    | **976**  | **9286**    | **$0.000983** |
| 2 — **ganador** | Conway | 813      | 1699                        | 0        | 1071        | $0.000355     |
| 3               | Conway | 892      | 14699                       | 0        | 14356       | $0.005093     |
| **Total**       |        | **2701** | **26119**                   | **976**  | **24713**   | **$0.006431** |


### Tokens de pensamiento y facturación

DeepSeek sí devuelve `reasoning_tokens` (a diferencia de la serie *o* de OpenAI, que la
consigna advierte que puede ocultarlos). Se facturan dentro de `completion_tokens`, al precio de salida ($0,12 por millón): no hay tarifa separada. Por eso el intento 3 costó 14 veces más que el 2 con el mismo prompt — **el gasto lo domina cuánto razona el modelo, no el tamaño del prompt**.

### Tokens cacheados y ahorro

**Ahorro real: $0.** No hay caching disponible para este modelo (ver hallazgo del ejercicio
2), así que los 976 `cached_tokens` del intento 1 son un error de reporte, no un ahorro.

### Gasto total vs. dashboard de OpenRouter


| Concepto                                                | USD                 |
| ------------------------------------------------------- | ------------------- |
| Logs del ejercicio 1 (10 archivos)                      | $0.018385           |
| Logs del ejercicio 2 (3 intentos)                       | $0.006431           |
| **Total logueado**                                      | **$0.024816**       |
| Gasto real de la cuenta (`GET /api/v1/key`, 2026-09-17) | $0.067740           |
| **Diferencia sin log**                                  | **$0.042924 (63%)** |


La diferencia son llamadas que no pasaron por `chat_interface.py` y por lo tanto no
generaron log:

- **$0.009117, medido.** Las corridas de n=8 de la medición de `effort` del slot 1, hechas
con `chat()` directo. Es exacto: se consultó `GET /api/v1/key` antes ($0.053964) y
después ($0.067740); de esos $0.013776, $0.004659 quedaron logueados y $0.009117 no.
- **$0.033807, estimado.** El resto, anterior. `openrouter.py` tiene un bloque
`if __name__ == "__main__":` que prueba los 4 slots en vivo, con costo real y sin log. Es consistente en magnitud: una sola llamada con `effort=high` costó $0.005093 en el intento 3. Quien armó ese archivo confirma que es probable haber corrido pruebas antes, sin recordar cuántas, y el grupo no tiene acceso al dashboard (solo a la API key) para verificar request por request.

Esto no afecta la admisibilidad del ejercicio 2 (sus 3 intentos tienen log completo), pero
sí significa que el gasto de la cuenta no es reconstruible solo desde `logs/`.

**La lección:** toda llamada que no pasa por la interfaz gasta sin dejar rastro, y es fácil
hacerlo sin querer — nos volvió a pasar midiendo el `effort`, ya sabiendo del problema. El
arreglo sería que `chat()` loguee siempre, sea quien sea que la llame, para que la
contabilidad no dependa de acordarse de usar la interfaz.

### Conclusión

El costo lo dominó la variabilidad del razonamiento, no el prompt: 13× entre dos corridas
idénticas con `effort=high`. El caching que la consigna esperaba demostrar no está
disponible en ningún proveedor de DeepSeek detrás de OpenRouter, así que no es una perilla
que podamos tocar. Para bajar el costo sin perder el "1 prompt" cambiaríamos
`reasoning.effort="high"` por `reasoning.max_tokens=1500` (apenas por encima de lo que usó
el ganador): acota el gasto máximo por corrida sin depender de que el caching funcione.