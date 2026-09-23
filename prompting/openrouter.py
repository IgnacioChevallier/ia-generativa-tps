"""Cliente único de OpenRouter para los 4 modelos del TP.

Uso:
    from openrouter import MODELS, chat
    r = chat(MODELS[1], [{"role": "user", "content": "hola"}], effort="high")
    r["content"], r["usage"]

Prueba de los 4 slots:  python3 openrouter.py
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = {
    1: "openai/gpt-5.6-luna",             # reasoning.effort
    2: "anthropic/claude-haiku-4.5",      # cache_control explícito
    3: "google/gemini-3.7-flash",         # JSON Schema
    4: "deepseek/deepseek-v4-flash-0731", # barato; el del ejercicio 2
}


def _api_key():
    env = Path(__file__).with_name(".env")
    if env.exists():
        for line in env.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() and not k.startswith("#"):
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Falta OPENROUTER_API_KEY (en .env o en el entorno)")
    return key


def _mark_cache(messages):
    """Anthropic solo cachea bloques marcados: marca los mensajes system."""
    out = []
    for m in messages:
        if m["role"] == "system" and isinstance(m["content"], str):
            m = {"role": "system", "content": [
                {"type": "text", "text": m["content"], "cache_control": {"type": "ephemeral"}}
            ]}
        out.append(m)
    return out


def parse_usage(usage):
    """Aplana el usage de OpenRouter; lo que no venga queda en 0."""
    usage = usage or {}
    return {
        "prompt_tokens": usage.get("prompt_tokens") or 0,
        "completion_tokens": usage.get("completion_tokens") or 0,
        "cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0,
        "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0,
        "cost": usage.get("cost") or 0.0,
        "cache_discount": usage.get("cache_discount") or 0.0,
    }


def chat(model, messages, *, effort=None, json_schema=None, max_tokens=16000, timeout=300):
    """Manda la conversación completa y devuelve {content, usage, raw}.

    effort: "low" | "medium" | "high" -> reasoning.effort (slot 1; también activa el razonamiento en DeepSeek)
    json_schema: dict con un JSON Schema -> response_format estructurado (slot 3)
    max_tokens: tope de salida (incluye razonamiento). Sin tope, OpenRouter reserva
        crédito para el máximo del modelo (65536) y responde 402 si el saldo no alcanza.
    """
    body = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if model.startswith("anthropic/"):
        body["messages"] = _mark_cache(messages)
    if effort:
        body["reasoning"] = {"effort": effort}
    if json_schema:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "respuesta", "strict": True, "schema": json_schema},
        }

    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.load(resp)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"OpenRouter {e.code}: {e.read().decode(errors='replace')}") from None

    if "error" in raw:  # OpenRouter a veces devuelve 200 con error adentro
        raise RuntimeError(f"OpenRouter: {raw['error']}")
    return {
        "content": raw["choices"][0]["message"].get("content") or "",
        "usage": parse_usage(raw.get("usage")),
        "raw": raw,
    }


if __name__ == "__main__":
    # parse_usage no necesita red
    u = parse_usage({"prompt_tokens": 10, "prompt_tokens_details": {"cached_tokens": 4}, "cost": 0.1})
    assert u == {"prompt_tokens": 10, "completion_tokens": 0, "cached_tokens": 4,
                 "reasoning_tokens": 0, "cost": 0.1, "cache_discount": 0.0}, u
    assert _mark_cache([{"role": "system", "content": "x"}])[0]["content"][0]["cache_control"]

    ask = [{"role": "user", "content": "¿Cuántos números primos hay entre 1 y 50? Respondé solo el número."}]

    print("== Slot 1: effort low vs high ==")
    # pregunta que obliga a pensar; con una trivial el modelo no razona en ningún nivel
    # una sola corrida por nivel tiene ruido; con esta pregunta minimal < low < high se sostiene
    hard = [{"role": "user", "content": "Encontrá el menor entero positivo n tal que n^2 + n + 41 no es primo, y el menor n > 1 tal que 2^n ≡ 1 (mod 1019·n)? Si el segundo no existe bajo 5000 decí 'no'. Respondé solo los dos valores."}]
    for level in ("minimal", "low", "high"):
        print(level, chat(MODELS[1], hard, effort=level)["usage"])

    print("== Slot 2: cache (dos pasadas del mismo system) ==")
    # Haiku 4.5 no cachea prompts chicos (mínimo ~4096 tokens): contexto estático grande
    ctx = "Sos un asistente de un curso de IA generativa. " + "Regla de estilo: respondé breve y en español. " * 600
    msgs = [{"role": "system", "content": ctx}, {"role": "user", "content": "Decí hola."}]
    for i in (1, 2):
        print(f"pasada {i}", chat(MODELS[2], msgs)["usage"])

    print("== Slot 3: JSON Schema ==")
    schema = {"type": "object", "properties": {"primos": {"type": "integer"}},
              "required": ["primos"], "additionalProperties": False}
    r = chat(MODELS[3], ask, json_schema=schema)
    print(json.loads(r["content"]), r["usage"])

    print("== Slot 4: DeepSeek ==")
    r = chat(MODELS[4], ask)
    print(r["content"], r["usage"])
