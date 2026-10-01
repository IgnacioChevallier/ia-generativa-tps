# Informe: RAG, MCP y Transformers en el Hospital Arroyo Claro

## Cómo correr la entrega

El repositorio de GitHub reúne varios TPs de la materia, uno por carpeta. La raíz de esta entrega es `rag-mcp-transformers/`: todos los comandos del enunciado se corren desde esa carpeta, donde están `datos/`, `api/`, `evaluar/` y `atencion/` tal como los entregó la cátedra.

```bash
cd rag-mcp-transformers
python3 recuperar.py --preguntas datos/preguntas_recuperacion_dev.jsonl --salida resultados.jsonl
python3 evaluar/evaluar.py recuperacion --preguntas datos/preguntas_recuperacion_dev.jsonl --resultados resultados.jsonl
python3 atencion/test_atencion.py atencion.py
```



## Parte 1: RAG vectorial



### Configuración entregada


| Encoder                                                                               | Chunking                                       | Metadatos                       | Selección                                  | Context relevance (dev)                                 |
| ------------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------- | ------------------------------------------ | ------------------------------------------------------- |
| `BAAI/bge-m3`                                                                         | una sección `##` por fragmento (56 fragmentos) | título del documento antepuesto | top-3 con margen 0,01 respecto del primero | **1,000** (recall 1,000, precision 1,000, k medio 1,00) |
| Línea de base: `google-bert/bert-base-multilingual-cased`, promedio de la última capa | igual                                          | igual                           | top-1                                      | 0,300                                                   |


Queda fija en `CONFIG` de `recuperar.py`: el comando de la consigna la usa sin argumentos.
La evaluación de esta fila es [experimentos/bge-sec-k3-m0.01.jsonl.eval.json](experimentos/bge-sec-k3-m0.01.jsonl.eval.json)
y coincide con [resultados.jsonl.eval.json](resultados.jsonl.eval.json), la corrida del comando oficial.

### Cómo se experimentó

