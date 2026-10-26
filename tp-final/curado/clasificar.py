"""Clasifica las 2.000 filas del historial como correcta, error o ruido.

    uv run python -m curado.clasificar

Criterio (el de la consigna):
- error: la fila viola una norma escrita. Se compara la ficha de la fila con la que calcula el oráculo con las normas
  originales (`normas/original`, las vigentes cuando se armó el historial) y se anota qué norma se violó.
- ruido: la fila no viola ninguna norma pero se aparta de una costumbre del hospital: hace algo que las normas no cubren
  y que no es lo que hacen casi todos los operadores en esa situación (ver `curado/costumbres.py`).
- correcta: todas las demás.

Si una fila tiene un error y además se aparta de una costumbre, es error (viola una norma escrita).

Salidas: `historial_clasificado.csv` (id,tipo) en la raíz y `curado/detalle_clasificacion.jsonl` con, por fila, los
motivos."""

import csv
import json
from collections import Counter
from pathlib import Path

from .historial import RAIZ, caso_desde_fila, ficha_de_fila, leer_historial
from .oraculo import cargar_parametros, ficha_esperada, voluntariado_costumbre

SALIDA_CSV = RAIZ / "historial_clasificado.csv"
SALIDA_DETALLE = RAIZ / "curado" / "detalle_clasificacion.jsonl"
SALIDA_RESUMEN = RAIZ / "curado" / "resumen_clasificacion.json"


def _norma_del_campo(campo: str, caso: dict, p: dict, esperada: dict) -> str:
    """La norma escrita que fija el valor de `campo` en este caso."""
    if campo in ("registro", "numero_documento"):
        pasaporte_o_cedula = caso["documento_tipo"] in ("pasaporte", "cédula")
        return "NOR-ADM-03" if pasaporte_o_cedula and caso["nivel"] <= p["P-ADM-3"] else "NOR-ADM-01"
    if campo == "box_antes_del_registro":
        mayor = caso["edad"] >= p["P-ADM-2"] and caso["nivel"] > p["P-ADM-1"]
        return "NOR-ADM-02" if mayor else "NOR-ADM-01"
    if campo == "circuito":
        return {"ecg": "NOR-TDE-01", "codigo_acv": "NOR-TDE-02", "codigo_sepsis": "NOR-TDE-03",
                "ninguno": "NOR-TDE-01 a 03"}[esperada["circuito"]]
    if campo == "plazo_circuito_min":
        return "NOR-TDE-04" if caso["llegada"] == "en ambulancia" else {
            "ecg": "NOR-TDE-01", "codigo_acv": "NOR-TDE-02", "codigo_sepsis": "NOR-TDE-03"}.get(
                esperada["circuito"], "NOR-TDE-01 a 03")
    if caso["trabajo"]:
        return "NOR-COB-02 §5"
    return "NOR-COB-04" if campo in ("cobertura", "entidad_a_notificar") and _termina_en_reservado(caso, p) \
        else "NOR-COB-03"


def _termina_en_reservado(caso: dict, p: dict) -> bool:
    for cred in caso["credenciales"] or ([caso["declarada"]] if caso["declarada"] else []):
        digitos = [ch for ch in cred[2] if ch.isdigit()]
        if digitos and int(digitos[-1]) == p["P-COB-2"]:
            return True
    return False


