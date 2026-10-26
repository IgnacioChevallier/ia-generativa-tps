"""Genera los datos de entrenamiento de la Parte 1.

    uv run python -m curado.generar_datos [--por-version 500] [--semilla 7] [--salida datos]

Entradas: `historial_clasificado.csv` (de `curado.clasificar`), `historial/historial.csv`, las normas de `normas/` y
el generador de casos de la cátedra. Salidas, en `datos/`:

- `versiones_sinteticas.json`: los valores de parámetros de las versiones de normas inventadas (la cátedra evalúa con
  otros números; entrenar con varias versiones enseña a leerlos del buscador y no a memorizarlos).
- `trayectorias_reales.jsonl`: una por fila `correcta` del historial, jugada con las normas originales.
- `trayectorias_sinteticas.jsonl`: casos del generador de la cátedra, jugados con las normas original, b, c y las
  versiones sintéticas.
- `conversaciones_reales.jsonl` y `conversaciones_sinteticas.jsonl`: las mismas trayectorias como mensajes de chat, con
  el mensaje de sistema y el formato del agente de ejemplo de la cátedra (la Parte 3 los vuelve a armar con el prompt
  optimizado a partir de las trayectorias).
- `resumen_generacion.json`: cuántas se generaron y cuántas se descartaron y por qué.
- `SHA256SUMS`: el hash de cada archivo. La generación es determinista (misma semilla, mismos bytes), así que en git
  van los hashes y no los 65 MB de datos: `sha256sum -c datos/SHA256SUMS` verifica lo que se regeneró.

Los 50 casos de práctica no se usan para entrenar: se descartan los casos generados que coinciden con alguno."""

import argparse
import csv
import hashlib
import json
import random
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import yaml

from admision.casos import cargar_casos
from admision.ejemplo import mensaje_de_sistema, primer_mensaje
from admision.generador import generar

from buscador import BuscadorNormas

from .historial import RAIZ, leer_historial
from .oraculo import cargar_parametros
from .trayectorias import caso_de_fila, jugar

VERSIONES_DE_LA_CATEDRA = ("original", "b", "c")


def parametros_sinteticos(semilla: int) -> dict[str, int]:
    r = random.Random(semilla)
    tde_1, tde_2, tde_3 = r.randint(8, 30), r.randint(8, 30), r.randint(10, 45)
    tde_4 = r.randint(30, 120)
    return {"P-ADM-1": r.randint(1, 3), "P-ADM-2": r.randint(55, 80), "P-ADM-3": r.randint(1, 3),
            "P-COB-2": r.randint(0, 9), "P-TDE-1": tde_1, "P-TDE-2": tde_2, "P-TDE-3": tde_3, "P-TDE-4": tde_4,
            "P-TDE-5": r.randint(2, min(tde_1, tde_2, tde_3, 8) - 1)}


