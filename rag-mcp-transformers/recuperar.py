"""Recuperador vectorial de la parte 1.

  python3 recuperar.py --preguntas datos/preguntas_recuperacion_dev.jsonl --salida resultados.jsonl

Corta los documentos del corpus en fragmentos, calcula un embedding por fragmento con un
transformer encoder y, para cada pregunta, devuelve los fragmentos con mayor similitud
coseno. Sin `--config` usa la configuración ganadora (CONFIG); las claves están
documentadas en SPEC.md.
"""
import argparse
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sentence_transformers.sentence_transformer.modules import Pooling, Transformer

CORPUS = Path(__file__).parent / "datos" / "corpus"

# Configuración ganadora (ver INFORME.md, parte 1).
CONFIG = {
    "encoder": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "pooling": "st",
    "prefijo_pregunta": "",
    "prefijo_fragmento": "",
    "chunking": "seccion",
    "tamano": 60,
    "solapamiento": 20,
    "metadatos": True,
    "top_k": 1,
    "umbral": 0.0,
    "margen": None,
}


# ---------------- chunking ----------------

def _secciones(texto):
    """Devuelve (título del documento, [(encabezado `##` o "", [líneas])])."""
    lineas = texto.strip().splitlines()
    titulo = ""
    if lineas and lineas[0].startswith("# "):
        titulo = lineas[0][2:].strip()
        lineas = lineas[1:]
    secciones, encabezado, actual = [], "", []
    for linea in lineas:
        if linea.startswith("## "):
            secciones.append((encabezado, actual))
            encabezado, actual = linea.strip(), []
        else:
            actual.append(linea)
    secciones.append((encabezado, actual))
    return titulo, secciones


def _prefijo(*partes):
    return "".join(f"{p}\n" for p in partes if p)


def fragmentar(texto, chunking="seccion", tamano=60, solapamiento=20, metadatos=True):
    """Corta un documento Markdown en fragmentos de texto literal del corpus.

    - seccion: un fragmento por sección `##` (el texto previo a la primera es otro).
    - parrafo: un fragmento por párrafo (bloque separado por líneas en blanco).
    - ventana: ventanas de `tamano` palabras que se solapan en `solapamiento` palabras.

    Con `metadatos`, antepone el título del documento (y la sección, en `parrafo`).
    """
    titulo, secciones = _secciones(texto)
    tit = titulo if metadatos else ""
    fragmentos = []

    if chunking == "seccion":
        for encabezado, lineas in secciones:
            cuerpo = "\n".join(([encabezado] if encabezado else []) + lineas).strip()
            if "\n".join(lineas).strip():
                fragmentos.append(_prefijo(tit) + cuerpo)
    elif chunking == "parrafo":
        for encabezado, lineas in secciones:
            for parrafo in "\n".join(lineas).split("\n\n"):
                if parrafo.strip():
                    fragmentos.append(_prefijo(tit, encabezado if metadatos else "") + parrafo.strip())
    elif chunking == "ventana":
        if not 0 <= solapamiento < tamano:
            raise ValueError("el solapamiento tiene que ser menor que el tamaño")
        palabras = "\n".join(l for _, lineas in secciones for l in lineas).split()
        paso = tamano - solapamiento
        for inicio in range(0, max(len(palabras) - solapamiento, 1), paso):
            fragmentos.append(_prefijo(tit) + " ".join(palabras[inicio:inicio + tamano]))
    else:
        raise ValueError(f"chunking desconocido: {chunking}")
    return fragmentos


def cargar_corpus(cfg, carpeta=CORPUS):
    opciones = {k: cfg[k] for k in ("chunking", "tamano", "solapamiento", "metadatos")}
    return [f for doc in sorted(carpeta.glob("*.md"))
            for f in fragmentar(doc.read_text(encoding="utf-8"), **opciones)]


# ---------------- encoder y búsqueda ----------------

def cargar_encoder(cfg):
    if cfg["pooling"] == "mean":
        # Línea de base: BERT sin ajustar, promedio de los vectores de la última capa.
        transformer = Transformer(cfg["encoder"], max_seq_length=512)
        pooling = Pooling(transformer.get_word_embedding_dimension(), pooling_mode="mean")
        return SentenceTransformer(modules=[transformer, pooling], device="cpu")
    return SentenceTransformer(cfg["encoder"], device="cpu")


def seleccionar(sims, top_k=1, umbral=0.0, margen=None):
    """Índices a devolver, en orden de similitud. Siempre devuelve al menos el mejor."""
    orden = sims.argsort()[::-1]
    mejor = sims[orden[0]]
    elegidos = [i for i in orden[:top_k]
                if sims[i] >= umbral and (margen is None or sims[i] >= mejor - margen)]
    return elegidos or [int(orden[0])]


class Recuperador:
    def __init__(self, cfg=None):
        self.cfg = {**CONFIG, **(cfg or {})}
        self.fragmentos = cargar_corpus(self.cfg)
        self.modelo = cargar_encoder(self.cfg)
        self.emb = self._codificar(self.fragmentos, self.cfg["prefijo_fragmento"])

    def _codificar(self, textos, prefijo):
        return self.modelo.encode([prefijo + t for t in textos], normalize_embeddings=True)

    def similitudes(self, preguntas):
        # Vectores normalizados: producto punto = coseno.
        return self._codificar(preguntas, self.cfg["prefijo_pregunta"]) @ self.emb.T

    def elegir(self, sims):
        c = self.cfg
        return [self.fragmentos[i] for i in seleccionar(sims, c["top_k"], c["umbral"], c["margen"])]

    def buscar(self, pregunta):
        return self.elegir(self.similitudes([pregunta])[0])


_recuperador = None


def buscar(pregunta):
    """Fragmentos relevantes para una pregunta, con la configuración ganadora."""
    global _recuperador
    if _recuperador is None:
        _recuperador = Recuperador()
    return _recuperador.buscar(pregunta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preguntas", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--config", help="JSON con claves que pisan CONFIG (para experimentos)")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8")) if args.config else {}
    preguntas = [json.loads(l) for l in Path(args.preguntas).read_text(encoding="utf-8").splitlines() if l.strip()]
    rec = Recuperador(cfg)
    sims = rec.similitudes([p["pregunta"] for p in preguntas])

    with open(args.salida, "w", encoding="utf-8") as f:
        for p, s in zip(preguntas, sims):
            f.write(json.dumps({"id": p["id"], "fragmentos": rec.elegir(s)}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
