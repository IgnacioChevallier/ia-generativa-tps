"""Trayectorias de entrenamiento: un experto juega cada caso contra el `Entorno` de la cátedra y el buscador del grupo.

Una trayectoria es la lista de pasos (herramienta, argumentos, observación) que lleva a la ficha correcta. Las
observaciones son las reales: las produce `admision.entorno.Entorno`, y las búsquedas las responde `BuscadorNormas` con
las normas de la versión que se esté jugando. Así el modelo aprende a leer los números del texto que trae el buscador
y no a memorizarlos.

El experto no inventa la ficha: la calcula `curado.oraculo` (validado contra las 150 fichas de práctica) con los
parámetros de la versión de normas, y `admision.comparar` confirma que la trayectoria resuelve los 9 controles. Las
que no (por ejemplo, porque el buscador no trajo un número necesario) se descartan."""

import hashlib
import random

from admision.casos import Caso
from admision.catalogo import APELLIDOS, NOMBRES
from admision.comparar import comparar
from admision.entorno import K_POR_DEFECTO, Entorno
from admision.generador import NO_RESPONDE

from .historial import caso_desde_fila
from .oraculo import _ultimo_digito, entidad_de_consulta, ficha_esperada

# Cada necesidad de información es una búsqueda con varias formulaciones; el experto elige una al azar (con semilla).
CONSULTAS = {
    "box": ["ubicación en el box antes del registro según el nivel de triage y la edad",
            "edad y nivel de triage para ubicar al paciente en el box antes de registrarlo",
            "cuándo se ubica al paciente en el box antes del registro"],
    "pasaporte": ["registro con pasaporte o cédula según el nivel de triage",
                  "pasaporte o cédula en un nivel de triage urgente: registro provisorio o definitivo"],
    "reservado": ["terminación reservada del número de afiliado",
                  "dígito reservado del número de afiliado: paciente sin cobertura"],
    "ecg": ["plazo del electrocardiograma por dolor torácico", "ECG por dolor torácico: plazo en minutos"],
    "codigo_acv": ["plazo del Código ACV por signos neurológicos focales de inicio súbito",
                   "activar el Código ACV: plazo en minutos"],
    "sepsis_probable": ["plazo del Código Sepsis con sospecha probable o con signos de shock",
                        "Código Sepsis probable o con shock: plazo en minutos"],
    "sepsis_posible": ["plazo del Código Sepsis con sospecha posible sin signos de shock",
                       "Código Sepsis posible sin shock: plazo en minutos"],
    "ambulancia": ["minutos que se restan al plazo del circuito si el paciente llegó en ambulancia",
                   "llegada en ambulancia: plazo del circuito menos minutos"],
}

# Los parámetros cuyo valor tiene que figurar en lo que trae cada búsqueda para poder decidir.
PARAMETROS_POR_NECESIDAD = {"box": ("P-ADM-1", "P-ADM-2"), "pasaporte": ("P-ADM-3",), "reservado": ("P-COB-2",),
                            "ecg": ("P-TDE-1",), "codigo_acv": ("P-TDE-2",), "sepsis_probable": ("P-TDE-3",),
                            "sepsis_posible": ("P-TDE-4",), "ambulancia": ("P-TDE-5",)}


def caso_de_fila(fila: dict) -> Caso:
    """Reconstruye el caso que vio el operador. Lo que el historial no trae (nombre, motivo de no responder, id de
    paciente) se completa de forma determinista a partir del id de la fila."""
    c = caso_desde_fila(fila)
    r = random.Random(int(hashlib.sha256(fila["id"].encode()).hexdigest(), 16))
    sexo = r.choice("FM")
    c["paciente_id"] = f"P-{1000 + (int(fila['id'].split('-')[1]) * 37) % 9000}"
    c["nombre"] = f"{r.choice(NOMBRES[sexo])} {r.choice(APELLIDOS)}"
    c["no_responde_porque"] = None if c["puede_responder"] else r.choice(NO_RESPONDE)
    cred = [tuple(x) for x in c["credenciales"]]
    if cred:  # con credencial, lo que el paciente contestaría es la entidad que vale
        prepagas = [x for x in cred if x[0] == "prepaga"]
        c["declarada"] = list(prepagas[0] if len(cred) == 2 and prepagas else cred[0])
    for x in cred:  # la credencial que el operador no verificó no se consulta nunca: su estado no importa
        c["afiliaciones"].setdefault(f"{x[1]}|{x[2]}", True)
    del c["consultada"]
    c["credenciales"] = tuple(tuple(x) for x in c["credenciales"])
    for k in ("declarada", "art"):
        if c[k] is not None:
            c[k] = tuple(c[k])
    return Caso(**c)


