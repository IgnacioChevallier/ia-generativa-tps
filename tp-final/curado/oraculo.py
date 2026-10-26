"""Oráculo de la ficha: calcula la ficha correcta de un caso aplicando las normas escritas (NOR-ADM, NOR-COB, NOR-TDE)
más las costumbres del hospital que se descubrieron en el historial (ver costumbres.md).

El kit de la cátedra no trae este cálculo (`admision.comparar` solo compara contra fichas esperadas ya dadas), así que se
escribe acá y se valida contra las 150 fichas esperadas de `practica/` (50 casos x normas original, b y c):

    uv run python -m curado.validar_oraculo

Los valores salen siempre de `parametros.yaml` de la carpeta de normas que se recibe, nunca de números fijos."""

from pathlib import Path

import yaml

CIRCUITO_POR_MOTIVO = {"dolor torácico": "ecg", "signos neurológicos focales de inicio súbito": "codigo_acv"}

# Costumbre del hospital (no está en las normas): el aviso al voluntariado se da a los pacientes mayores que llegan sin
# acompañante. El umbral sale del historial (curado/costumbres.py lo mide): los operadores que la siguen la cumplen sin
# excepción. No depende de las normas, así que no cambia entre las versiones original, b y c.
EDAD_AVISO_VOLUNTARIADO = 75


def voluntariado_costumbre(caso: dict) -> bool:
    return not caso["acompanante"] and caso["edad"] >= EDAD_AVISO_VOLUNTARIADO


def cargar_parametros(ruta_normas: Path) -> dict[str, int]:
    datos = yaml.safe_load((Path(ruta_normas) / "parametros.yaml").read_text(encoding="utf-8"))
    return {p["codigo"]: p["valor"] for p in datos["parametros"]}


def _ultimo_digito(numero: str) -> int | None:
    for ch in reversed(numero):
        if ch.isdigit():
            return int(ch)
    return None


def circuito_y_plazo(caso: dict, p: dict) -> tuple[str, int | None]:
    """NOR-TDE-01 a 04. La sospecha de sepsis y el motivo son excluyentes en los datos de la cátedra."""
    if caso["sepsis"] != "no":
        circuito = "codigo_sepsis"
        base = p["P-TDE-4"] if caso["sepsis"] == "posible, sin signos de shock" else p["P-TDE-3"]
    elif caso["motivo"] in CIRCUITO_POR_MOTIVO:
        circuito = CIRCUITO_POR_MOTIVO[caso["motivo"]]
        base = p["P-TDE-1"] if circuito == "ecg" else p["P-TDE-2"]
    else:
        return "ninguno", None
    return circuito, base - (p["P-TDE-5"] if caso["llegada"] == "en ambulancia" else 0)


def registro(caso: dict, p: dict) -> tuple[str, str | None]:
    """NOR-ADM-01 §2-§3 y NOR-ADM-03: el número de documento se anota siempre que haya documento."""
    tipo, numero = caso["documento_tipo"], caso["documento_numero"]
    if not numero:
        return "provisorio", None
    if tipo in ("pasaporte", "cédula") and caso["nivel"] <= p["P-ADM-3"]:
        return "provisorio", numero
    return "definitivo", numero


def box_antes(caso: dict, p: dict) -> bool:
    """NOR-ADM-01 §4 y NOR-ADM-02."""
    return caso["nivel"] <= p["P-ADM-1"] or caso["edad"] >= p["P-ADM-2"]


def entidad_de_consulta(caso: dict) -> tuple[str, str, str] | None:
    """La (tipo, entidad, número) con que se verifica la cobertura de una obra social o prepaga (NOR-COB-01).

    Con credencial, la credencial reemplaza la consulta (§4); con dos credenciales (obra social y prepaga) se toma la
    prepaga (costumbre: ver costumbres.md). Sin credencial se consulta al paciente y, si no puede responder, a su
    acompañante (§1-§3). Si no puede responder y no tiene acompañante, queda sin cobertura (§3)."""
    cred = [tuple(c) for c in caso["credenciales"]]
    if cred:
        prepagas = [c for c in cred if c[0] == "prepaga"]
        return prepagas[0] if len(cred) == 2 and prepagas else cred[0]
    if caso["puede_responder"] or caso["acompanante"]:
        return tuple(caso["declarada"]) if caso["declarada"] else None
    return None


def cobertura(caso: dict, p: dict) -> dict:
    """NOR-COB-02 a 04. Devuelve cobertura, entidad_a_notificar y la verificación que corresponde."""
    nombres_credenciales = [c[1] for c in caso["credenciales"]]
    if caso["trabajo"]:  # NOR-COB-02 §5: la cobertura es la ART, no la obra social ni la prepaga
        art, cuil = caso["art"]
        return {"cobertura": "art", "entidad_a_notificar": art, "requerida": [art, cuil],
                "prohibidas": list(dict.fromkeys(
                    nombres_credenciales + ([caso["declarada"][1]] if caso["declarada"] else [])))}
    ent = entidad_de_consulta(caso)
    prohibidas = [n for n in nombres_credenciales if not ent or n != ent[1]]
    if ent is None:
        return {"cobertura": "sin_cobertura", "entidad_a_notificar": None, "requerida": None,
                "prohibidas": prohibidas}
    tipo, nombre, numero = ent
    activa = caso["afiliaciones"].get(f"{nombre}|{numero}", False)
    reservada = _ultimo_digito(numero) == p["P-COB-2"]
    if reservada:  # NOR-COB-04: sin cobertura, pero se notifica a la entidad esté activa o no
        cob, notif = "sin_cobertura", nombre
    elif activa:
        cob, notif = tipo, nombre
    else:  # NOR-COB-03 §4: afiliación inactiva, no se notifica
        cob, notif = "sin_cobertura", None
    return {"cobertura": cob, "entidad_a_notificar": notif, "requerida": [nombre, numero],
            "prohibidas": prohibidas}


def ficha_esperada(caso: dict, p: dict, voluntariado=voluntariado_costumbre) -> dict:
    """{"ficha": {8 campos}, "verificacion": {"requerida", "prohibidas"}}. `voluntariado(caso) -> bool` es la costumbre
    del aviso al voluntariado."""
    reg, numero = registro(caso, p)
    circuito, plazo = circuito_y_plazo(caso, p)
    cob = cobertura(caso, p)
    return {
        "ficha": {
            "registro": reg,
            "numero_documento": numero,
            "box_antes_del_registro": box_antes(caso, p),
            "circuito": circuito,
            "plazo_circuito_min": plazo,
            "cobertura": cob["cobertura"],
            "entidad_a_notificar": cob["entidad_a_notificar"],
            "aviso_al_voluntariado": bool(voluntariado(caso)),
        },
        "verificacion": {"requerida": cob["requerida"], "prohibidas": cob["prohibidas"]},
    }
