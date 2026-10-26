# Informe — El agente de admisión de guardia

Estado: **Partes 1 y 2 hechas y medidas. Partes 3, 4 y 5 pendientes** (necesitan GPU en Modal, el repositorio de Hugging
Face y W&B del grupo; ver el final). Cada número dice qué comando lo produce. Todo se corre desde `tp-final/` con
`uv sync` y `uv run ...`.

## Parte 1: curado e ingeniería de datos

### 1.1 El oráculo de la ficha

El kit no trae un cálculo de la ficha correcta: `admision.comparar` solo compara contra fichas esperadas ya dadas. Para
clasificar el historial hacía falta calcularla, así que se escribió `curado/oraculo.py`, que aplica las normas
NOR-ADM, NOR-COB y NOR-TDE con los parámetros de la carpeta de normas que recibe, más las dos costumbres de 1.3.

Se validó contra las 150 fichas esperadas de la cátedra (50 casos de práctica con las normas original, b y c, los 8 campos
más la verificación): **150 de 150**. `uv run python -m curado.validar_oraculo`.

La primera versión, sin ninguna costumbre, coincidía en 31 de los 50 casos en cada versión de normas. De los 19 que
fallaban, 14 eran el aviso al voluntariado (de ahí salió la costumbre 1) y 5 un error mío: en los accidentes de trabajo la
lista de entidades que no se deben verificar salía con la misma entidad repetida.

### 1.2 Clasificación del historial

`uv run python -m curado.clasificar` escribe `historial_clasificado.csv` (id,tipo), `curado/detalle_clasificacion.jsonl`
(los motivos de cada fila) y `curado/resumen_clasificacion.json`.

Criterio. *Error*: la ficha viola una norma escrita, comparada con la del oráculo con las normas originales. *Ruido*: no
viola ninguna, pero se aparta de una costumbre (hace algo que las normas no cubren y que no es lo que hacen casi todos).
*Correcta*: las demás. Si una fila tiene ambas cosas es error.

| tipo | filas |
|---|---|
| correcta | 1.600 (80 %) |
| ruido | 160 (8 %) |
| error | 240 (12 %) |

Los errores son cuatro normas escritas. Cada fila errónea tiene exactamente un error. "Expuestas" son las filas donde la
norma aplicaba:

| norma violada | qué hizo el operador | filas expuestas | con error | tasa |
|---|---|---|---|---|
| NOR-TDE-04 | llegó en ambulancia y no restó los minutos de P-TDE-5 al plazo del circuito | 487 | 97 | 19,9 % |
| NOR-ADM-03 | pasaporte o cédula en nivel urgente y registro definitivo en vez de provisorio | 271 | 64 | 23,6 % |
| NOR-ADM-02 | paciente mayor (edad ≥ P-ADM-2, nivel menos urgente) sin ubicar en el box antes del registro | 278 | 61 | 21,9 % |
| NOR-COB-04 | número de afiliado con la terminación reservada y no se lo registró sin cobertura (o no se notificó la afiliación inactiva) | 144 | 18 | 12,5 % |

Los errores no son de ningún operador: cada uno de los 20 comete entre 7 y 18. En cambio el **ruido** es de tres
operadores, OP-04 (39 filas), OP-11 (64) y OP-17 (57), y de nadie más. Que el 80/8/12 salga redondo y que cada fila
errónea tenga un solo error es una señal de que la clasificación recupera la verdadera, pero no es una prueba: no
tenemos la clasificación de la cátedra.

Se descartó una hipótesis: que los errores fueran de operadores puntuales (como el ruido). Se repartían parejo.

### 1.3 Las costumbres

Se detallan en `costumbres.md`, que genera `uv run python -m curado.costumbres` midiendo cada número desde el historial.
Son dos, y las dos las siguen exactamente los mismos 17 operadores:

1. **Aviso al voluntariado: se avisa si y solo si el paciente tiene 75 años o más y no tiene acompañante.** Ninguna
   norma menciona al voluntariado. Los 17 operadores que la siguen no tienen una sola excepción en 1.674 filas (185
   avisos). El umbral se midió probando todas las edades: 74 años, 0 de 13 avisos; 75 años, 8 de 8. No cambia con las
   normas: las fichas esperadas de práctica tienen el mismo aviso en las tres versiones.
2. **Con dos credenciales (obra social y prepaga) vale la prepaga.** NOR-COB-01 §4 no dice cuál. Los 17 operadores
   verificaron la prepaga en todas sus filas, sin importar el orden ni cuál estuviera activa. Los casos de práctica
   coinciden (los 5 con dos credenciales).

OP-04, OP-11 y OP-17 rompen las dos: avisan al voluntariado en el 47 % de sus filas sin relación con la edad ni el
acompañante, y en 9 filas verificaron la obra social. De ahí salen las 160 filas de ruido (151 de voluntariado y 9 de
credenciales). `curado/resumen_clasificacion.json`.

