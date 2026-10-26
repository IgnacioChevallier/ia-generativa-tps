"""Valida el oráculo contra las 150 fichas esperadas de la cátedra (50 casos de práctica x normas original, b y c).

    uv run python -m curado.validar_oraculo

Imprime, por versión de normas, cuántos casos coinciden en los 8 campos y en la verificación, y el detalle de cada
diferencia."""

import sys
from pathlib import Path

from admision.casos import cargar_esperadas, leer_jsonl

from .oraculo import cargar_parametros, ficha_esperada

RAIZ = Path(__file__).resolve().parent.parent


def validar(detalle: bool = True) -> int:
    casos = leer_jsonl(RAIZ / "practica" / "casos.jsonl")
    diferencias = 0
    for version in ("original", "b", "c"):
        p = cargar_parametros(RAIZ / "normas" / version)
        esperadas = cargar_esperadas(RAIZ / "practica" / f"esperadas-{version}.jsonl")
        ok = 0
        for caso in casos:
            calculada = ficha_esperada(caso, p)
            esperada = esperadas[caso["id"]]
            malos = [k for k in esperada["ficha"] if calculada["ficha"][k] != esperada["ficha"][k]]
            ver_ok = (calculada["verificacion"]["requerida"] == esperada["verificacion"]["requerida"]
                      and sorted(calculada["verificacion"]["prohibidas"])
                      == sorted(esperada["verificacion"]["prohibidas"]))
            if not malos and ver_ok:
                ok += 1
                continue
            diferencias += 1
            if detalle:
                print(f"[{version}] {caso['id']}: campos distintos {malos}, verificación {'ok' if ver_ok else 'DISTINTA'}")
                for k in malos:
                    print(f"    {k}: esperado {esperada['ficha'][k]!r}  calculado {calculada['ficha'][k]!r}")
                if not ver_ok:
                    print(f"    verificacion esperada {esperada['verificacion']}  calculada {calculada['verificacion']}")
        print(f"normas {version}: {ok}/{len(casos)} casos coinciden")
    return diferencias


if __name__ == "__main__":
    sys.exit(1 if validar() else 0)