def clasificar_fila(fila: dict, p: dict) -> dict:
    caso = caso_desde_fila(fila)
    ficha = ficha_de_fila(fila)
    errores, desvios = [], []

    verificada = [fila["entidad_verificada"], fila["numero_verificado"]]
    if len(caso["credenciales"]) == 2 and not caso["trabajo"]:
        elegida = next((c for c in caso["credenciales"] if [c[1], c[2]] == verificada), None)
        if elegida is not None and elegida[0] != "prepaga":
            # Con dos credenciales las normas no dicen cuál vale: la costumbre es la prepaga. Quien verificó la obra
            # social se aparta de la costumbre, y el resto de su ficha se evalúa respecto de la credencial que eligió.
            desvios.append({"costumbre": "dos_credenciales_prepaga", "hizo": f"verificó {elegida[1]} (obra social)"})
            caso = {**caso, "credenciales": [list(elegida)]}

    esperado = ficha_esperada(caso, p)
    esperada = esperado["ficha"]
    ver = esperado["verificacion"]

    verificacion_ok = verificada == ver["requerida"] if ver["requerida"] is not None else not fila["entidad_verificada"]
    if fila["entidad_verificada"] and fila["entidad_verificada"] in ver["prohibidas"]:
        verificacion_ok = False
    if not verificacion_ok:
        errores.append({"norma": "NOR-COB-02 §2 y §5", "campo": "verificacion",
                        "esperado": ver["requerida"], "real": verificada if fila["entidad_verificada"] else None})

    for campo in ("registro", "numero_documento", "box_antes_del_registro", "circuito", "plazo_circuito_min",
                  "cobertura", "entidad_a_notificar"):
        if campo in ("cobertura", "entidad_a_notificar") and not verificacion_ok:
            continue  # sin el estado de la afiliación correcta no se puede calcular la cobertura
        if ficha[campo] != esperada[campo]:
            errores.append({"norma": _norma_del_campo(campo, caso, p, esperada), "campo": campo,
                            "esperado": esperada[campo], "real": ficha[campo]})

    costumbre = voluntariado_costumbre(caso)
    if ficha["aviso_al_voluntariado"] != costumbre:
        desvios.append({"costumbre": "voluntariado_mayores_sin_acompanante",
                        "hizo": "avisó al voluntariado" if ficha["aviso_al_voluntariado"] else "no avisó al voluntariado",
                        "costumbre_seria": "avisar" if costumbre else "no avisar"})

    tipo = "error" if errores else "ruido" if desvios else "correcta"
    return {"id": fila["id"], "operador": fila["operador"], "tipo": tipo, "aplica": _normas_que_aplican(caso, p, esperada),
            "errores": errores, "desvios": desvios}


def _normas_que_aplican(caso: dict, p: dict, esperada: dict) -> list[str]:
    """Las normas con una regla que esta fila podía violar (para medir qué parte de los casos expuestos se violó)."""
    aplica = []
    if esperada["circuito"] != "ninguno" and caso["llegada"] == "en ambulancia":
        aplica.append("NOR-TDE-04")
    if caso["documento_tipo"] in ("pasaporte", "cédula") and caso["nivel"] <= p["P-ADM-3"]:
        aplica.append("NOR-ADM-03")
    if caso["edad"] >= p["P-ADM-2"] and caso["nivel"] > p["P-ADM-1"]:
        aplica.append("NOR-ADM-02")
    if not caso["trabajo"] and _termina_en_reservado(caso, p):
        aplica.append("NOR-COB-04")
    return aplica


def clasificar(ruta_normas: Path = RAIZ / "normas" / "original") -> list[dict]:
    p = cargar_parametros(ruta_normas)
    return [clasificar_fila(f, p) for f in leer_historial()]


def escribir(resultados: list[dict]) -> None:
    with open(SALIDA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "tipo"])
        w.writerows((r["id"], r["tipo"]) for r in resultados)
    with open(SALIDA_DETALLE, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in resultados)


def resumen(resultados: list[dict]) -> dict:
    por_norma = {}
    for norma in sorted({n for r in resultados for n in r["aplica"]}):
        aplica = sum(norma in r["aplica"] for r in resultados)
        errores = sum(any(e["norma"] == norma for e in r["errores"]) for r in resultados)
        por_norma[norma] = {"filas_expuestas": aplica, "filas_con_error": errores, "tasa": round(errores / aplica, 3)}
    return {
        "filas": len(resultados),
        "por_tipo": dict(Counter(r["tipo"] for r in resultados)),
        "errores_por_norma": por_norma,
        "ruido_por_costumbre": dict(Counter(d["costumbre"] for r in resultados if r["tipo"] == "ruido"
                                            for d in r["desvios"])),
        "ruido_por_operador": dict(sorted(Counter(r["operador"] for r in resultados if r["tipo"] == "ruido").items())),
    }


def main():
    resultados = clasificar()
    escribir(resultados)
    SALIDA_RESUMEN.write_text(json.dumps(resumen(resultados), ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print("filas por tipo:", dict(Counter(r["tipo"] for r in resultados)))
    print("errores por norma:", dict(Counter(e["norma"] for r in resultados for e in r["errores"]).most_common()))
    print("desvíos por costumbre:", dict(Counter(d["costumbre"] for r in resultados for d in r["desvios"])))
    print("ruido por operador:", dict(sorted(Counter(r["operador"] for r in resultados if r["tipo"] == "ruido").items())))
    errores_por_operador = Counter(r["operador"] for r in resultados if r["tipo"] == "error")
    print("errores por operador (min/max):", min(errores_por_operador.values()), max(errores_por_operador.values()))
    print(f"escrito {SALIDA_CSV.name} y {SALIDA_DETALLE.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
