"""Corre la grilla de experimentos de la parte 1.

  python3 experimentos/correr.py            # todas las configuraciones
  python3 experimentos/correr.py e5 bge     # solo las que contienen alguno de esos textos

Por cada configuración escribe en experimentos/:
  <nombre>.config.json   las claves que pisan CONFIG (reproducible con recuperar.py --config)
  <nombre>.jsonl         los fragmentos devueltos
  <nombre>.jsonl.eval.json   la evaluación de evaluar/evaluar.py, sin modificar
y al final arma experimentos/tabla.md con todas las filas que tengan su .eval.json.
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from recuperar import CONFIG, Recuperador  # noqa: E402

DIR = RAIZ / "experimentos"
PREGUNTAS = RAIZ / "datos" / "preguntas_recuperacion_dev.jsonl"
EVALUADOR = RAIZ / "evaluar" / "evaluar.py"

BERT = {"encoder": "google-bert/bert-base-multilingual-cased", "pooling": "mean"}
MINILM = {"encoder": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "pooling": "st"}
E5S = {"encoder": "intfloat/multilingual-e5-small", "pooling": "st",
       "prefijo_pregunta": "query: ", "prefijo_fragmento": "passage: "}
E5B = {**E5S, "encoder": "intfloat/multilingual-e5-base"}
BGE = {"encoder": "BAAI/bge-m3", "pooling": "st"}

ENCODERS = {"bert": BERT, "minilm": MINILM, "e5s": E5S, "e5b": E5B, "bge": BGE}
CHUNKINGS = {
    "sec": {"chunking": "seccion"},
    "par": {"chunking": "parrafo"},
    "v60": {"chunking": "ventana", "tamano": 60, "solapamiento": 20},
    "v120": {"chunking": "ventana", "tamano": 120, "solapamiento": 40},
}

EXPERIMENTOS = {}
# 1. Encoders y chunking, con metadatos y top-1.
for e, enc in ENCODERS.items():
    for c, ch in CHUNKINGS.items():
        EXPERIMENTOS[f"{e}-{c}-k1"] = {**enc, **ch, "metadatos": True, "top_k": 1}
# 2. Metadatos: el mismo fragmento sin título ni sección.
for e, enc in ENCODERS.items():
    for c in ("sec", "par"):
        EXPERIMENTOS[f"{e}-{c}-sinmeta-k1"] = {**enc, **CHUNKINGS[c], "metadatos": False, "top_k": 1}
# 3. Top-k, umbral y margen sobre sección y párrafo.
# Cada encoder tiene su propia escala de coseno (e5 y BERT amontonan todo entre 0,8 y 0,95;
# MiniLM va de 0,3 a 0,8), así que el umbral absoluto se prueba en valores de su escala.
UMBRALES = {"bert": (0.85, 0.90), "minilm": (0.50, 0.60), "e5s": (0.85, 0.88),
            "e5b": (0.85, 0.88), "bge": (0.50, 0.60)}
for e, enc in ENCODERS.items():
    for c in ("sec", "par"):
        base = {**enc, **CHUNKINGS[c], "metadatos": True}
        for k in (2, 3, 5):
            EXPERIMENTOS[f"{e}-{c}-k{k}"] = {**base, "top_k": k}
        for u in UMBRALES[e]:
            EXPERIMENTOS[f"{e}-{c}-k3-u{u:.2f}"] = {**base, "top_k": 3, "umbral": u}
        for m in (0.005, 0.01, 0.02, 0.05):
            EXPERIMENTOS[f"{e}-{c}-k3-m{m:g}"] = {**base, "top_k": 3, "margen": m}

CLAVES_INDICE = ("encoder", "pooling", "prefijo_fragmento", "chunking", "tamano", "solapamiento", "metadatos")


def correr(nombres):
    preguntas = [json.loads(l) for l in PREGUNTAS.read_text(encoding="utf-8").splitlines() if l.strip()]
    textos = [p["pregunta"] for p in preguntas]
    cache = {}  # un índice por (encoder, chunking, metadatos): top-k y umbral no lo cambian
    for nombre in nombres:
        cfg = {**CONFIG, **EXPERIMENTOS[nombre]}
        clave = (tuple(cfg[k] for k in CLAVES_INDICE), cfg["prefijo_pregunta"])
        if clave not in cache:
            rec = Recuperador(cfg)
            cache[clave] = (rec, rec.similitudes(textos))
        rec, sims = cache[clave]
        rec.cfg = cfg
        salida = DIR / f"{nombre}.jsonl"
        (DIR / f"{nombre}.config.json").write_text(json.dumps(EXPERIMENTOS[nombre], ensure_ascii=False, indent=1), encoding="utf-8")
        with open(salida, "w", encoding="utf-8") as f:
            for p, s in zip(preguntas, sims):
                f.write(json.dumps({"id": p["id"], "fragmentos": rec.elegir(s)}, ensure_ascii=False) + "\n")
        subprocess.run([sys.executable, str(EVALUADOR), "recuperacion", "--preguntas", str(PREGUNTAS),
                        "--resultados", str(salida)], check=True, capture_output=True)
        r = json.loads(Path(f"{salida}.eval.json").read_text(encoding="utf-8"))["resumen"]
        print(f"{nombre:28} CR={r['context_relevance']:.3f} R={r['recall']:.3f} P={r['precision']:.3f} k={r['k']:.2f}", flush=True)


def tabla():
    filas = ["| Experimento | Encoder | Chunking | Metadatos | top-k | Umbral / margen | Context relevance | Recall | Precision | k medio | MRR |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for nombre, exp in EXPERIMENTOS.items():
        ev = DIR / f"{nombre}.jsonl.eval.json"
        if not ev.exists():
            continue
        cfg = {**CONFIG, **exp}
        r = json.loads(ev.read_text(encoding="utf-8"))["resumen"]
        ch = cfg["chunking"] + (f" {cfg['tamano']}/{cfg['solapamiento']}" if cfg["chunking"] == "ventana" else "")
        corte = f"margen {cfg['margen']}" if cfg["margen"] is not None else (f"coseno ≥ {cfg['umbral']}" if cfg["umbral"] else "—")
        filas.append(f"| [{nombre}]({nombre}.jsonl.eval.json) | {cfg['encoder'].split('/')[-1]}"
                     f"{' (promedio)' if cfg['pooling'] == 'mean' else ''} | {ch} | {'sí' if cfg['metadatos'] else 'no'}"
                     f" | {cfg['top_k']} | {corte} | **{r['context_relevance']:.3f}** | {r['recall']:.3f}"
                     f" | {r['precision']:.3f} | {r['k']:.2f} | {r['mrr']:.3f} |")
    (DIR / "tabla.md").write_text("\n".join(filas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    filtros = sys.argv[1:]
    correr([n for n in EXPERIMENTOS if not filtros or any(f in n for f in filtros)])
    tabla()
