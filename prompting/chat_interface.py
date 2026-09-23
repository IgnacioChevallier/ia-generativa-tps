#!/usr/bin/env python3
"""Interfaz de chat de terminal — Ejercicio 1 (Persona 2).

No es linda a propósito (la consigna no lo pide): un REPL que sirve los 4
modelos de `openrouter.py`, muestra el usage después de cada respuesta y
guarda un log .md por conversación.

Uso:
    python3 chat_interface.py

Comandos dentro del chat:
    /model            elige otro modelo (arranca conversación nueva)
    /effort <nivel>   fija reasoning.effort: minimal|low|medium|high|off (slot 1, y opcional en otros)
    /schema <json>    fija un JSON Schema para response_format (slot 3); "/schema off" lo saca
    /system <texto>   agrega un mensaje system a la conversación
    /file <ruta>      manda el contenido completo de un archivo como un único mensaje
                      (la terminal parte un pegado multilínea en un mensaje por línea;
                      para prompts largos, guardalos en un .txt y usá este comando)
    /exit             termina el chat
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from openrouter import MODELS, chat

for _stream in (sys.stdin, sys.stdout):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

LOG_DIR = Path(__file__).with_name("logs")


def elegir_modelo():
    print("\nModelos disponibles:")
    for slot, model in MODELS.items():
        print(f"  {slot}. {model}")
    while True:
        elegido = input("Elegí un modelo (1-4): ").strip()
        if elegido in {"1", "2", "3", "4"}:
            return MODELS[int(elegido)]
        print("Opción inválida.")


def nombre_log(model):
    slug = model.replace("/", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    LOG_DIR.mkdir(exist_ok=True)
    return LOG_DIR / f"{slug}_{ts}.md"


def formatear_usage(usage):
    return (
        f"prompt={usage['prompt_tokens']} "
        f"completion={usage['completion_tokens']} "
        f"cached={usage['cached_tokens']} "
        f"reasoning={usage['reasoning_tokens']} "
        f"cost=${usage['cost']:.6f}"
    )


def log_append(path, texto):
    with open(path, "a", encoding="utf-8") as f:
        f.write(texto)


def nueva_conversacion(model):
    """Cambiar de modelo = conversación nueva: mensajes, effort y schema se resetean."""
    log_path = nombre_log(model)
    log_append(
        log_path,
        f"# Conversación — {model}\n\n"
        f"_Inicio: {datetime.now().isoformat(timespec='seconds')}_\n\n",
    )
    print(f"\n== Conversación nueva con {model} ==")
    print(f"Log: {log_path}")
    return [], log_path, None, None


def main():
    model = elegir_modelo()
    messages, log_path, effort, schema = nueva_conversacion(model)

    print("Escribí tu mensaje, o un comando (/model, /effort, /schema, /system, /file, /exit).\n")

    def enviar(texto):
        messages.append({"role": "user", "content": texto})
        log_append(log_path, f"## user\n\n{texto}\n\n")
        try:
            r = chat(model, messages, effort=effort, json_schema=schema)
        except Exception as e:
            print(f"Error: {e}")
            messages.pop()
            log_append(log_path, f"## error\n\n{e}\n\n")
            return
        messages.append({"role": "assistant", "content": r["content"]})
        usage_str = formatear_usage(r["usage"])
        print(f"\n{model}: {r['content']}\n")
        print(f"[usage] {usage_str}\n")
        log_append(
            log_path,
            f"## assistant\n\n{r['content']}\n\n**Usage:** {usage_str}\n\n",
        )

    while True:
        try:
            entrada = input("Vos: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not entrada:
            continue
        if entrada == "/exit":
            break

        if entrada == "/model":
            model = elegir_modelo()
            messages, log_path, effort, schema = nueva_conversacion(model)
            continue

        if entrada.startswith("/effort"):
            partes = entrada.split(maxsplit=1)
            nivel = partes[1].strip() if len(partes) > 1 else "off"
            effort = None if nivel == "off" else nivel
            log_append(log_path, f"## config\n\n`reasoning.effort = {effort}`\n\n")
            print(f"(effort = {effort})")
            continue

        if entrada.startswith("/schema"):
            resto = entrada[len("/schema"):].strip()
            if resto in ("", "off"):
                schema = None
                log_append(log_path, "## config\n\n`response_format = off`\n\n")
                print("(schema off)")
            else:
                try:
                    schema = json.loads(resto)
                    log_append(log_path, f"## config\n\n`response_format.schema = {resto}`\n\n")
                    print("(schema seteado)")
                except json.JSONDecodeError as e:
                    print(f"JSON Schema inválido: {e}")
            continue

        if entrada.startswith("/system"):
            texto = entrada[len("/system"):].strip()
            if texto:
                messages.append({"role": "system", "content": texto})
                log_append(log_path, f"## system\n\n{texto}\n\n")
                print("(system agregado)")
            continue

        if entrada.startswith("/file"):
            ruta = entrada[len("/file"):].strip()
            if not ruta:
                print("Uso: /file <ruta-al-prompt.txt>")
                continue
            try:
                texto = Path(ruta).expanduser().read_text(encoding="utf-8").strip()
            except OSError as e:
                print(f"No pude leer el archivo: {e}")
                continue
            print(f"(mandando {len(texto)} caracteres desde {ruta})")
            enviar(texto)
            continue

        enviar(entrada)


if __name__ == "__main__":
    main()