def escribir_version(destino: Path, valores: dict[str, int]) -> Path:
    """Una carpeta de normas con el texto de `normas/original` y los parámetros `valores`."""
    origen = RAIZ / "normas" / "original"
    destino.mkdir(parents=True, exist_ok=True)
    for f in origen.glob("NOR-*.md"):
        shutil.copy(f, destino / f.name)
    datos = yaml.safe_load((origen / "parametros.yaml").read_text(encoding="utf-8"))
    for p in datos["parametros"]:
        p["valor"] = valores.get(p["codigo"], p["valor"])
    (destino / "parametros.yaml").write_text(yaml.safe_dump(datos, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n")
    return destino


def a_mensajes(trayectoria: dict) -> list[dict]:
    """La trayectoria como conversación con el formato del agente de ejemplo: el modelo responde un JSON por turno y
    el resultado de la herramienta vuelve como mensaje del usuario."""
    mensajes = [{"role": "system", "content": mensaje_de_sistema()},
                {"role": "user", "content": primer_mensaje(trayectoria["paciente_id"])}]
    pasos = trayectoria["pasos"]
    for i, p in enumerate(pasos):
        mensajes.append({"role": "assistant", "content": json.dumps(
            {"herramienta": p["herramienta"], "argumentos": p["argumentos"]}, ensure_ascii=False)})
        if i < len(pasos) - 1:
            mensajes.append({"role": "user", "content": f"Resultado de {p['herramienta']}:\n{p['observacion']}"})
    return mensajes


def composicion(trayectorias: list[dict]) -> dict:
    """Tamaño medio de la conversación (4 caracteres por token, como la evaluación del buscador) y qué parte es
    mensaje de sistema y qué parte es texto de búsquedas."""
    total = sistema = busquedas = 0
    for t in trayectorias:
        for m in a_mensajes(t):
            n = len(m["content"])
            total += n
            if m["role"] == "system":
                sistema += n
            elif m["content"].startswith("Resultado de buscar_normativa"):
                busquedas += n
    return {"tokens_por_conversacion": round(total / len(trayectorias) / 4),
            "porcentaje_sistema": round(100 * sistema / total, 1), "porcentaje_busquedas": round(100 * busquedas / total, 1)}


def _firma(caso) -> tuple:
    return (caso.edad, caso.nivel, caso.motivo, caso.nota, caso.documento_numero, caso.paciente_id)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--por-version", type=int, default=500, help="casos sintéticos por versión de normas")
    ap.add_argument("--versiones-sinteticas", type=int, default=5)
    ap.add_argument("--semilla", type=int, default=7)
    ap.add_argument("--salida", type=Path, default=RAIZ / "datos")
    a = ap.parse_args()
    a.salida.mkdir(parents=True, exist_ok=True)
    resumen = {"semilla": a.semilla, "descartes": Counter(), "generadas": Counter()}

    with tempfile.TemporaryDirectory() as tmp:
        carpetas = {v: RAIZ / "normas" / v for v in VERSIONES_DE_LA_CATEDRA}
        sinteticas = {}
        for i in range(a.versiones_sinteticas):
            nombre = f"s{i + 1:02d}"
            sinteticas[nombre] = parametros_sinteticos(a.semilla * 1000 + i)
            carpetas[nombre] = escribir_version(Path(tmp) / nombre, sinteticas[nombre])
        (a.salida / "versiones_sinteticas.json").write_text(json.dumps(sinteticas, indent=2), encoding="utf-8", newline="\n")
        buscadores = {v: BuscadorNormas(c) for v, c in carpetas.items()}
        parametros = {v: cargar_parametros(c) for v, c in carpetas.items()}

        # reales: las filas correctas del historial, con las normas originales
        clases = {r["id"]: r["tipo"] for r in csv.DictReader(open(RAIZ / "historial_clasificado.csv", encoding="utf-8"))}
        azar = random.Random(a.semilla)
        reales = []
        for fila in leer_historial():
            if clases[fila["id"]] != "correcta":
                continue
            t = jugar(caso_de_fila(fila), buscadores["original"], parametros["original"], azar)
            if t is None:
                resumen["descartes"]["real"] += 1
                continue
            reales.append({**t, "origen": "real", "version": "original"})

        # sintéticos: casos del generador de la cátedra, uno por semilla y versión
        practica = {_firma(c) for c in cargar_casos(RAIZ / "practica" / "casos.jsonl")}
        sinteticos = []
        for j, version in enumerate(carpetas):
            for caso in generar(semilla=a.semilla * 100 + j, n=a.por_version, prefijo=f"sim-{version}"):
                if _firma(caso) in practica:
                    resumen["descartes"]["coincide_con_practica"] += 1
                    continue
                t = jugar(caso, buscadores[version], parametros[version], azar)
                if t is None:
                    resumen["descartes"]["sintetico"] += 1
                    continue
                sinteticos.append({**t, "origen": "sintetico", "version": version})

    for nombre, trayectorias in (("reales", reales), ("sinteticas", sinteticos)):
        (a.salida / f"trayectorias_{nombre}.jsonl").write_text(
            "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in trayectorias), encoding="utf-8", newline="\n")
        (a.salida / f"conversaciones_{nombre}.jsonl").write_text(
            "".join(json.dumps({"id": t["id"], "version": t["version"], "messages": a_mensajes(t)},
                               ensure_ascii=False) + "\n" for t in trayectorias), encoding="utf-8", newline="\n")
        resumen["generadas"][nombre] = len(trayectorias)
    resumen["generadas_por_version"] = dict(Counter(t["version"] for t in sinteticos))
    resumen["pasos_medios"] = {n: round(sum(len(t["pasos"]) for t in ts) / len(ts), 2)
                               for n, ts in (("reales", reales), ("sinteticas", sinteticos))}
    resumen["composicion"] = {"reales": composicion(reales), "sinteticas": composicion(sinteticos)}
    resumen["descartes"], resumen["generadas"] = dict(resumen["descartes"]), dict(resumen["generadas"])
    (a.salida / "resumen_generacion.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    sumas = [f"{hashlib.sha256((a.salida / n).read_bytes()).hexdigest()}  {n}" for n in sorted(
        x.name for x in a.salida.iterdir() if x.suffix in (".json", ".jsonl") and x.name != "consultas_propias.jsonl")]
    (a.salida / "SHA256SUMS").write_text("\n".join(sumas) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