def _necesidades(caso: Caso, ficha: dict) -> list[str]:
    """Qué números hay que buscar para decidir esta ficha: los que cambian entre versiones de las normas."""
    necesidades = ["box"]
    if caso.documento_tipo in ("pasaporte", "cédula"):
        necesidades.append("pasaporte")
    if not caso.trabajo and entidad_de_consulta(caso.como_dict()) is not None:
        necesidades.append("reservado")
    if ficha["circuito"] == "ecg":
        necesidades.append("ecg")
    elif ficha["circuito"] == "codigo_acv":
        necesidades.append("codigo_acv")
    elif ficha["circuito"] == "codigo_sepsis":
        necesidades.append("sepsis_posible" if caso.sepsis == "posible, sin signos de shock" else "sepsis_probable")
    if ficha["circuito"] != "ninguno" and caso.llegada == "en ambulancia":
        necesidades.append("ambulancia")
    return necesidades


def _fundamentos(caso: Caso, ficha: dict, p: dict) -> list[str]:
    f = ["NOR-ADM-01"]
    if caso.edad >= p["P-ADM-2"] and caso.nivel > p["P-ADM-1"]:
        f.append("NOR-ADM-02")
    if caso.documento_tipo in ("pasaporte", "cédula") and caso.nivel <= p["P-ADM-3"]:
        f.append("NOR-ADM-03")
    f += ["NOR-COB-01", "NOR-COB-02"]
    entidad = None if caso.trabajo else entidad_de_consulta(caso.como_dict())
    if entidad and _ultimo_digito(entidad[2]) == p["P-COB-2"]:
        f.append("NOR-COB-04")
    if ficha["cobertura"] == "sin_cobertura":
        f.append("NOR-COB-03")
    f += {"ecg": ["NOR-TDE-01"], "codigo_acv": ["NOR-TDE-02"], "codigo_sepsis": ["NOR-TDE-03"],
          "ninguno": []}[ficha["circuito"]]
    if ficha["circuito"] != "ninguno" and caso.llegada == "en ambulancia":
        f.append("NOR-TDE-04")
    return list(dict.fromkeys(f))


def jugar(caso: Caso, buscador, p: dict, azar: random.Random) -> dict | None:
    """Juega `caso` con la política del experto. Devuelve la trayectoria, o None si el buscador no trae algún número
    necesario o la ficha no resuelve los 9 controles."""
    esperado = ficha_esperada(caso.como_dict(), p)
    ficha = esperado["ficha"]
    env = Entorno(caso, buscador)
    pasos = []

    def paso(herramienta: str, argumentos: dict) -> None:
        obs, _ = env.paso(herramienta, argumentos)
        pasos.append({"herramienta": herramienta, "argumentos": argumentos, "observacion": obs})

    paso("leer_triage", {"paciente_id": caso.paciente_id})

    k = getattr(buscador, "k_entorno", K_POR_DEFECTO)
    for necesidad in _necesidades(caso, ficha):
        formas = CONSULTAS[necesidad][:]
        azar.shuffle(formas)
        consulta = next((c for c in formas if _trae(necesidad, buscador.recuperar(c, k))), None)
        if consulta is None:
            return None
        paso("buscar_normativa", {"consulta": consulta})

    if caso.trabajo:
        paso("preguntar", {"paciente_id": caso.paciente_id, "a_quien": "paciente" if caso.puede_responder
                           else "acompanante", "tema": "art"})
        paso("verificar_afiliacion", {"entidad": caso.art[0], "numero_afiliado": caso.art[1]})
    elif caso.credenciales:
        _, entidad, numero = entidad_de_consulta(caso.como_dict())
        paso("verificar_afiliacion", {"entidad": entidad, "numero_afiliado": numero})
    elif caso.puede_responder or caso.acompanante:
        paso("preguntar", {"paciente_id": caso.paciente_id, "a_quien": "paciente" if caso.puede_responder
                           else "acompanante", "tema": "cobertura"})
        if caso.declarada:
            paso("verificar_afiliacion", {"entidad": caso.declarada[1], "numero_afiliado": caso.declarada[2]})

    paso("registrar_decision", {**ficha, "fundamentos": _fundamentos(caso, ficha, p)})

    resultado = comparar({"caso": caso.id, "ficha": ficha, "verificacion": esperado["verificacion"]},
                         env.decision, env.log)
    return {"id": caso.id, "paciente_id": caso.paciente_id, "pasos": pasos, "ficha": ficha} \
        if resultado["resuelto"] else None


def _trae(necesidad: str, fragmentos: list) -> bool:
    texto = "\n".join(f if isinstance(f, str) else f.texto for f in fragmentos)
    return all(f"{c} = " in texto for c in PARAMETROS_POR_NECESIDAD[necesidad])
