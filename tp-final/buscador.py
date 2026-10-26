"""Buscador de las normas del hospital (Parte 2).

`BuscadorNormas(ruta_normas)` indexa las normas de la carpeta que recibe, así que sirve para cualquier versión de los
valores: el texto de las secciones es el mismo y los números se leen de `parametros.yaml` de esa carpeta, nunca están
escritos acá.

Cada fragmento es un párrafo (§) de una sección, con su código y título al principio y la línea `Valores:` con los
parámetros que cita ese párrafo al final. Se busca con BM25 sobre el texto del párrafo más, opcionalmente, las
expansiones de `buscador_expansiones.json` (paráfrasis coloquiales de cada párrafo, que solo se indexan: no se
devuelven)."""

import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from admision.normas import cargar_parametros, linea_de_valores

RUTA_EXPANSIONES = Path(__file__).with_name("buscador_expansiones.json")

PALABRAS_VACIAS = set("""a al algo ante con contra cual cuando cuanto de del desde donde dos e el ella ellos en entre es esa
ese eso esta este esto la las le les lo los me mi mas mismo muy ni no nos o otra otro para pero por porque que quien se si
sin sobre su sus te tiene tengo tienen un una uno unos unas y ya ser son sea hay hace hago hacer puede puedo debe debo
como cual cuales cada todo toda todos todas""".split())


def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def raiz(palabra: str) -> str:
    """Un stemmer mínimo para el español: plurales y terminaciones frecuentes."""
    for sufijo in ("aciones", "uciones", "amiento", "imiento", "ciones", "cion", "mente", "idad", "ando", "iendo",
                   "ados", "adas", "idos", "idas", "ado", "ada", "ido", "ida", "ar", "er", "ir", "es", "s"):
        if len(palabra) - len(sufijo) >= 4 and palabra.endswith(sufijo):
            return palabra[: -len(sufijo)]
    return palabra


def tokens(texto: str, con_raiz: bool = True) -> list[str]:
    palabras = re.findall(r"[a-z0-9]+", normalizar(texto))
    return [raiz(p) if con_raiz else p for p in palabras if p not in PALABRAS_VACIAS]


@dataclass(frozen=True)
class Fragmento:
    id: str
    seccion: str
    texto: str = field(compare=False)


def partir_seccion(codigo: str, cuerpo: str, valores: dict[str, str]) -> list[Fragmento]:
    """Un fragmento por párrafo (§). El encabezado va al principio de cada uno y los valores que cita, al final."""
    lineas = cuerpo.strip().splitlines()
    encabezado = lineas[0].lstrip("# ").strip()
    parrafos = [p.strip() for p in re.split(r"\n\s*\n", "\n".join(lineas[1:])) if p.strip()]
    fragmentos = []
    for p in parrafos:
        m = re.match(r"§(\d+)", p)
        id_parrafo = f"{codigo}#§{m.group(1)}" if m else f"{codigo}#{len(fragmentos) + 1}"
        vals = linea_de_valores(p, valores)
        texto = f"{encabezado}\n{p}" + (f"\n{vals}" if vals else "")
        fragmentos.append(Fragmento(id_parrafo, codigo, texto))
    return fragmentos


class BuscadorNormas:
    """BM25 sobre párrafos de las normas. `k_entorno` es cuántos fragmentos trae `buscar_normativa`."""

    def __init__(self, ruta_normas: Path, *, granularidad: str = "parrafo", k_entorno: int = 3, k1: float = 1.2,
                 b: float = 0.75, expansiones: bool = True, con_raiz: bool = True):
        self.k_entorno = k_entorno
        self.k1, self.b, self.con_raiz = k1, b, con_raiz
        ruta = Path(ruta_normas)
        valores = cargar_parametros(ruta)
        extra = {}
        if expansiones and RUTA_EXPANSIONES.exists():
            extra = json.loads(RUTA_EXPANSIONES.read_text(encoding="utf-8"))
        self.fragmentos: list[Fragmento] = []
        for archivo in sorted(ruta.glob("NOR-*.md")):
            cuerpo = archivo.read_text(encoding="utf-8").strip()
            if granularidad == "seccion":
                vals = linea_de_valores(cuerpo, valores)
                self.fragmentos.append(Fragmento(archivo.stem, archivo.stem, cuerpo + (f"\n{vals}" if vals else "")))
            else:
                self.fragmentos.extend(partir_seccion(archivo.stem, cuerpo, valores))
        docs = [tokens(f.texto + "\n" + extra.get(f.id, ""), con_raiz) for f in self.fragmentos]
        self._tf = [Counter(d) for d in docs]
        self._largo = [len(d) for d in docs]
        self._prom = sum(self._largo) / len(docs)
        df = Counter(t for tf in self._tf for t in tf)
        n = len(docs)
        self._idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def puntajes(self, consulta: str) -> list[float]:
        q = tokens(consulta, self.con_raiz)
        puntajes = []
        for tf, largo in zip(self._tf, self._largo):
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self._idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * largo / self._prom))
            puntajes.append(s)
        return puntajes

    def recuperar(self, consulta: str, k: int) -> list[Fragmento]:
        p = self.puntajes(consulta)
        orden = sorted(range(len(p)), key=lambda i: (-p[i], i))
        return [self.fragmentos[i] for i in orden[:k]]
