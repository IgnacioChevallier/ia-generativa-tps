"""Recuperador vectorial de la parte 1 (versión mínima).

  python3 recuperar.py --preguntas datos/preguntas_recuperacion_dev.jsonl --salida resultados.jsonl

Corta cada documento del corpus por secciones `##`, calcula un embedding por fragmento
con un encoder de oraciones y, para cada pregunta, devuelve los TOP_K fragmentos con
mayor similitud coseno.
"""
import argparse
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

CORPUS = Path(__file__).parent / "datos" / "corpus"
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 1


def fragmentar(texto):
    """Un fragmento por sección `##`; el texto previo a la primera sección es otro fragmento.

    El fragmento conserva el texto literal del documento (el evaluador busca la
    evidencia como substring) y se le antepone el título `#` del documento.
    """
    lineas = texto.strip().splitlines()
    titulo = lineas[0].lstrip("# ").strip() if lineas and lineas[0].startswith("# ") else ""
    bloques, actual = [], []
    for linea in lineas[1:] if titulo else lineas:
        if linea.startswith("## ") and actual:
            bloques.append(actual)
            actual = []
        actual.append(linea)
    if actual:
        bloques.append(actual)
    fragmentos = []
    for bloque in bloques:
        cuerpo = "\n".join(bloque).strip()
        if cuerpo:
            fragmentos.append(f"{titulo}\n{cuerpo}" if titulo else cuerpo)
    return fragmentos


def cargar_corpus(carpeta=CORPUS):
    return [f for doc in sorted(carpeta.glob("*.md")) for f in fragmentar(doc.read_text(encoding="utf-8"))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preguntas", required=True)
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()

    preguntas = [json.loads(l) for l in Path(args.preguntas).read_text(encoding="utf-8").splitlines() if l.strip()]
    fragmentos = cargar_corpus()

    modelo = SentenceTransformer(MODELO)
    emb_frag = modelo.encode(fragmentos, normalize_embeddings=True)
    emb_preg = modelo.encode([p["pregunta"] for p in preguntas], normalize_embeddings=True)
    similitudes = emb_preg @ emb_frag.T  # vectores normalizados: producto punto = coseno

    with open(args.salida, "w", encoding="utf-8") as f:
        for p, sims in zip(preguntas, similitudes):
            mejores = sims.argsort()[::-1][:TOP_K]
            f.write(json.dumps({"id": p["id"], "fragmentos": [fragmentos[i] for i in mejores]}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