### 1.4 Conversaciones de entrenamiento

`uv run python -m curado.generar_datos` genera, con semilla fija, las trayectorias y las conversaciones.

Un experto (`curado/trayectorias.py`) juega cada caso contra el `Entorno` de la cátedra y el buscador del grupo. La ficha
la calcula el oráculo con los parámetros de la versión de normas que se juega, y `admision.comparar` confirma que
resuelve los 9 controles. Las observaciones son las reales, incluidas las búsquedas: el modelo ve el texto que va a ver en
producción y aprende a leer de ahí los números (`P-ADM-2 = 67 años`), no a memorizarlos. El experto busca solo los
números que necesita para cada caso (entre 1 y 5 búsquedas, 2,7 de media), con varias formulaciones por necesidad, y descarta la
trayectoria si el buscador no trae el número.

| archivo | contenido |
|---|---|
| `datos/trayectorias_reales.jsonl` | 1.600 filas `correcta` del historial, jugadas con las normas originales |
| `datos/trayectorias_sinteticas.jsonl` | 4.000 casos del generador de la cátedra: 500 por versión de normas (original, b, c y cinco versiones inventadas, `datos/versiones_sinteticas.json`) |
| `datos/conversaciones_*.jsonl` | las mismas trayectorias como mensajes de chat, con el mensaje de sistema y el formato del agente de ejemplo |
| `datos/resumen_generacion.json` | cuentas y descartes: **0 descartes** |
| `datos/SHA256SUMS` | hash de cada archivo |

- **Qué filas sirven.** Solo las 1.600 correctas. Las 240 con error y las 160 con ruido no se usan: se podrían reparar con
  el oráculo, pero preferimos que lo que el modelo imita sea lo que hizo un operador sin error ni apartarse de la
  costumbre. Los casos raros (terminación reservada, ambulancia, pasaporte urgente) los cubren los sintéticos.
- **Sintéticas.** Entrenar con varias versiones de las normas, y no solo con las tres de práctica, es lo que enseña a leer
  números que el modelo no vio: la cátedra evalúa con otros. Los casos generados que coinciden con alguno de los 50 de
  práctica se descartan (ninguno coincidió), así que la práctica sigue sirviendo para evaluar.
- **Tamaño.** 6,1 pasos por caso. Una conversación ocupa unos 1.600 tokens (4 caracteres por token): el 34-35 % es el
  mensaje de sistema y el 38-39 % son textos de búsquedas (`composicion` en `datos/resumen_generacion.json`). Esos son los
  dos lugares donde se puede ahorrar en las Partes 2 y 3.
- **Reproducibilidad.** La generación es determinista (dos corridas dieron los mismos bytes), así que en git van los
  hashes y no los 65 MB: `uv run python -m curado.generar_datos && (cd datos && sha256sum -c SHA256SUMS)`.
- **Prueba de que alcanza con lo que trae el buscador.** `tests/test_trayectorias.py`: el experto resuelve los 150 juegos
  de práctica (50 casos × 3 versiones) contra el entorno real. Es una cota superior de lo que puede hacer un agente que
  use este buscador; no dice nada de lo que va a hacer el modelo.

Las conversaciones que se entrenen en la Parte 4 se volverán a armar desde las trayectorias con el prompt optimizado de la
Parte 3; las de `datos/conversaciones_*.jsonl` usan el prompt del agente de ejemplo.

## Parte 2: buscador propio

`buscador.py`. Cada **párrafo (§)** de las normas es un fragmento, con el código y título de su sección al principio y,
al final, la línea `Valores:` con los parámetros que cita ese párrafo, leídos de `parametros.yaml` de la carpeta que
recibe (nunca hay números de las normas en el código). Se busca con BM25 propio sobre el texto del fragmento más una
paráfrasis coloquial que se indexa pero no se devuelve (`buscador_expansiones.json`, 81 líneas, una por párrafo).

La evaluación oficial, antes de empezar el agente:

```bash
uv run python -m admision.evaluar_rag --entrega entrega.py --normas normas/original --consultas rag/consultas_dev.jsonl
```

| buscador | k | recall de evidencia | precisión | tokens por consulta | consultas completas |
|---|---|---|---|---|---|
| **referencia de la cátedra** (BM25, sección entera) | 2 | 0,875 | 0,492 | 580 | 51 de 60 |
| **el nuestro** | 3 | **0,892** | 0,333 | **242** | 51 de 60 |
| el nuestro | 2 | 0,858 | 0,467 | 171 | 49 de 60 |
| el nuestro | 4 | 0,933 | 0,267 | 331 | 55 de 60 |

