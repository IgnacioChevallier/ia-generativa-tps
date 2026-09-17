# CLAUDE.md

Instrucciones de proyecto para trabajar en este repo con un asistente de código.
Contexto completo de la consigna: [task/mission.md](task/mission.md) y [task/rubric.md](task/rubric.md).

## Qué es esto

TP de prompting: una interfaz de chat propia sobre 4 modelos vía OpenRouter (ejercicio 1),
usada para generar `vida.py` (Conway) en el mínimo de prompts posible, con caching
obligatorio y medición de tokens/costo (ejercicios 2 y 3).

## Archivos clave

- `openrouter.py` — cliente único de OpenRouter. Expone `MODELS` (los 4 slots) y `chat()`.
  No tocar la firma de `chat()` sin avisar: `chat_interface.py` depende de ella.
- `chat_interface.py` — REPL de la interfaz. Cambiar de modelo reinicia la conversación
  (mensajes, `effort` y `schema` se resetean) — es un requisito de la consigna, no un detalle.
- `vida.py` — el script de Conway. **No editar a mano.** Tiene que ser exactamente el
  código que salió del log de la conversación ganadora (ver regla abajo).
- `logs/*.md` — logs de conversación, uno por archivo. Son la evidencia de auditoría:
  sin log, esa corrida no cuenta para la nota (regla de admisibilidad de la rúbrica).
- `prompt_conway_intento1.txt` — el prompt del ejercicio 2, para referencia/reuso.
- `informe.md` — el informe de los 3 ejercicios.
- `task/` — consigna y rúbrica de la cátedra, y `task/tests/test_vida.py` (los tests).

## Reglas no negociables

1. **`vida.py` tiene que ser byte a byte igual al código del log ganador.** Si un editor
   recorta trailing whitespace o cambia el final de línea al guardar, se rompe la
   verificación de la rúbrica ("el `vida.py` entregado no coincide con el log" → 2.1 y 2.2
   valen 0). Si hay que tocar algo, se cambia el prompt y se corre de nuevo, no el archivo.
2. **Nunca commitear `.env`** (tiene la `OPENROUTER_API_KEY`). Ya está en `.gitignore`.
3. **El ejercicio 2 es 1 prompt, o a lo sumo 2.** Si un intento se pasa de 2 turnos de
   usuario, quedó quemado: conversación nueva, prompt reescrito desde cero. No se parchea
   código a mano entre intentos — lo que cambia es el prompt.
4. **La parte estática del prompt de Conway va primero e idéntica entre intentos**, para
   intentar forzar el cache por prefijo (ver hallazgo en `informe.md`: para
   `deepseek/deepseek-v4-flash-0731` el cache no está disponible en ningún proveedor
   detrás de OpenRouter al día de esta entrega — no asumir que un `cached_tokens=0` es un
   error del prompt sin revisar antes ese hallazgo).
5. **Correr los tests de la cátedra contra `vida.py` tal cual, sin flags extra**:
   `python3 task/tests/test_vida.py vida.py`.

## Cómo correr

```bash
python3 chat_interface.py                    # interfaz de chat
python3 task/tests/test_vida.py vida.py       # tests de la cátedra
python3 openrouter.py                         # smoke test de los 4 slots (imprime usage)
```

Necesita `OPENROUTER_API_KEY` en `.env` (junto a `openrouter.py`) o en el entorno.

## Commits

Historia limpia: un commit por unidad de trabajo real (un ejercicio, una corrección, un
hallazgo), con mensaje que explica el cambio. Nada de "todo en un commit" — la rúbrica lo
puntúa explícitamente (4.3).
