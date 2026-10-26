"""Grilla de variantes del buscador (Parte 2), medidas con `admision.evaluar_rag` sobre las 60 consultas de desarrollo.

    uv run python -m experimentos.rag_grilla [--normas normas/original] [--salida experimentos/rag/grilla.json]

Cada variante deja sus números en el JSON de salida y una tabla en pantalla. Las variantes que no mejoran también
quedan registradas."""

import argparse
import json
import sys
from pathlib import Path

from admision.evaluar_rag import cargar_dataset, evaluar_buscador, evaluar_recuperador

from buscador import BuscadorNormas

RAIZ = Path(__file__).resolve().parent.parent

VARIANTES = {
    "seccion_k2_sin_raiz_sin_exp": dict(granularidad="seccion", k_entorno=2, expansiones=False, con_raiz=False),
    "seccion_k2_raiz": dict(granularidad="seccion", k_entorno=2, expansiones=False),
    "parrafo_k2": dict(granularidad="parrafo", k_entorno=2, expansiones=False),
    "parrafo_k3": dict(granularidad="parrafo", k_entorno=3, expansiones=False),
    "parrafo_k4": dict(granularidad="parrafo", k_entorno=4, expansiones=False),
    "parrafo_k3_exp": dict(granularidad="parrafo", k_entorno=3, expansiones=True),
    "parrafo_k2_exp": dict(granularidad="parrafo", k_entorno=2, expansiones=True),
    "parrafo_k4_exp": dict(granularidad="parrafo", k_entorno=4, expansiones=True),
}


def correr(normas: Path, consultas: Path, variantes: dict) -> dict:
    dataset = cargar_dataset(consultas)
    resultados = {}
    for nombre, cfg in variantes.items():
        b = BuscadorNormas(normas, **cfg)
        r = evaluar_buscador(b, dataset)
        r["presupuesto"] = {p: evaluar_recuperador(b.recuperar, dataset, p) for p in (256, 512, 1024)}
        resultados[nombre] = {"config": cfg, **r}
    return resultados


def tabla(resultados: dict) -> str:
    filas = ["variante                      k  recall  prec  tokens  completas  rec@256 rec@512 rec@1024"]
    for n, r in resultados.items():
        pr = r["presupuesto"]
        filas.append(f"{n:29s} {r['k_entorno']}  {r['recall_evidencia']:.3f}  {r['precision']:.3f}  "
                     f"{r['tokens_por_consulta']:5d}  {r['consultas_con_toda_la_evidencia']:3d}/{r['consultas']}   "
                     f"{pr[256]['recall_evidencia']:.3f}   {pr[512]['recall_evidencia']:.3f}   {pr[1024]['recall_evidencia']:.3f}")
    return "\n".join(filas)


def ajustar_bm25(normas: Path, conjuntos: dict[str, Path]) -> dict:
    """Recall (k=3) de BM25 para una grilla de k1 y b, sobre cada conjunto de consultas. Si ninguna combinación mejora
    en todos los conjuntos a la vez, se dejan los valores por defecto."""
    resultados = {}
    for k1 in (0.9, 1.2, 1.5, 2.0):
        for b in (0.3, 0.5, 0.75, 0.9):
            buscador = BuscadorNormas(normas, k_entorno=3, k1=k1, b=b)
            resultados[f"k1={k1} b={b}"] = {
                nombre: {k: v for k, v in evaluar_buscador(buscador, cargar_dataset(ruta)).items()
                         if k in ("recall_evidencia", "precision", "consultas_con_toda_la_evidencia")}
                for nombre, ruta in conjuntos.items()}
    return resultados


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ajustar-bm25", action="store_true", help="grilla de k1 y b sobre dev y consultas propias")
    ap.add_argument("--normas", type=Path, default=RAIZ / "normas" / "original")
    ap.add_argument("--consultas", type=Path, default=RAIZ / "rag" / "consultas_dev.jsonl")
    ap.add_argument("--salida", type=Path, default=RAIZ / "experimentos" / "rag" / "grilla.json")
    a = ap.parse_args()
    if a.ajustar_bm25:
        conjuntos = {"dev": RAIZ / "rag" / "consultas_dev.jsonl", "propias": RAIZ / "datos" / "consultas_propias.jsonl"}
        res = ajustar_bm25(a.normas, conjuntos)
        a.salida.parent.mkdir(parents=True, exist_ok=True)
        a.salida.with_name("ajuste_bm25.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        for k, v in res.items():
            print(f"{k:16s} dev recall {v['dev']['recall_evidencia']:.3f} prec {v['dev']['precision']:.3f} | "
                  f"propias recall {v['propias']['recall_evidencia']:.3f} prec {v['propias']['precision']:.3f}")
        sys.exit(0)
    res = correr(a.normas, a.consultas, VARIANTES)
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(tabla(res))
    sys.exit(0)
