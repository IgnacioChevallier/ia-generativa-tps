"""Lee `historial/historial.csv` y convierte cada fila en el caso que el oráculo y el entorno entienden.

Una fila es una admisión pasada: lo que decía el triage, lo que averiguó el operador y la ficha que completó. De lo que
averiguó el operador solo se conoce la afiliación que verificó (entidad, número y respuesta): si verificó otra cosa
que la correcta, el estado de la correcta no se conoce y queda fuera de `afiliaciones`."""

import csv
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTA_HISTORIAL = RAIZ / "historial" / "historial.csv"

_CREDENCIAL = re.compile(r"^(?P<entidad>.+?) \((?P<tipo>obra social|prepaga)\) (?P<numero>\S+)$")
_ART = re.compile(r"^(?P<art>.+? ART) CUIL (?P<cuil>\S+)$")

CAMPOS_FICHA = ["registro", "numero_documento", "box_antes_del_registro", "circuito", "plazo_circuito_min", "cobertura",
                "entidad_a_notificar", "aviso_al_voluntariado"]


def leer_historial(ruta: Path = RUTA_HISTORIAL) -> list[dict]:
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _credencial(texto: str) -> tuple[str, str, str]:
    m = _CREDENCIAL.match(texto.strip())
    return ("obra_social" if m["tipo"] == "obra social" else "prepaga", m["entidad"], m["numero"])


def caso_desde_fila(fila: dict) -> dict:
    """El caso (mismas claves que `admision.casos.Caso`) que describe la fila. `declarada` es lo que el operador anotó
    como respuesta a la consulta de cobertura: None si el paciente dijo que no tiene, y también None si no se
    consultó (`consultada` distingue los dos). Los datos que el historial no trae (nombre, motivo de no responder)
    quedan en None."""
    cred = [_credencial(c) for c in fila["credenciales"].split(";") if c.strip()]
    declarada_txt = fila["cobertura_declarada"].strip()
    declarada = _credencial(declarada_txt) if declarada_txt not in ("", "ninguna") else None
    m = _ART.match(fila["art_declarada"].strip()) if fila["art_declarada"].strip() else None
    afiliaciones = {}
    if fila["entidad_verificada"]:
        afiliaciones[f"{fila['entidad_verificada']}|{fila['numero_verificado']}"] = fila["respuesta_verificacion"] == "activa"
    trabajo = fila["lesion_trabajo"] if fila["lesion_trabajo"] != "no" else None
    return {
        "id": fila["id"], "paciente_id": None, "nombre": None,
        "edad": int(fila["edad"]), "nivel": int(fila["nivel"]), "motivo": fila["motivo"],
        "nota": fila["nota_enfermeria"], "sepsis": fila["sospecha_sepsis"], "llegada": fila["llegada"],
        "documento_tipo": fila["documento_tipo"] or None, "documento_numero": fila["documento_numero"] or None,
        "credenciales": [list(c) for c in cred], "puede_responder": fila["puede_responder"] == "sí",
        "no_responde_porque": None, "acompanante": fila["acompanante"] or None, "trabajo": trabajo,
        "declarada": list(declarada) if declarada else None, "consultada": declarada_txt != "",
        "art": [m["art"], m["cuil"]] if m else None, "afiliaciones": afiliaciones,
    }


def ficha_de_fila(fila: dict) -> dict:
    """La ficha que completó el operador, con los tipos de la ficha esperada (bool, int, None)."""
    def vacio(x):
        return x or None
    return {
        "registro": fila["registro"], "numero_documento": vacio(fila["numero_documento"]),
        "box_antes_del_registro": fila["box_antes_del_registro"] == "sí", "circuito": fila["circuito"],
        "plazo_circuito_min": int(fila["plazo_circuito_min"]) if fila["plazo_circuito_min"] else None,
        "cobertura": fila["cobertura"], "entidad_a_notificar": vacio(fila["entidad_a_notificar"]),
        "aviso_al_voluntariado": fila["aviso_al_voluntariado"] == "sí",
    }
