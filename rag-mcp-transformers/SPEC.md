# SPEC.md

Qué se construyó, concretamente. La consigna completa está en
[task/mission.md](task/mission.md); esto describe la implementación.

## Parte 1: `recuperar.py` — recuperador vectorial

### Contrato

```bash
python3 recuperar.py --preguntas datos/preguntas_recuperacion_dev.jsonl --salida resultados.jsonl
```

- Una línea por pregunta: `{"id": ..., "fragmentos": [...]}`, en orden de relevancia.
- Sin `--config`, usa la configuración ganadora (`CONFIG` en `recuperar.py`). Con
  `--config archivo.json`, pisa las claves que traiga el archivo (solo para experimentos).
- Todo corre en CPU y sin red una vez descargados los modelos.

### Configuración

| Clave | Valores | Qué hace |
|---|---|---|
| `encoder` | id de Hugging Face | Modelo que calcula los embeddings |
| `pooling` | `"st"` \| `"mean"` | `st`: el pooling que trae el modelo de sentence-transformers. `mean`: promedio de los vectores de la última capa (la línea de base BERT) |
| `prefijo_pregunta`, `prefijo_fragmento` | texto | Para e5: `"query: "` y `"passage: "` |
| `chunking` | `"seccion"` \| `"parrafo"` \| `"ventana"` | Un fragmento por sección `##`, por párrafo, o ventanas de palabras |
| `tamano`, `solapamiento` | enteros (palabras) | Solo para `ventana` |
| `metadatos` | bool | Anteponer el título del documento (y la sección en `parrafo`) al fragmento |
| `top_k` | entero ≥ 1 | Máximo de fragmentos a devolver |
| `umbral` | coseno | Descarta fragmentos con similitud menor |
| `margen` | coseno o `null` | Descarta fragmentos a más de `margen` de la similitud del primero |

### Reglas

- **Los fragmentos son texto literal del corpus.** El evaluador busca la evidencia como
  substring (normalizando espacios y mayúsculas), así que el chunking nunca reescribe el
  texto: solo lo corta y, con `metadatos`, le antepone título y sección.
- **Siempre se devuelve al menos un fragmento** (el más parecido), aunque ninguno pase el
  umbral: devolver cero da recall 0 seguro.
- `buscar(pregunta)` devuelve lo mismo que el CLI para una pregunta. Es la función que
  usan las herramientas de las partes 2 y 3.

### Experimentos

`experimentos/correr.py` corre la grilla de configuraciones. Por cada una escribe
`experimentos/<nombre>.jsonl`, lo evalúa con `evaluar/evaluar.py` sin modificar (que
genera `<nombre>.jsonl.eval.json`) y arma `experimentos/tabla.md` con todas las filas.

Las preguntas `dev` son solo 20. Para no sobreajustar, la elección final prefiere reglas
simples (k chico, umbral o margen redondos) a la fila con el número más alto por una
pregunta.

## Parte 4: `atencion.py` — capa de atención en NumPy

Solo NumPy. Todas las matrices son 2D: una fila por token.

| Función | Devuelve | Qué hace |
|---|---|---|
| `softmax(M)` | matriz de la forma de `M` | softmax por fila (último eje) |
| `atencion(Q, K, V, mascara=False)` | `(salida, A)` | `A = softmax(Q Kᵀ / √d_k)`, `salida = A V` |
| `autoatencion(X, Wq, Wk, Wv, mascara=False)` | `(salida, A)` | `atencion(X Wq, X Wk, X Wv)` |
| `multicabeza(X, cabezas, Wo, mascara=False)` | `salida` | concatena la salida de cada cabeza por columnas y multiplica por `Wo` |
| `layer_norm(x, eps=1e-5)` | matriz de la forma de `x` | `(x − media) / √(var + eps)` por fila |

Formas: con `X` de n×d y `Wv` de d×d_v, `A` es n×n y la salida n×d_v.

Decisiones:

- **Softmax estable:** resta el máximo de cada fila antes de `exp`. El resultado no cambia
  y `exp` nunca desborda (`[[1000, 1000]]` → `[[0.5, 0.5]]`).
- **d_k sale de `Q.shape[-1]`**, no es una constante: cada cabeza puede tener el suyo.
- **Máscara causal:** las posiciones arriba de la diagonal se ponen en `−inf` antes del
  softmax, así su peso queda en 0 y cada fila sigue sumando 1. Se aplica solo en
  `atencion`; `autoatencion` y `multicabeza` la pasan hacia abajo. La diagonal nunca se
  enmascara, así que ninguna fila queda toda en `−inf` (no hay NaN).
- **Layer norm sin γ ni β**, con varianza poblacional (`np.var`, ddof=0): es lo que piden
  los valores de referencia.

Verificación: `python3 atencion/test_atencion.py atencion.py` (14 tests de la cátedra,
valores del ejemplo "the cat sat", d = 4). Además se comparó contra una implementación
con bucles sobre datos aleatorios (n ≠ d, d_k ≠ d_v, con y sin máscara).
