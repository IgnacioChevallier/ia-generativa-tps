# SPEC.md

Qué se construyó, concretamente. La consigna completa está en
[task/mission.md](task/mission.md); esto describe la implementación.

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