`experimentos/correr.py` recorre la grilla y, por cada configuración, deja en `experimentos/`
su `.config.json` (reproducible con `python3 recuperar.py --config ...`), los fragmentos
devueltos (`.jsonl`) y la evaluación de `evaluar/evaluar.py` sin modificar (`.jsonl.eval.json`).
Se probaron 120 configuraciones; la tabla completa está en el [anexo](#anexo-tabla-completa-de-experimentos-de-la-parte-1).
La evaluación de recuperación no usa LLM, así que la grilla no tuvo costo en OpenRouter.

Ejes:

1. **Encoder** (5): BERT multilingüe sin ajustar con promedio de los vectores de la última capa
  (línea de base obligatoria), `paraphrase-multilingual-MiniLM-L12-v2`, `multilingual-e5-small`,
   `multilingual-e5-base` (ambos con `query:`  / `passage:` ) y `bge-m3`.
2. **Chunking** (4): por sección `##`, por párrafo, y ventanas de 60/20 y 120/40 palabras.
3. **Metadatos**: con y sin título (y sección, en párrafo) antepuesto.
4. **Selección**: top-k fijo (1, 2, 3, 5), top-3 con umbral absoluto de coseno y top-3 con
  margen respecto del mejor (0,005 a 0,05).



### Resultados por eje

**Encoder y chunking** (con metadatos y top-1; context relevance):


| Encoder                     | Sección   | Párrafo | Ventana 60/20 | Ventana 120/40 |
| --------------------------- | --------- | ------- | ------------- | -------------- |
| BERT multilingüe (promedio) | 0,300     | 0,300   | 0,200         | 0,250          |
| MiniLM-L12                  | 0,800     | 0,850   | 0,750         | 0,700          |
| e5-small                    | 0,900     | 0,850   | 0,800         | 0,950          |
| e5-base                     | **1,000** | 0,950   | 0,800         | 0,900          |
| bge-m3                      | **1,000** | 0,950   | 0,800         | 0,900          |


- Cualquier encoder entrenado para similitud le gana por más del doble a BERT. BERT promediado
queda incluso por debajo del recuperador léxico ingenuo de la consigna (0,35).
- Cortar por sección es lo mejor para los encoders buenos. Cada sección del corpus trata un
solo tema (una modalidad de visita, un estudio, un tipo de turno), así que es la unidad
natural de la respuesta. Las ventanas de 60 palabras cortan en medio de una sección y dejan
fragmentos que mezclan dos temas o que pierden el contexto que desambigua: son la peor opción
para todos. El párrafo solo le conviene a MiniLM (0,85 contra 0,80), el encoder más chico.
No es por truncamiento: su límite de 128 tokens recorta solo 1 de las 56 secciones.

**Metadatos** (top-1; con → sin título antepuesto):


| Encoder  | Sección       | Párrafo       |
| -------- | ------------- | ------------- |
| BERT     | 0,300 → 0,200 | 0,300 → 0,250 |
| MiniLM   | 0,800 → 0,800 | 0,850 → 0,750 |
| e5-small | 0,900 → 0,850 | 0,850 → 0,800 |
| e5-base  | 1,000 → 0,950 | 0,950 → 0,800 |
| bge-m3   | 1,000 → 1,000 | 0,950 → 0,900 |


El título nunca empeora y ayuda más cuanto más chico es el fragmento. Un párrafo como "Una
persona por vez" no dice de qué servicio habla, y el título del documento se lo agrega.
bge-m3 por sección es el único que no lo necesita: acierta las 20 igual. Con el chunking por
sección, el encabezado `##` siempre queda dentro del fragmento, y a bge-m3 eso le alcanza para
ubicar el tema, aunque a los demás encoders no.

**Top-k, umbral y margen** (sección, con metadatos):


| Encoder | k=1   | k=2   | k=3   | umbral (2 valores) | margen 0,005 | margen 0,01 | margen 0,02 | margen 0,05 |
| ------- | ----- | ----- | ----- | ------------------ | ------------ | ----------- | ----------- | ----------- |
| MiniLM  | 0,800 | 0,667 | 0,500 | 0,700 / 0,767      | 0,833        | 0,817       | 0,850       | 0,850       |
| e5-base | 1,000 | 0,667 | 0,500 | 0,858 / 0,983      | 0,967        | 0,942       | 0,875       | 0,692       |
| bge-m3  | 1,000 | 0,667 | 0,500 | 0,617 / 0,850      | **1,000**    | **1,000**   | 0,983       | 0,908       |


(umbrales: MiniLM y bge-m3 0,50 / 0,60; e5-base 0,85 / 0,88.)

- En este corpus cada pregunta tiene su evidencia en un solo fragmento, así que un k fijo
mayor a 1 castiga la precisión de forma mecánica: si el correcto está entre los devueltos,
el techo es 2/(1+k), es decir 0,667 con k=2 y 0,5 con k=3. Con los encoders buenos el recall con
k=2 ya es 1,0, así que el problema nunca es encontrar la evidencia, sino no traer de más.
- **El umbral absoluto no sirve para esto.** El coseno del fragmento correcto varía mucho
entre preguntas (con bge-m3 va de 0,55 a 0,77), así que cualquier corte fijo deja pasar
fragmentos de más en preguntas "fáciles" o no aporta nada en las difíciles. Además, cada
encoder tiene su propia escala: e5 amontona todos los cosenos entre 0,73 y 0,93, y bge-m3
los reparte entre 0,23 y 0,77. Un umbral que sirve para uno no sirve para otro.
- **El margen relativo al primero sí sirve.** Agrega un segundo fragmento solo cuando empata
casi exacto con el mejor, que es justo cuando el top-1 es una apuesta.



### Por qué bge-m3 y no e5-base

e5-base y bge-m3 empatan en 1,000 con top-1. Con 20 preguntas, ese empate no alcanza para
decidir. Lo que los separa es **cuánto le gana el fragmento correcto al mejor incorrecto**
(sección, con metadatos):


| Encoder         | Aciertos top-1 | Rango de cosenos | Diferencia mediana correcto − mejor incorrecto | Diferencia mínima entre las acertadas | Preguntas con diferencia < 0,01 |
| --------------- | -------------- | ---------------- | ---------------------------------------------- | ------------------------------------- | ------------------------------- |
| BERT (promedio) | 6/20           | 0,41 – 0,74      | −0,019                                         | 0,009                                 | 1                               |
| MiniLM          | 16/20          | −0,15 – 0,77     | +0,104                                         | 0,010                                 | 2                               |
| e5-small        | 18/20          | 0,74 – 0,93      | +0,033                                         | 0,003                                 | 5                               |
| e5-base         | 20/20          | 0,73 – 0,91      | +0,033                                         | 0,000                                 | 3                               |
| **bge-m3**      | **20/20**      | 0,23 – 0,77      | **+0,110**                                     | **0,015**                             | **0**                           |


- **e5-base acierta las 20 por muy poco.** En R01 ("terapia intensiva al mediodía") el
correcto le gana a la sección de Pediatría del mismo documento por menos de 0,001; en R15
por 0,002 y en R02 (endoscopía alta contra colonoscopía) por 0,005. Con preguntas nuevas, varias de esas van a caer del lado equivocado.
- **bge-m3 separa al correcto por 0,11 de mediana**, tres veces más que e5-base, y la
diferencia más chica es 0,015 (R02, endoscopía contra colonoscopía, que son secciones
vecinas del mismo documento). Como no hay casi empates en dev, el margen 0,01 no se activa en
ninguna pregunta (k medio 1,00). En el conjunto de test cubre justo los casos ambiguos,
donde devolver dos fragmentos (0,667) rinde más en promedio que jugarse a uno (1 o 0).
- **BERT sin ajustar no sirve como recuperador.** Con el promedio de los vectores de la
última capa, el fragmento correcto ni siquiera le gana en mediana al mejor incorrecto
(−0,019), y acierta 6 de 20. El modelo se entrenó para predecir palabras enmascaradas, no
para que una pregunta y el pasaje que la responde queden cerca. Nada en su entrenamiento
hace que el promedio de sus vectores ordene los textos por significado. MiniLM, e5 y bge-m3
se entrenaron con pares de textos relacionados (aprendizaje contrastivo; e5 y bge-m3, con
pares pregunta–pasaje), que es exactamente esta tarea.
- **Por qué bge-m3 separa mejor que e5:** es un modelo más grande (568M de parámetros contra
278M de e5-base) y se entrenó específicamente para recuperación multilingüe, con pasajes
largos (hasta 8192 tokens). En la práctica, su escala de coseno es más ancha, así que las
diferencias entre fragmentos son más grandes.

Costo de la elección: bge-m3 pesa unos 2,2 GB y tarda unos 5 s en CPU en indexar el corpus y
responder las 20 preguntas. Para 56 fragmentos es irrelevante.

### Riesgo de sobreajuste

Todas las decisiones se tomaron con las 20 preguntas `dev`. Para no elegir la fila con el
número más alto por azar:

- Entre las configuraciones empatadas en 1,000 se eligió la de **mayor separación**, que
es la que menos depende de las preguntas puntuales.
- El chunking por sección y los metadatos no se eligieron con ajustes finos, sino por la
estructura del corpus, y rinden parecido en los cinco encoders.
- El margen 0,01 no mejora el número de dev (da lo mismo que top-1). Se eligió como seguro
para el test, apenas por debajo de la separación mínima observada (0,015).

Esperamos que el resultado en test sea algo menor que 1,000, por la cantidad chica de
preguntas. La separación de bge-m3 sugiere que la caída va a ser menor que con cualquier
otro encoder de la tabla.

### Qué no se probó

El reranking con cross-encoder (opcional en la consigna). Con recall 1,0 en top-2 y la
configuración elegida ya en 1,000, un reranker solo podría cambiar el orden entre los dos
primeros, que es lo que ya cubre el margen. Queda como mejora si el test muestra errores de
orden.

## Parte 2: agente con dos fuentes



### Cómo está hecho

- `hospital.py` define las seis herramientas como funciones de Python (`buscar_documentos`,
`consultar_camas`, `consultar_guardia`, `consultar_turnos`, `consultar_farmacia`,
`consultar_espera`). `buscar_documentos` llama a `recuperar.buscar` (la configuración
ganadora de la parte 1) y las demás hacen `GET` a la API del hospital. Quedan en un módulo
aparte, sin LangChain, para que el servidor MCP de la parte 3 use exactamente las mismas.
- `agente.py` envuelve cada función como tool de LangChain (`StructuredTool.from_function`, así
el docstring pasa a ser la descripción) y arma el agente con `create_agent` sobre
`ChatOpenAI(model="deepseek/deepseek-v4-flash-0731", base_url="https://openrouter.ai/api/v1", temperature=0)`. Pide `usage.include` para que OpenRouter devuelva el costo real de cada llamada.
- Las descripciones dicen para qué preguntas sirve cada herramienta **y para cuáles no** (por
ejemplo, `consultar_turnos` aclara que no dice qué documentos llevar). El prompt de sistema
fija cuatro reglas: llamar siempre a una herramienta antes de contestar; en las preguntas
mixtas llamar a la de la API y también a `buscar_documentos`; contestar solo con lo que
devolvieron las herramientas; y si una herramienta devuelve error con opciones válidas,
corregir el argumento. Las herramientas devuelven los errores de la API como texto (con la
lista de opciones), no como excepción, para que el modelo se corrija solo.
- Tests propios sin LLM en `tests/test_hospital.py` (contra la API real, levantada en el test) y
`tests/test_agente.py` (armado del registro y del log).



### Resultados en `dev` (12 preguntas)

Corrida: [logs/agente_20260930_111531.md](logs/agente_20260930_111531.md) ·
respuestas: [respuestas.jsonl](respuestas.jsonl) ·
evaluación: [respuestas.jsonl.eval.json](respuestas.jsonl.eval.json).


| Ruteo    | Context relevance | Answer faithfulness | Answer relevance | Costo del agente | Costo del juez |
| -------- | ----------------- | ------------------- | ---------------- | ---------------- | -------------- |
| **1,00** | **5,00**          | **5,00**            | **5,00**         | USD 0,0012       | USD 0,0163     |


El agente usó exactamente las herramientas esperadas en las 12 preguntas: una sola en las de
documentos y en las de API, y las dos en A10, A11 y A12. Una corrida completa son 24 llamadas al
modelo (dos por pregunta: elegir herramientas y redactar) con 39.196 tokens de entrada y 2.225 de
salida en total. La mayor parte de la entrada es el prompt de sistema y las descripciones de las
herramientas que se reenvían en cada llamada.

Se corrió el benchmark una sola vez con el agente final: no hubo iteraciones de prompt, porque la
primera versión ya llegó al techo del juez. Eso también significa que el prompt **no está
tuneado a las preguntas** `dev`: no contiene ninguna de ellas ni sus respuestas.

### Análisis de las preguntas donde el agente falló

En la corrida final no hubo ninguna pregunta con nota menor a 5 ni con ruteo incompleto, así que
no hay un fallo del agente que analizar. Lo que sí hay son tres cosas que observamos en los logs
y que pueden aparecer en el conjunto de test:

1. **Fallo de infraestructura, no del agente (corrida de prueba con A05 y A10).**
  [logs/agente_20260930_111305.md](logs/agente_20260930_111305.md) es una prueba de humo con dos
   preguntas. A05 salió bien, pero A10 quedó vacía (sin herramientas ni respuesta): la descarga de
   `bge-m3` desde HuggingFace falló por un error de certificado SSL en la computadora donde se
   corrió, y la excepción se registró como `ERROR` en el log en lugar de tirar abajo toda la
   corrida. Se arregló usando el almacén de certificados de Windows (`truststore`); no cambia el
   código entregado.
2. **A09 (espera en la guardia).** La referencia dice que 135 minutos superan el máximo de 2
  horas del triage verde, pero el agente solo llamó a `consultar_espera` y respondió "135
   minutos". El juez le dio 5 porque la pregunta era solo cuánto se espera, pero es el caso más
   propenso a bajar en test: si la pregunta pide comparar con la norma, hace falta también
   `buscar_documentos`. La descripción de `consultar_espera` ya lo sugiere, pero el prompt no lo
   exige.
3. **Detalle de más (A04, A12).** El agente agregó datos correctos que la pregunta no pedía
  (intervalos entre donaciones y tatuajes en A04; ubicación y horario de la farmacia en A12).
   Están respaldados por los contextos, así que no bajan la fidelidad, pero una respuesta más
   larga tiene más chances de incluir una afirmación que el juez no encuentre en el contexto.



### Límites de esta medición

- Son 12 preguntas y una sola corrida con `temperature=0`; no medimos la variación entre
corridas.
- El juez es un solo modelo con un prompt fijo, y con 5 en las tres métricas no puede
distinguir mejoras. La diferencia real entre variantes tendría que verse en el conjunto de
test, que no tenemos.
- La calidad de `buscar_documentos` depende de la parte 1: con `top_k=3` y margen 0,01 el
recuperador devolvió un solo fragmento en seis de las siete búsquedas de esta corrida y dos en
A10 (la sección "Acompañante" de internación programada y la de pediatría del régimen de visitas).



### Costo de la parte 2

Agente: USD 0,0012 (corrida final) + USD 0,0001 (prueba de humo). Juez: USD 0,0163 según el
propio `evaluar.py`. Las cifras salen de los logs y del `.eval.json`. Ojo para el cierre: las
llamadas del agente se hicieron con la clave personal de un integrante y las del juez con la
clave del grupo, así que el dashboard de actividad de OpenRouter va a mostrar el gasto repartido
en dos cuentas; hay que sumar las dos para contrastar con el total de los logs.

## Parte 3: servidor MCP



### Cómo está hecho

- `servidor_mcp.py` expone las seis herramientas de `hospital.py` con FastMCP del SDK
oficial `mcp` (stdio, sin LangChain): `mcp.tool()(f)` aplicado a cada función de
`hospital.HERRAMIENTAS`, equivalente a decorarlas ahí mismo pero sin repetir sus firmas.
El servidor no tiene código propio para la API ni el recuperador; todo sale de
`hospital.py`, el mismo módulo que usa `agente.py` en la parte 2.
- `agente_mcp.py` es el cliente: descubre las herramientas con `tools/list` y las llama
con `tools/call` vía `langchain-mcp-adapters` (`MultiServerMCPClient`, transporte
stdio), con el mismo modelo, prompt y formato de log que `agente.py` — reutilizados de
ahí (`from agente import ...`) para no duplicar esa lógica. `agente_mcp.py` no tiene
ningún código propio para consultar la API ni el recuperador.



### Un bug de Windows que vale la pena documentar

La primera corrida se colgaba sin error en la primera llamada a `buscar_documentos`,
indefinidamente y con 0% de uso de CPU (se descartó que fuera una descarga lenta: el
encoder ya estaba cacheado y no había ninguna actividad de red o disco). Aislado paso a
paso (probando `recuperar.buscar()` fuera de MCP, después con el cliente oficial `mcp` sin
LangChain, después con `langchain-mcp-adapters`): el cuelgue ocurría en los tres casos
exactamente en el primer import de `sentence_transformers`/`torch` dentro del proceso del
servidor. FastMCP despacha cada herramienta en un hilo del executor, no en el hilo
principal, y en Windows el primer import de una librería con extensiones de C pesadas
(torch) desde un hilo secundario puede quedar en deadlock contra el *loader lock* del
sistema — un problema conocido de CPython en Windows, no un bug de `recuperar.py` ni de
`langchain-mcp-adapters`.

**La solución:** `servidor_mcp.py` precarga el encoder (`recuperar.buscar("precarga")`) en
el hilo principal, antes de `mcp.run()`. Así el import pesado ocurre donde es seguro, y
para cuando llega la primera request ya está resuelto. Esto agrega ~20-30 segundos al
arranque de cada sesión del servidor (ver el costo más abajo), pero sin esto la parte 3
no corre en Windows.

### Verificación con MCP Inspector

Conectado con `npx @modelcontextprotocol/inspector`, sin ningún LLM de por medio, se
llamó a las seis herramientas una por una contra la API real. Capturas en
[experimentos/inspector/](experimentos/inspector/): `01_consultar_espera.jpg`,
`02_buscar_documentos.jpg`, `03_consultar_camas.jpg`, `04_consultar_guardia.jpg`,
`05_consultar_turnos.jpg`, `06_consultar_farmacia.jpg`. Las seis devolvieron datos reales
de la API/recuperador, confirmando que el servidor funciona con un cliente MCP genérico y
no solo con `agente_mcp.py`.

### Resultados en `dev` (12 preguntas) y comparación con la parte 2

Corrida: [logs/agente_mcp_20260930_153140.md](logs/agente_mcp_20260930_153140.md) ·
respuestas: [respuestas_mcp.jsonl](respuestas_mcp.jsonl) ·
evaluación: [respuestas_mcp.jsonl.eval.json](respuestas_mcp.jsonl.eval.json).


|                             | Ruteo    | Context relevance | Faithfulness | Answer relevance | Costo del agente | Costo del juez |
| --------------------------- | -------- | ----------------- | ------------ | ---------------- | ---------------- | -------------- |
| Parte 2 (LangChain directo) | 1,00     | 5,00              | 5,00         | 5,00             | USD 0,0012       | USD 0,0163     |
| Parte 3 (servidor MCP)      | **1,00** | **5,00**          | **5,00**     | **5,00**         | **USD 0,003235** | USD 0,01856    |


Las cuatro métricas del juez son **idénticas** a la parte 2: mismo modelo, mismo prompt,
mismas 12 preguntas, y las herramientas hacen exactamente lo mismo de un lado que del
otro (son las mismas funciones de `hospital.py`), así que no hay razón para que cambien, y
no cambiaron.

**El costo del agente sí cambió: 2,7 veces más caro** (USD 0,003235 contra USD 0,0012).
La razón está en los logs, no en el modelo ni el prompt: `langchain-mcp-adapters` abre
**una sesión MCP nueva por cada llamada a una herramienta** (lo documenta su propio
`get_tools()`: *"A new session will be created for each tool call"*). Cada sesión nueva es
un proceso de Python nuevo que tiene que reimportar `sentence_transformers`/`torch` y, en
las preguntas que usan `buscar_documentos`, recargar el encoder de la parte 1 — el mismo
costo de arranque que pagó la parte 2 **una sola vez** al iniciar el proceso, la parte 3 lo
paga de nuevo en cada pregunta que toca documentos. El costo del juez (que no depende de
la arquitectura del agente, sino de las 12 llamadas al juez sobre el mismo contenido) da
prácticamente igual en ambas partes, como es de esperar.

**Esto es un costo de la arquitectura MCP tal como la exige la consigna (servidor por
stdio, sesión nueva por llamada), no de una implementación de menor calidad**: con un
transporte persistente (por ejemplo streamable-http con un servidor de larga vida) el
costo por llamada bajaría al nivel de la parte 2, porque el encoder se cargaría una sola
vez para toda la corrida en lugar de una vez por pregunta.

## Parte 5: un bloque de transformer a mano

La resolución del punto 5 está disponible en [a_mano/respuestas.pdf](a_mano/respuestas.pdf).

## Costo total de la misión

Costos con impacto real en OpenRouter (la parte 1 y la parte 4 corren embeddings y NumPy
en CPU local, sin llamadas a la API):


| Origen                                           | Agente                                                          | Juez        | Total            |
| ------------------------------------------------ | --------------------------------------------------------------- | ----------- | ---------------- |
| Parte 2                                          | USD 0,0013 (0,0012 corrida final + 0,0001 prueba de humo)       | USD 0,01627 | USD 0,01757      |
| Parte 3                                          | USD 0,003402 (0,003235 corrida final + 0,000167 prueba de humo) | USD 0,01856 | USD 0,022122     |
| **Total (documentado en los logs de este repo)** |                                                                 |             | **USD 0,039692** |




### Contra el dashboard de OpenRouter

Consultado el 2026-09-30 vía `GET /api/v1/key` (la cuenta compartida del grupo):

- **Gasto de hoy** (`usage_daily`, el día en que se corrieron las partes 2 y 3): **USD
0,038642**.
- **Gasto total acumulado de la key** (`usage`, desde que se creó): USD 0,109724.

**El gasto de hoy (USD 0,038642) cierra razonablemente contra el total documentado (USD
0,039692): una diferencia de USD 0,00105 (2,6%)**, coherente con que ambas partes 2 y 3
se corrieron el mismo día. La diferencia probablemente sale de llamadas de desarrollo que
no quedaron en ningún log entregado (por ejemplo, alguna iteración exploratoria del agente
antes de la corrida final).

**El acumulado total (USD 0,109724) no se puede reconciliar completo contra esta misión**,
por dos razones que conviene dejar explícitas:

1. **Esta key se comparte entre TPs de la materia**: el mismo grupo la usó también para
  la misión de prompting (`prompting/`), cuyo propio informe ya documentó un gasto total
   de esa cuenta de USD 0,053963798 al 2026-09-17 — trece días antes de esta entrega, fuera
   de la ventana de "hoy" o incluso de los últimos 7 días que muestra la API.
2. **La parte 2 se desarrolló con dos claves distintas**: según su propia sección de
  costo más arriba, el agente corrió con la clave personal de un integrante y el juez
   con la de esta cuenta del grupo. El gasto del agente de la parte 2 documentado en la
   tabla (USD 0,0013) sale de sus logs, no de esta key — así que no está incluido en el
   `usage` que devuelve esta consulta, y no hay forma de verificarlo por API sin esa otra
   clave.

**Conclusión de la reconciliación:** el gasto de un día puntual (hoy) cierra con margen
razonable; el acumulado histórico de la cuenta no, porque mide más gasto que el de esta
misión (arrastra la otra materia) y menos (le falta una clave personal usada en la parte
2). Para una reconciliación exacta haría falta que **una sola clave** cubra toda la
misión, o sumar manualmente el gasto de cada clave usada.

## Anexo: tabla completa de experimentos de la parte 1

Generada por `experimentos/correr.py` (también en [experimentos/tabla.md](experimentos/tabla.md)).
Cada fila enlaza a su `.eval.json`.


| Experimento                                                                 | Encoder                                 | Chunking       | Metadatos | top-k | Umbral / margen | Context relevance | Recall | Precision | k medio | MRR   |
| --------------------------------------------------------------------------- | --------------------------------------- | -------------- | --------- | ----- | --------------- | ----------------- | ------ | --------- | ------- | ----- |
| [bert-sec-k1](experimentos/bert-sec-k1.jsonl.eval.json)                     | bert-base-multilingual-cased (promedio) | seccion        | sí        | 1     | —               | **0.300**         | 0.300  | 0.300     | 1.00    | 0.300 |
| [bert-par-k1](experimentos/bert-par-k1.jsonl.eval.json)                     | bert-base-multilingual-cased (promedio) | parrafo        | sí        | 1     | —               | **0.300**         | 0.300  | 0.300     | 1.00    | 0.300 |
| [bert-v60-k1](experimentos/bert-v60-k1.jsonl.eval.json)                     | bert-base-multilingual-cased (promedio) | ventana 60/20  | sí        | 1     | —               | **0.200**         | 0.200  | 0.200     | 1.00    | 0.200 |
| [bert-v120-k1](experimentos/bert-v120-k1.jsonl.eval.json)                   | bert-base-multilingual-cased (promedio) | ventana 120/40 | sí        | 1     | —               | **0.250**         | 0.250  | 0.250     | 1.00    | 0.250 |
| [minilm-sec-k1](experimentos/minilm-sec-k1.jsonl.eval.json)                 | paraphrase-multilingual-MiniLM-L12-v2   | seccion        | sí        | 1     | —               | **0.800**         | 0.800  | 0.800     | 1.00    | 0.800 |
| [minilm-par-k1](experimentos/minilm-par-k1.jsonl.eval.json)                 | paraphrase-multilingual-MiniLM-L12-v2   | parrafo        | sí        | 1     | —               | **0.850**         | 0.850  | 0.850     | 1.00    | 0.850 |
| [minilm-v60-k1](experimentos/minilm-v60-k1.jsonl.eval.json)                 | paraphrase-multilingual-MiniLM-L12-v2   | ventana 60/20  | sí        | 1     | —               | **0.750**         | 0.750  | 0.750     | 1.00    | 0.750 |
| [minilm-v120-k1](experimentos/minilm-v120-k1.jsonl.eval.json)               | paraphrase-multilingual-MiniLM-L12-v2   | ventana 120/40 | sí        | 1     | —               | **0.700**         | 0.700  | 0.700     | 1.00    | 0.700 |
| [e5s-sec-k1](experimentos/e5s-sec-k1.jsonl.eval.json)                       | multilingual-e5-small                   | seccion        | sí        | 1     | —               | **0.900**         | 0.900  | 0.900     | 1.00    | 0.900 |
| [e5s-par-k1](experimentos/e5s-par-k1.jsonl.eval.json)                       | multilingual-e5-small                   | parrafo        | sí        | 1     | —               | **0.850**         | 0.850  | 0.850     | 1.00    | 0.850 |
| [e5s-v60-k1](experimentos/e5s-v60-k1.jsonl.eval.json)                       | multilingual-e5-small                   | ventana 60/20  | sí        | 1     | —               | **0.800**         | 0.800  | 0.800     | 1.00    | 0.800 |
| [e5s-v120-k1](experimentos/e5s-v120-k1.jsonl.eval.json)                     | multilingual-e5-small                   | ventana 120/40 | sí        | 1     | —               | **0.950**         | 0.950  | 0.950     | 1.00    | 0.950 |
| [e5b-sec-k1](experimentos/e5b-sec-k1.jsonl.eval.json)                       | multilingual-e5-base                    | seccion        | sí        | 1     | —               | **1.000**         | 1.000  | 1.000     | 1.00    | 1.000 |
| [e5b-par-k1](experimentos/e5b-par-k1.jsonl.eval.json)                       | multilingual-e5-base                    | parrafo        | sí        | 1     | —               | **0.950**         | 0.950  | 0.950     | 1.00    | 0.950 |
| [e5b-v60-k1](experimentos/e5b-v60-k1.jsonl.eval.json)                       | multilingual-e5-base                    | ventana 60/20  | sí        | 1     | —               | **0.800**         | 0.800  | 0.800     | 1.00    | 0.800 |
| [e5b-v120-k1](experimentos/e5b-v120-k1.jsonl.eval.json)                     | multilingual-e5-base                    | ventana 120/40 | sí        | 1     | —               | **0.900**         | 0.900  | 0.900     | 1.00    | 0.900 |
| [bge-sec-k1](experimentos/bge-sec-k1.jsonl.eval.json)                       | bge-m3                                  | seccion        | sí        | 1     | —               | **1.000**         | 1.000  | 1.000     | 1.00    | 1.000 |
| [bge-par-k1](experimentos/bge-par-k1.jsonl.eval.json)                       | bge-m3                                  | parrafo        | sí        | 1     | —               | **0.950**         | 0.950  | 0.950     | 1.00    | 0.950 |
| [bge-v60-k1](experimentos/bge-v60-k1.jsonl.eval.json)                       | bge-m3                                  | ventana 60/20  | sí        | 1     | —               | **0.800**         | 0.800  | 0.800     | 1.00    | 0.800 |
| [bge-v120-k1](experimentos/bge-v120-k1.jsonl.eval.json)                     | bge-m3                                  | ventana 120/40 | sí        | 1     | —               | **0.900**         | 0.900  | 0.900     | 1.00    | 0.900 |
| [bert-sec-sinmeta-k1](experimentos/bert-sec-sinmeta-k1.jsonl.eval.json)     | bert-base-multilingual-cased (promedio) | seccion        | no        | 1     | —               | **0.200**         | 0.200  | 0.200     | 1.00    | 0.200 |
| [bert-par-sinmeta-k1](experimentos/bert-par-sinmeta-k1.jsonl.eval.json)     | bert-base-multilingual-cased (promedio) | parrafo        | no        | 1     | —               | **0.250**         | 0.250  | 0.250     | 1.00    | 0.250 |
| [minilm-sec-sinmeta-k1](experimentos/minilm-sec-sinmeta-k1.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2   | seccion        | no        | 1     | —               | **0.800**         | 0.800  | 0.800     | 1.00    | 0.800 |
| [minilm-par-sinmeta-k1](experimentos/minilm-par-sinmeta-k1.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2   | parrafo        | no        | 1     | —               | **0.750**         | 0.750  | 0.750     | 1.00    | 0.750 |
| [e5s-sec-sinmeta-k1](experimentos/e5s-sec-sinmeta-k1.jsonl.eval.json)       | multilingual-e5-small                   | seccion        | no        | 1     | —               | **0.850**         | 0.850  | 0.850     | 1.00    | 0.850 |
| [e5s-par-sinmeta-k1](experimentos/e5s-par-sinmeta-k1.jsonl.eval.json)       | multilingual-e5-small                   | parrafo        | no        | 1     | —               | **0.800**         | 0.800  | 0.800     | 1.00    | 0.800 |
| [e5b-sec-sinmeta-k1](experimentos/e5b-sec-sinmeta-k1.jsonl.eval.json)       | multilingual-e5-base                    | seccion        | no        | 1     | —               | **0.950**         | 0.950  | 0.950     | 1.00    | 0.950 |
| [e5b-par-sinmeta-k1](experimentos/e5b-par-sinmeta-k1.jsonl.eval.json)       | multilingual-e5-base                    | parrafo        | no        | 1     | —               | **0.800**         | 0.800  | 0.800     | 1.00    | 0.800 |
| [bge-sec-sinmeta-k1](experimentos/bge-sec-sinmeta-k1.jsonl.eval.json)       | bge-m3                                  | seccion        | no        | 1     | —               | **1.000**         | 1.000  | 1.000     | 1.00    | 1.000 |
| [bge-par-sinmeta-k1](experimentos/bge-par-sinmeta-k1.jsonl.eval.json)       | bge-m3                                  | parrafo        | no        | 1     | —               | **0.900**         | 0.900  | 0.900     | 1.00    | 0.900 |
| [bert-sec-k2](experimentos/bert-sec-k2.jsonl.eval.json)                     | bert-base-multilingual-cased (promedio) | seccion        | sí        | 2     | —               | **0.233**         | 0.350  | 0.175     | 2.00    | 0.325 |
| [bert-sec-k3](experimentos/bert-sec-k3.jsonl.eval.json)                     | bert-base-multilingual-cased (promedio) | seccion        | sí        | 3     | —               | **0.200**         | 0.400  | 0.133     | 3.00    | 0.342 |
| [bert-sec-k5](experimentos/bert-sec-k5.jsonl.eval.json)                     | bert-base-multilingual-cased (promedio) | seccion        | sí        | 5     | —               | **0.167**         | 0.500  | 0.100     | 5.00    | 0.362 |
| [bert-sec-k3-u0.85](experimentos/bert-sec-k3-u0.85.jsonl.eval.json)         | bert-base-multilingual-cased (promedio) | seccion        | sí        | 3     | coseno ≥ 0.85   | **0.300**         | 0.300  | 0.300     | 1.00    | 0.300 |
| [bert-sec-k3-u0.90](experimentos/bert-sec-k3-u0.90.jsonl.eval.json)         | bert-base-multilingual-cased (promedio) | seccion        | sí        | 3     | coseno ≥ 0.9    | **0.300**         | 0.300  | 0.300     | 1.00    | 0.300 |
| [bert-sec-k3-m0.005](experimentos/bert-sec-k3-m0.005.jsonl.eval.json)       | bert-base-multilingual-cased (promedio) | seccion        | sí        | 3     | margen 0.005    | **0.300**         | 0.300  | 0.300     | 1.45    | 0.300 |
| [bert-sec-k3-m0.01](experimentos/bert-sec-k3-m0.01.jsonl.eval.json)         | bert-base-multilingual-cased (promedio) | seccion        | sí        | 3     | margen 0.01     | **0.283**         | 0.300  | 0.275     | 1.85    | 0.300 |
| [bert-sec-k3-m0.02](experimentos/bert-sec-k3-m0.02.jsonl.eval.json)         | bert-base-multilingual-cased (promedio) | seccion        | sí        | 3     | margen 0.02     | **0.317**         | 0.400  | 0.283     | 2.35    | 0.342 |
| [bert-sec-k3-m0.05](experimentos/bert-sec-k3-m0.05.jsonl.eval.json)         | bert-base-multilingual-cased (promedio) | seccion        | sí        | 3     | margen 0.05     | **0.250**         | 0.400  | 0.200     | 2.80    | 0.342 |
| [bert-par-k2](experimentos/bert-par-k2.jsonl.eval.json)                     | bert-base-multilingual-cased (promedio) | parrafo        | sí        | 2     | —               | **0.233**         | 0.350  | 0.175     | 2.00    | 0.325 |
| [bert-par-k3](experimentos/bert-par-k3.jsonl.eval.json)                     | bert-base-multilingual-cased (promedio) | parrafo        | sí        | 3     | —               | **0.200**         | 0.400  | 0.133     | 3.00    | 0.342 |
| [bert-par-k5](experimentos/bert-par-k5.jsonl.eval.json)                     | bert-base-multilingual-cased (promedio) | parrafo        | sí        | 5     | —               | **0.167**         | 0.500  | 0.100     | 5.00    | 0.367 |
| [bert-par-k3-u0.85](experimentos/bert-par-k3-u0.85.jsonl.eval.json)         | bert-base-multilingual-cased (promedio) | parrafo        | sí        | 3     | coseno ≥ 0.85   | **0.300**         | 0.300  | 0.300     | 1.00    | 0.300 |
| [bert-par-k3-u0.90](experimentos/bert-par-k3-u0.90.jsonl.eval.json)         | bert-base-multilingual-cased (promedio) | parrafo        | sí        | 3     | coseno ≥ 0.9    | **0.300**         | 0.300  | 0.300     | 1.00    | 0.300 |
| [bert-par-k3-m0.005](experimentos/bert-par-k3-m0.005.jsonl.eval.json)       | bert-base-multilingual-cased (promedio) | parrafo        | sí        | 3     | margen 0.005    | **0.300**         | 0.300  | 0.300     | 1.20    | 0.300 |
| [bert-par-k3-m0.01](experimentos/bert-par-k3-m0.01.jsonl.eval.json)         | bert-base-multilingual-cased (promedio) | parrafo        | sí        | 3     | margen 0.01     | **0.283**         | 0.300  | 0.275     | 1.65    | 0.300 |
| [bert-par-k3-m0.02](experimentos/bert-par-k3-m0.02.jsonl.eval.json)         | bert-base-multilingual-cased (promedio) | parrafo        | sí        | 3     | margen 0.02     | **0.300**         | 0.400  | 0.258     | 2.20    | 0.342 |
| [bert-par-k3-m0.05](experimentos/bert-par-k3-m0.05.jsonl.eval.json)         | bert-base-multilingual-cased (promedio) | parrafo        | sí        | 3     | margen 0.05     | **0.225**         | 0.400  | 0.167     | 2.90    | 0.342 |
| [minilm-sec-k2](experimentos/minilm-sec-k2.jsonl.eval.json)                 | paraphrase-multilingual-MiniLM-L12-v2   | seccion        | sí        | 2     | —               | **0.667**         | 1.000  | 0.500     | 2.00    | 0.900 |
| [minilm-sec-k3](experimentos/minilm-sec-k3.jsonl.eval.json)                 | paraphrase-multilingual-MiniLM-L12-v2   | seccion        | sí        | 3     | —               | **0.500**         | 1.000  | 0.333     | 3.00    | 0.900 |
| [minilm-sec-k5](experimentos/minilm-sec-k5.jsonl.eval.json)                 | paraphrase-multilingual-MiniLM-L12-v2   | seccion        | sí        | 5     | —               | **0.333**         | 1.000  | 0.200     | 5.00    | 0.900 |
| [minilm-sec-k3-u0.50](experimentos/minilm-sec-k3-u0.50.jsonl.eval.json)     | paraphrase-multilingual-MiniLM-L12-v2   | seccion        | sí        | 3     | coseno ≥ 0.5    | **0.700**         | 0.900  | 0.625     | 1.75    | 0.850 |
| [minilm-sec-k3-u0.60](experimentos/minilm-sec-k3-u0.60.jsonl.eval.json)     | paraphrase-multilingual-MiniLM-L12-v2   | seccion        | sí        | 3     | coseno ≥ 0.6    | **0.767**         | 0.850  | 0.733     | 1.30    | 0.825 |
| [minilm-sec-k3-m0.005](experimentos/minilm-sec-k3-m0.005.jsonl.eval.json)   | paraphrase-multilingual-MiniLM-L12-v2   | seccion        | sí        | 3     | margen 0.005    | **0.833**         | 0.850  | 0.825     | 1.05    | 0.825 |
| [minilm-sec-k3-m0.01](experimentos/minilm-sec-k3-m0.01.jsonl.eval.json)     | paraphrase-multilingual-MiniLM-L12-v2   | seccion        | sí        | 3     | margen 0.01     | **0.817**         | 0.850  | 0.800     | 1.10    | 0.825 |
| [minilm-sec-k3-m0.02](experimentos/minilm-sec-k3-m0.02.jsonl.eval.json)     | paraphrase-multilingual-MiniLM-L12-v2   | seccion        | sí        | 3     | margen 0.02     | **0.850**         | 0.900  | 0.825     | 1.15    | 0.850 |
| [minilm-sec-k3-m0.05](experimentos/minilm-sec-k3-m0.05.jsonl.eval.json)     | paraphrase-multilingual-MiniLM-L12-v2   | seccion        | sí        | 3     | margen 0.05     | **0.850**         | 0.950  | 0.808     | 1.35    | 0.875 |
| [minilm-par-k2](experimentos/minilm-par-k2.jsonl.eval.json)                 | paraphrase-multilingual-MiniLM-L12-v2   | parrafo        | sí        | 2     | —               | **0.667**         | 1.000  | 0.500     | 2.00    | 0.925 |
| [minilm-par-k3](experimentos/minilm-par-k3.jsonl.eval.json)                 | paraphrase-multilingual-MiniLM-L12-v2   | parrafo        | sí        | 3     | —               | **0.500**         | 1.000  | 0.333     | 3.00    | 0.925 |
| [minilm-par-k5](experimentos/minilm-par-k5.jsonl.eval.json)                 | paraphrase-multilingual-MiniLM-L12-v2   | parrafo        | sí        | 5     | —               | **0.333**         | 1.000  | 0.200     | 5.00    | 0.925 |
| [minilm-par-k3-u0.50](experimentos/minilm-par-k3-u0.50.jsonl.eval.json)     | paraphrase-multilingual-MiniLM-L12-v2   | parrafo        | sí        | 3     | coseno ≥ 0.5    | **0.750**         | 0.950  | 0.675     | 1.75    | 0.900 |
| [minilm-par-k3-u0.60](experimentos/minilm-par-k3-u0.60.jsonl.eval.json)     | paraphrase-multilingual-MiniLM-L12-v2   | parrafo        | sí        | 3     | coseno ≥ 0.6    | **0.817**         | 0.900  | 0.783     | 1.30    | 0.875 |
| [minilm-par-k3-m0.005](experimentos/minilm-par-k3-m0.005.jsonl.eval.json)   | paraphrase-multilingual-MiniLM-L12-v2   | parrafo        | sí        | 3     | margen 0.005    | **0.883**         | 0.900  | 0.875     | 1.05    | 0.875 |
| [minilm-par-k3-m0.01](experimentos/minilm-par-k3-m0.01.jsonl.eval.json)     | paraphrase-multilingual-MiniLM-L12-v2   | parrafo        | sí        | 3     | margen 0.01     | **0.867**         | 0.900  | 0.850     | 1.10    | 0.875 |
| [minilm-par-k3-m0.02](experimentos/minilm-par-k3-m0.02.jsonl.eval.json)     | paraphrase-multilingual-MiniLM-L12-v2   | parrafo        | sí        | 3     | margen 0.02     | **0.867**         | 0.900  | 0.850     | 1.10    | 0.875 |
| [minilm-par-k3-m0.05](experimentos/minilm-par-k3-m0.05.jsonl.eval.json)     | paraphrase-multilingual-MiniLM-L12-v2   | parrafo        | sí        | 3     | margen 0.05     | **0.817**         | 0.950  | 0.758     | 1.45    | 0.900 |
| [e5s-sec-k2](experimentos/e5s-sec-k2.jsonl.eval.json)                       | multilingual-e5-small                   | seccion        | sí        | 2     | —               | **0.633**         | 0.950  | 0.475     | 2.00    | 0.925 |
| [e5s-sec-k3](experimentos/e5s-sec-k3.jsonl.eval.json)                       | multilingual-e5-small                   | seccion        | sí        | 3     | —               | **0.500**         | 1.000  | 0.333     | 3.00    | 0.942 |
| [e5s-sec-k5](experimentos/e5s-sec-k5.jsonl.eval.json)                       | multilingual-e5-small                   | seccion        | sí        | 5     | —               | **0.333**         | 1.000  | 0.200     | 5.00    | 0.942 |
| [e5s-sec-k3-u0.85](experimentos/e5s-sec-k3-u0.85.jsonl.eval.json)           | multilingual-e5-small                   | seccion        | sí        | 3     | coseno ≥ 0.85   | **0.750**         | 1.000  | 0.650     | 1.90    | 0.942 |
| [e5s-sec-k3-u0.88](experimentos/e5s-sec-k3-u0.88.jsonl.eval.json)           | multilingual-e5-small                   | seccion        | sí        | 3     | coseno ≥ 0.88   | **0.933**         | 0.950  | 0.925     | 1.05    | 0.925 |
| [e5s-sec-k3-m0.005](experimentos/e5s-sec-k3-m0.005.jsonl.eval.json)         | multilingual-e5-small                   | seccion        | sí        | 3     | margen 0.005    | **0.908**         | 0.950  | 0.892     | 1.15    | 0.925 |
| [e5s-sec-k3-m0.01](experimentos/e5s-sec-k3-m0.01.jsonl.eval.json)           | multilingual-e5-small                   | seccion        | sí        | 3     | margen 0.01     | **0.892**         | 1.000  | 0.850     | 1.40    | 0.942 |
| [e5s-sec-k3-m0.02](experimentos/e5s-sec-k3-m0.02.jsonl.eval.json)           | multilingual-e5-small                   | seccion        | sí        | 3     | margen 0.02     | **0.850**         | 1.000  | 0.792     | 1.55    | 0.942 |
| [e5s-sec-k3-m0.05](experimentos/e5s-sec-k3-m0.05.jsonl.eval.json)           | multilingual-e5-small                   | seccion        | sí        | 3     | margen 0.05     | **0.683**         | 1.000  | 0.575     | 2.25    | 0.942 |
| [e5s-par-k2](experimentos/e5s-par-k2.jsonl.eval.json)                       | multilingual-e5-small                   | parrafo        | sí        | 2     | —               | **0.600**         | 0.900  | 0.450     | 2.00    | 0.875 |
| [e5s-par-k3](experimentos/e5s-par-k3.jsonl.eval.json)                       | multilingual-e5-small                   | parrafo        | sí        | 3     | —               | **0.500**         | 1.000  | 0.333     | 3.00    | 0.908 |
| [e5s-par-k5](experimentos/e5s-par-k5.jsonl.eval.json)                       | multilingual-e5-small                   | parrafo        | sí        | 5     | —               | **0.333**         | 1.000  | 0.200     | 5.00    | 0.908 |
| [e5s-par-k3-u0.85](experimentos/e5s-par-k3-u0.85.jsonl.eval.json)           | multilingual-e5-small                   | parrafo        | sí        | 3     | coseno ≥ 0.85   | **0.717**         | 1.000  | 0.608     | 2.05    | 0.908 |
| [e5s-par-k3-u0.88](experimentos/e5s-par-k3-u0.88.jsonl.eval.json)           | multilingual-e5-small                   | parrafo        | sí        | 3     | coseno ≥ 0.88   | **0.908**         | 0.950  | 0.892     | 1.15    | 0.892 |
| [e5s-par-k3-m0.005](experimentos/e5s-par-k3-m0.005.jsonl.eval.json)         | multilingual-e5-small                   | parrafo        | sí        | 3     | margen 0.005    | **0.858**         | 0.900  | 0.842     | 1.15    | 0.875 |
| [e5s-par-k3-m0.01](experimentos/e5s-par-k3-m0.01.jsonl.eval.json)           | multilingual-e5-small                   | parrafo        | sí        | 3     | margen 0.01     | **0.867**         | 1.000  | 0.817     | 1.50    | 0.908 |
| [e5s-par-k3-m0.02](experimentos/e5s-par-k3-m0.02.jsonl.eval.json)           | multilingual-e5-small                   | parrafo        | sí        | 3     | margen 0.02     | **0.817**         | 1.000  | 0.750     | 1.70    | 0.908 |
| [e5s-par-k3-m0.05](experimentos/e5s-par-k3-m0.05.jsonl.eval.json)           | multilingual-e5-small                   | parrafo        | sí        | 3     | margen 0.05     | **0.650**         | 1.000  | 0.525     | 2.35    | 0.908 |
| [e5b-sec-k2](experimentos/e5b-sec-k2.jsonl.eval.json)                       | multilingual-e5-base                    | seccion        | sí        | 2     | —               | **0.667**         | 1.000  | 0.500     | 2.00    | 1.000 |
| [e5b-sec-k3](experimentos/e5b-sec-k3.jsonl.eval.json)                       | multilingual-e5-base                    | seccion        | sí        | 3     | —               | **0.500**         | 1.000  | 0.333     | 3.00    | 1.000 |
| [e5b-sec-k5](experimentos/e5b-sec-k5.jsonl.eval.json)                       | multilingual-e5-base                    | seccion        | sí        | 5     | —               | **0.333**         | 1.000  | 0.200     | 5.00    | 1.000 |
| [e5b-sec-k3-u0.85](experimentos/e5b-sec-k3-u0.85.jsonl.eval.json)           | multilingual-e5-base                    | seccion        | sí        | 3     | coseno ≥ 0.85   | **0.858**         | 1.000  | 0.800     | 1.50    | 1.000 |
| [e5b-sec-k3-u0.88](experimentos/e5b-sec-k3-u0.88.jsonl.eval.json)           | multilingual-e5-base                    | seccion        | sí        | 3     | coseno ≥ 0.88   | **0.983**         | 1.000  | 0.975     | 1.05    | 1.000 |
| [e5b-sec-k3-m0.005](experimentos/e5b-sec-k3-m0.005.jsonl.eval.json)         | multilingual-e5-base                    | seccion        | sí        | 3     | margen 0.005    | **0.967**         | 1.000  | 0.950     | 1.10    | 1.000 |
| [e5b-sec-k3-m0.01](experimentos/e5b-sec-k3-m0.01.jsonl.eval.json)           | multilingual-e5-base                    | seccion        | sí        | 3     | margen 0.01     | **0.942**         | 1.000  | 0.917     | 1.20    | 1.000 |
| [e5b-sec-k3-m0.02](experimentos/e5b-sec-k3-m0.02.jsonl.eval.json)           | multilingual-e5-base                    | seccion        | sí        | 3     | margen 0.02     | **0.875**         | 1.000  | 0.825     | 1.45    | 1.000 |
| [e5b-sec-k3-m0.05](experimentos/e5b-sec-k3-m0.05.jsonl.eval.json)           | multilingual-e5-base                    | seccion        | sí        | 3     | margen 0.05     | **0.692**         | 1.000  | 0.583     | 2.20    | 1.000 |
| [e5b-par-k2](experimentos/e5b-par-k2.jsonl.eval.json)                       | multilingual-e5-base                    | parrafo        | sí        | 2     | —               | **0.633**         | 0.950  | 0.475     | 2.00    | 0.950 |
| [e5b-par-k3](experimentos/e5b-par-k3.jsonl.eval.json)                       | multilingual-e5-base                    | parrafo        | sí        | 3     | —               | **0.500**         | 1.000  | 0.333     | 3.00    | 0.967 |
| [e5b-par-k5](experimentos/e5b-par-k5.jsonl.eval.json)                       | multilingual-e5-base                    | parrafo        | sí        | 5     | —               | **0.333**         | 1.000  | 0.200     | 5.00    | 0.967 |
| [e5b-par-k3-u0.85](experimentos/e5b-par-k3-u0.85.jsonl.eval.json)           | multilingual-e5-base                    | parrafo        | sí        | 3     | coseno ≥ 0.85   | **0.825**         | 1.000  | 0.750     | 1.60    | 0.967 |
| [e5b-par-k3-u0.88](experimentos/e5b-par-k3-u0.88.jsonl.eval.json)           | multilingual-e5-base                    | parrafo        | sí        | 3     | coseno ≥ 0.88   | **0.933**         | 0.950  | 0.925     | 1.05    | 0.950 |
| [e5b-par-k3-m0.005](experimentos/e5b-par-k3-m0.005.jsonl.eval.json)         | multilingual-e5-base                    | parrafo        | sí        | 3     | margen 0.005    | **0.933**         | 0.950  | 0.925     | 1.05    | 0.950 |
| [e5b-par-k3-m0.01](experimentos/e5b-par-k3-m0.01.jsonl.eval.json)           | multilingual-e5-base                    | parrafo        | sí        | 3     | margen 0.01     | **0.933**         | 1.000  | 0.908     | 1.25    | 0.967 |
| [e5b-par-k3-m0.02](experimentos/e5b-par-k3-m0.02.jsonl.eval.json)           | multilingual-e5-base                    | parrafo        | sí        | 3     | margen 0.02     | **0.875**         | 1.000  | 0.825     | 1.45    | 0.967 |
| [e5b-par-k3-m0.05](experimentos/e5b-par-k3-m0.05.jsonl.eval.json)           | multilingual-e5-base                    | parrafo        | sí        | 3     | margen 0.05     | **0.642**         | 1.000  | 0.517     | 2.40    | 0.967 |
| [bge-sec-k2](experimentos/bge-sec-k2.jsonl.eval.json)                       | bge-m3                                  | seccion        | sí        | 2     | —               | **0.667**         | 1.000  | 0.500     | 2.00    | 1.000 |
| [bge-sec-k3](experimentos/bge-sec-k3.jsonl.eval.json)                       | bge-m3                                  | seccion        | sí        | 3     | —               | **0.500**         | 1.000  | 0.333     | 3.00    | 1.000 |
| [bge-sec-k5](experimentos/bge-sec-k5.jsonl.eval.json)                       | bge-m3                                  | seccion        | sí        | 5     | —               | **0.333**         | 1.000  | 0.200     | 5.00    | 1.000 |
| [bge-sec-k3-u0.50](experimentos/bge-sec-k3-u0.50.jsonl.eval.json)           | bge-m3                                  | seccion        | sí        | 3     | coseno ≥ 0.5    | **0.617**         | 1.000  | 0.475     | 2.45    | 1.000 |
| [bge-sec-k3-u0.60](experimentos/bge-sec-k3-u0.60.jsonl.eval.json)           | bge-m3                                  | seccion        | sí        | 3     | coseno ≥ 0.6    | **0.850**         | 1.000  | 0.800     | 1.60    | 1.000 |
| [bge-sec-k3-m0.005](experimentos/bge-sec-k3-m0.005.jsonl.eval.json)         | bge-m3                                  | seccion        | sí        | 3     | margen 0.005    | **1.000**         | 1.000  | 1.000     | 1.00    | 1.000 |
| [bge-sec-k3-m0.01](experimentos/bge-sec-k3-m0.01.jsonl.eval.json)           | bge-m3                                  | seccion        | sí        | 3     | margen 0.01     | **1.000**         | 1.000  | 1.000     | 1.00    | 1.000 |
| [bge-sec-k3-m0.02](experimentos/bge-sec-k3-m0.02.jsonl.eval.json)           | bge-m3                                  | seccion        | sí        | 3     | margen 0.02     | **0.983**         | 1.000  | 0.975     | 1.05    | 1.000 |
| [bge-sec-k3-m0.05](experimentos/bge-sec-k3-m0.05.jsonl.eval.json)           | bge-m3                                  | seccion        | sí        | 3     | margen 0.05     | **0.908**         | 1.000  | 0.867     | 1.30    | 1.000 |
| [bge-par-k2](experimentos/bge-par-k2.jsonl.eval.json)                       | bge-m3                                  | parrafo        | sí        | 2     | —               | **0.667**         | 1.000  | 0.500     | 2.00    | 0.975 |
| [bge-par-k3](experimentos/bge-par-k3.jsonl.eval.json)                       | bge-m3                                  | parrafo        | sí        | 3     | —               | **0.500**         | 1.000  | 0.333     | 3.00    | 0.975 |
| [bge-par-k5](experimentos/bge-par-k5.jsonl.eval.json)                       | bge-m3                                  | parrafo        | sí        | 5     | —               | **0.333**         | 1.000  | 0.200     | 5.00    | 0.975 |
| [bge-par-k3-u0.50](experimentos/bge-par-k3-u0.50.jsonl.eval.json)           | bge-m3                                  | parrafo        | sí        | 3     | coseno ≥ 0.5    | **0.592**         | 1.000  | 0.442     | 2.55    | 0.975 |
| [bge-par-k3-u0.60](experimentos/bge-par-k3-u0.60.jsonl.eval.json)           | bge-m3                                  | parrafo        | sí        | 3     | coseno ≥ 0.6    | **0.808**         | 1.000  | 0.742     | 1.75    | 0.975 |
| [bge-par-k3-m0.005](experimentos/bge-par-k3-m0.005.jsonl.eval.json)         | bge-m3                                  | parrafo        | sí        | 3     | margen 0.005    | **0.950**         | 0.950  | 0.950     | 1.00    | 0.950 |
| [bge-par-k3-m0.01](experimentos/bge-par-k3-m0.01.jsonl.eval.json)           | bge-m3                                  | parrafo        | sí        | 3     | margen 0.01     | **0.950**         | 0.950  | 0.950     | 1.00    | 0.950 |
| [bge-par-k3-m0.02](experimentos/bge-par-k3-m0.02.jsonl.eval.json)           | bge-m3                                  | parrafo        | sí        | 3     | margen 0.02     | **0.933**         | 0.950  | 0.925     | 1.05    | 0.950 |
| [bge-par-k3-m0.05](experimentos/bge-par-k3-m0.05.jsonl.eval.json)           | bge-m3                                  | parrafo        | sí        | 3     | margen 0.05     | **0.875**         | 0.950  | 0.842     | 1.25    | 0.950 |

