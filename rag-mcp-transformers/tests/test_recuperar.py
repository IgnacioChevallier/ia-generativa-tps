import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from recuperar import CORPUS, fragmentar, seleccionar  # noqa: E402

DOC = """# Régimen de visitas

Texto general antes de las secciones.

## Terapia intensiva

La visita es de 12:00 a 12:30 y de 18:00 a 19:00.

Una persona por vez.

## Pediatría

Madre, padre o tutor pueden permanecer las 24 horas.
"""


def norm(t):
    # La misma normalización que evaluar/evaluar.py.
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", t).lower())


# ---------- chunking ----------

def test_seccion_un_fragmento_por_seccion_con_titulo():
    frags = fragmentar(DOC, chunking="seccion", metadatos=True)
    assert len(frags) == 3
    assert frags[0] == "Régimen de visitas\nTexto general antes de las secciones."
    assert frags[1].startswith("Régimen de visitas\n## Terapia intensiva\n")
    assert "Una persona por vez." in frags[1]


def test_seccion_sin_metadatos_no_antepone_titulo():
    frags = fragmentar(DOC, chunking="seccion", metadatos=False)
    assert frags[1].startswith("## Terapia intensiva")


def test_parrafo_un_fragmento_por_parrafo_con_titulo_y_seccion():
    frags = fragmentar(DOC, chunking="parrafo", metadatos=True)
    assert frags == [
        "Régimen de visitas\nTexto general antes de las secciones.",
        "Régimen de visitas\n## Terapia intensiva\nLa visita es de 12:00 a 12:30 y de 18:00 a 19:00.",
        "Régimen de visitas\n## Terapia intensiva\nUna persona por vez.",
        "Régimen de visitas\n## Pediatría\nMadre, padre o tutor pueden permanecer las 24 horas.",
    ]


def test_parrafo_sin_metadatos_es_solo_el_parrafo():
    frags = fragmentar(DOC, chunking="parrafo", metadatos=False)
    assert frags[1] == "La visita es de 12:00 a 12:30 y de 18:00 a 19:00."


def test_ventana_cubre_todas_las_palabras_con_solapamiento():
    texto = "# T\n\n" + " ".join(f"p{i}" for i in range(25))
    frags = fragmentar(texto, chunking="ventana", tamano=10, solapamiento=3, metadatos=False)
    palabras = [f.split() for f in frags]
    assert all(len(p) <= 10 for p in palabras)
    assert palabras[0][-3:] == palabras[1][:3]
    assert set(sum(palabras, [])) == {f"p{i}" for i in range(25)}


def test_ventana_rechaza_solapamiento_mayor_o_igual_al_tamano():
    with pytest.raises(ValueError):
        fragmentar(DOC, chunking="ventana", tamano=5, solapamiento=5)


@pytest.mark.parametrize("cfg", [
    {"chunking": "seccion"},
    {"chunking": "parrafo"},
    {"chunking": "ventana", "tamano": 60, "solapamiento": 20},
])
def test_ningun_chunking_rompe_la_evidencia_del_dev(cfg):
    """Cada frase de evidencia tiene que quedar entera en algún fragmento."""
    frags = [norm(f) for doc in sorted(CORPUS.glob("*.md"))
             for f in fragmentar(doc.read_text(encoding="utf-8"), metadatos=True, **cfg)]
    preguntas = RAIZ / "datos" / "preguntas_recuperacion_dev.jsonl"
    for linea in preguntas.read_text(encoding="utf-8").splitlines():
        for ev in json.loads(linea)["evidencia"]:
            assert any(norm(ev) in f for f in frags), ev


# ---------- selección ----------

SIMS = np.array([0.30, 0.82, 0.10, 0.79, 0.55])


def test_seleccionar_top_k_en_orden():
    assert seleccionar(SIMS, top_k=3) == [1, 3, 4]


def test_seleccionar_umbral_descarta_los_bajos():
    assert seleccionar(SIMS, top_k=5, umbral=0.5) == [1, 3, 4]


def test_seleccionar_margen_respecto_del_primero():
    assert seleccionar(SIMS, top_k=5, margen=0.05) == [1, 3]


def test_seleccionar_devuelve_al_menos_uno():
    assert seleccionar(SIMS, top_k=3, umbral=0.99) == [1]