Con el mismo recall que la referencia, trae 2,4 veces menos tokens (k=3), o 3,4 veces menos con un recall apenas menor
(k=2). Por tipo de consulta, con k=3: directas 1,00, numéricas 1,00, distractoras 1,00, coloquiales 0,67, dos secciones
0,69 (`experimentos/rag/evaluar_rag_dev.json`). Con presupuesto fijo de tokens: 256 → 0,883, 512 → 0,967, 1024 → 0,983.

### Qué se probó y qué no funcionó

`uv run python -m experimentos.rag_grilla` (dev) y `... --consultas datos/consultas_propias.jsonl --salida
experimentos/rag/grilla_propias.json` (propias). Recall de evidencia / tokens por consulta:

| variante | dev (60) | propias (41) |
|---|---|---|
| sección entera, k=2 (nuestra copia de la referencia) | 0,792 / 594 | 0,854 / 583 |
| sección entera + raíz de palabras | 0,792 / 594 | 0,829 / 581 |
| párrafo, k=3, sin expansiones | 0,700 / 258 | 0,780 / 247 |
| párrafo, k=4, sin expansiones | 0,750 / 344 | 0,805 / 336 |
| **párrafo + expansiones, k=3** | **0,892 / 242** | **0,902 / 243** |
| párrafo + expansiones, k=2 | 0,858 / 171 | 0,902 / 170 |
| párrafo + expansiones, k=4 | 0,933 / 331 | 0,951 / 330 |

- **Partir por párrafo solo no alcanza.** Baja los tokens a la mitad pero también el recall (0,79 → 0,70): las consultas
  coloquiales no comparten palabras con las normas ("se agarra el pecho" contra "dolor torácico": el párrafo correcto
  estaba en el puesto 70).
- **Reducir las palabras a su raíz no ayudó** (0,792 igual, y 0,829 contra 0,854 en las propias).
- **Las expansiones son lo que mejora**: +0,19 de recall. Son paráfrasis de cada párrafo con el vocabulario de una oficina
  de admisión (dolor de pecho, derrame cerebral, dado de baja, albañil, etc.), escritas con un modelo de lenguaje, y se
  indexan sin devolverse. Es generación de datos, no un servicio en operación.
- **Ajustar BM25 no sirvió**: una grilla de k1 ∈ {0,9; 1,2; 1,5; 2,0} y b ∈ {0,3; 0,5; 0,75; 0,9} movió el recall en una o
  dos consultas (`experimentos/rag/ajuste_bm25.json`). Es ruido; se dejaron los valores estándar (1,2 y 0,75).

**Cuidado con las 60 consultas de desarrollo:** las expansiones se escribieron *después* de ver qué consultas fallaban, así
que 0,892 es optimista. Por eso se armó un conjunto propio de 41 consultas nuevas (`experimentos/consultas_propias.py`:
estilo de agente, coloquiales, numéricas y de otras áreas, con evidencia verificada literal contra las normas). Ahí da
0,902 con los mismos k, o sea que las expansiones generalizan. Es un conjunto chico y escrito por quien escribió las
expansiones: no es independiente del todo.

### Lo que no hay que malinterpretar

- **Con las normas b y c el recall de la evaluación oficial baja a 0,708. No es un defecto del buscador.** Las 12 consultas
  numéricas piden como evidencia el texto literal `P-ADM-2 = 67 años`, que es el valor de las normas originales; con b o c
  el texto correcto dice `60 años`. Se comprobó que el buscador **trae exactamente los mismos tres fragmentos en el
  mismo orden con las tres versiones** en las 101 consultas (60 de desarrollo y 41 propias;
  `tests/test_buscador.py`). Por eso se reporta la evaluación solo con `normas/original`, como indica el manual.
- **Lo que falla.** Coloquiales de "sin cobertura" ("¿le pido plata a quien no tiene obra social?") pierden contra párrafos
  que dicen "obra social o prepaga" en general, y las consultas de dos secciones traen solo una cuando las dos están en
  áreas distintas. Un agente que busque con las palabras de las normas, o que haga dos búsquedas, lo evita.

### Cuánto rinde el agente con este buscador

**Pendiente**: hace falta el modelo (Parte 3 en adelante). Lo que sí está medido es la cota superior de 1.4 (el experto con
este buscador resuelve 150 de 150). `k_entorno = 3` es provisorio: cuántos fragmentos trae cada búsqueda se vuelve a
decidir con el agente funcionando.

## Partes 3, 4 y 5

Pendientes. Lo que ya está listo para ellas: las trayectorias (de las que sale cualquier formato de conversación), las
versiones de normas sintéticas para entrenar y para optimizar el prompt, el buscador y el entorno de evaluación
(`admision.correr`). Lo que falta y no se puede hacer desde esta máquina: una A100 en Modal, el repositorio de Hugging
Face del grupo y el proyecto de W&B.
