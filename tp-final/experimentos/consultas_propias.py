"""Conjunto propio de consultas para el buscador (Parte 2), escrito después de ajustar el buscador con las 60 consultas de
desarrollo de la cátedra para tener una medición que no se ajustó a esos fallos.

    uv run python -m experimentos.consultas_propias

Escribe `datos/consultas_propias.jsonl` con el mismo formato que `rag/consultas_dev.jsonl` y comprueba que cada
fragmento de evidencia aparece literal en algún párrafo de las normas originales. Los números de los valores son los de
`normas/original`."""

import json
import sys
from pathlib import Path

from admision.evaluar_rag import _normalizar

from buscador import BuscadorNormas

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "datos" / "consultas_propias.jsonl"

# (tipo, consulta, [(sección, fragmento literal)])
CONSULTAS = [
    # estilo agente: frases cortas con las palabras del tema
    ("agente", "registro de paciente sin documento",
     [("NOR-ADM-01", "Si el paciente no presenta documento, se hace un registro provisorio")]),
    ("agente", "plazo del ECG por dolor torácico con ambulancia",
     [("NOR-TDE-01", "P-TDE-1 = 10 min"), ("NOR-TDE-04", "P-TDE-5 = 5 min")]),
    ("agente", "plazo código ACV", [("NOR-TDE-02", "P-TDE-2 = 10 min")]),
    ("agente", "plazo código sepsis posible sin signos de shock", [("NOR-TDE-03", "P-TDE-4 = 60 min")]),
    ("agente", "código sepsis con signos de shock llegada en ambulancia",
     [("NOR-TDE-03", "P-TDE-3 = 15 min"), ("NOR-TDE-04", "P-TDE-5 = 5 min")]),
    ("agente", "verificar afiliación obra social número de afiliado",
     [("NOR-COB-02", "la admisión verifica la afiliación con la entidad")]),
    ("agente", "accidente de trabajo ART CUIL verificación",
     [("NOR-COB-02", "usando el CUIL del paciente como número de afiliado")]),
    ("agente", "número de afiliado con terminación reservada",
     [("NOR-COB-04", "la ficha registra al paciente como paciente sin cobertura")]),
    ("agente", "afiliación inactiva notificar a la entidad",
     [("NOR-COB-03", "Si la afiliación declarada resulta inactiva al verificarla, no se notifica a la entidad.")]),
    ("agente", "paciente no puede responder y no tiene acompañante cobertura",
     [("NOR-COB-01", "no se le pregunta a nadie")]),
    ("agente", "pasaporte nivel de triage urgente tipo de registro",
     [("NOR-ADM-03", "se hace un registro provisorio aunque el documento esté a la vista")]),
    ("agente", "paciente mayor box antes del registro",
     [("NOR-ADM-02", "se ubica en el box antes del registro, cualquiera sea su nivel de triage")]),
    ("agente", "nivel de triage ubicar en el box antes de registrar",
     [("NOR-ADM-01", "primero se ubica al paciente y después se lo registra")]),
    ("agente", "aviso al Servicio Social paciente sin cobertura",
     [("NOR-COB-03", "La admisión da aviso al Servicio Social del hospital")]),
    ("agente", "credencial presentada entidad y número de afiliado",
     [("NOR-COB-01", "reemplazan la consulta")]),
    # coloquiales
    ("coloquial", "Mi paciente dice que se cayó de un techo trabajando, ¿le aviso a su prepaga?",
     [("NOR-COB-02", "No se notifica a la obra social ni a la prepaga.")]),
    ("coloquial", "Vino un chico con una cédula y está muy grave, ¿lo anoto como definitivo?",
     [("NOR-ADM-03", "se hace un registro provisorio aunque el documento esté a la vista")]),
    ("coloquial", "El señor ya se fue a internación, ¿todavía le puedo cargar los datos?",
     [("NOR-ADM-01", "El registro se hace antes del egreso del paciente de la guardia")]),
    ("coloquial", "¿Le puedo pedir plata a alguien que no tiene obra social antes de atenderlo?",
     [("NOR-COB-03", "No se le pide pago, garantía ni autorización")]),
    ("coloquial", "La prepaga quiere una autorización antes de que lo atiendan, ¿se la tramito?",
     [("NOR-COB-02", "La atención de urgencia no requiere autorización ni validación previa de la obra social o la prepaga.")]),
    ("coloquial", "Se queja de dolor de pecho y todavía no tiene box, ¿espero a ubicarlo para el electro?",
     [("NOR-TDE-01", "El ECG se solicita aunque el paciente todavía no tenga box asignado")]),
    ("coloquial", "Sospechan una infección generalizada, ¿tengo que ordenar yo los antibióticos?",
     [("NOR-TDE-03", "La admisión no interviene en esas decisiones.")]),
    ("coloquial", "Llegó con un brazo caído y la boca torcida, ¿espero que lo vea el médico para dar el aviso?",
     [("NOR-TDE-02", "No se espera la evaluación médica ni las imágenes para activarlo.")]),
    ("coloquial", "El hijo trajo el DNI después de que lo anoté provisorio, ¿qué hago?",
     [("NOR-ADM-01", "se completa el registro: antes del egreso se hace el registro definitivo con ese documento")]),
    ("coloquial", "Es un caso gravísimo, ¿le pregunto primero la obra social o lo paso al box?",
     [("NOR-COB-01", "ningún trámite de cobertura (consulta, verificación, notificación a la entidad ni aviso al Servicio Social) se hace antes de ubicar al paciente en el box")]),
    ("coloquial", "Vino caminando con dolor de pecho, ¿le descuento algo al plazo del electro?",
     [("NOR-TDE-04", "Si llegó por sus propios medios, el plazo es el de la sección del circuito, sin cambios.")]),
    ("coloquial", "La entidad dice activo pero el número termina en siete, ¿lo cargo con cobertura?",
     [("NOR-COB-04", "la ficha registra al paciente como paciente sin cobertura, aunque la entidad informe la afiliación activa")]),
    ("coloquial", "Una señora de noventa años con nivel 5, ¿la dejo esperando mientras la registro?",
     [("NOR-ADM-02", "se ubica en el box antes del registro, cualquiera sea su nivel de triage")]),
    # numéricas
    ("numerica", "¿Con qué nivel de triage el pasaporte obliga a un registro provisorio?",
     [("NOR-ADM-03", "P-ADM-3 = nivel 2")]),
    ("numerica", "¿A partir de cuántos años un paciente se considera mayor para ubicarlo antes en el box?",
     [("NOR-ADM-02", "P-ADM-2 = 67 años")]),
    ("numerica", "¿Cuántos minutos se restan al plazo si el paciente llega en ambulancia?",
     [("NOR-TDE-04", "P-TDE-5 = 5 min")]),
    ("numerica", "¿Qué dígito final del número de afiliado lleva a sin cobertura?",
     [("NOR-COB-04", "P-COB-2 = 7")]),
    ("numerica", "¿Cuántos días tiene la entidad para validar después de la notificación?",
     [("NOR-COB-02", "P-COB-1 = 3 días")]),
    ("numerica", "¿En cuántos minutos hay que activar el código sepsis en un caso probable?",
     [("NOR-TDE-03", "P-TDE-3 = 15 min")]),
    # distractoras: otras áreas del hospital
    ("distractora", "El médico mandó a internar a un paciente con tuberculosis, ¿en qué tipo de habitación va?",
     [("NOR-INT-02", "se interna en una habitación de aislamiento respiratorio con presión negativa")]),
    ("distractora", "¿Puede compartir habitación un hombre con una mujer en la sala general?",
     [("NOR-INT-04", "Dos pacientes comparten habitación solo si son del mismo sexo.")]),
    ("distractora", "¿A qué hospital derivo a un paciente que no tiene obra social?",
     [("NOR-DER-01", "se lo deriva a un efector público de la red")]),
    ("distractora", "¿Cuándo corresponde pedirle a enfermería que vuelva a evaluar al paciente?",
     [("NOR-GUA-03", "Corresponde pedir un retriage a enfermería en dos situaciones")]),
    ("distractora", "No hay cama en terapia intensiva ni se espera ninguna alta, ¿qué hago?",
     [("NOR-INT-05", "el paciente se deriva a otro establecimiento según NOR-DER-01.")]),
    ("distractora", "¿A qué tipo de box va un paciente de nivel 3?",
     [("NOR-GUA-02", "los niveles 2 y 3, a un box de agudos")]),
    ("distractora", "¿Quién puede cambiar el nivel de triage de un paciente?",
     [("NOR-GUA-01", "El nivel lo asigna y lo modifica solo enfermería.")]),
]


def construir() -> list[dict]:
    buscador = BuscadorNormas(RAIZ / "normas" / "original", expansiones=False)
    textos = {f.seccion: [] for f in buscador.fragmentos}
    for f in buscador.fragmentos:
        textos[f.seccion].append(_normalizar(f.texto))
    filas = []
    for i, (tipo, consulta, evidencia) in enumerate(CONSULTAS, 1):
        for seccion, fragmento in evidencia:
            if not any(_normalizar(fragmento) in t for t in textos[seccion]):
                raise SystemExit(f"p{i:03d}: la evidencia no está literal en {seccion}: {fragmento!r}")
        filas.append({"id": f"p{i:03d}", "tipo": tipo, "consulta": consulta,
                      "evidencia": [{"seccion": s, "texto": t} for s, t in evidencia]})
    return filas


if __name__ == "__main__":
    filas = construir()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas), encoding="utf-8", newline="\n")
    print(f"{len(filas)} consultas escritas en {SALIDA.relative_to(RAIZ)}")
    sys.exit(0)
