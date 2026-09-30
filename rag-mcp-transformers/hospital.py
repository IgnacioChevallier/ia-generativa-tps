"""Las seis herramientas del asistente del hospital, como funciones de Python puras.

El agente de la parte 2 las envuelve como tools de LangChain y el servidor MCP de la
parte 3 las expone con FastMCP. Sin dependencias de ninguno de los dos: así las
herramientas quedan en un solo lugar. El docstring de cada función es lo que lee el
modelo para decidir cuál llamar.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

API_URL = os.environ.get("HOSPITAL_API_URL", "http://localhost:8765")


def _get(ruta, **params):
    """GET a la API del hospital. Devuelve el JSON como texto; un error también es texto
    (la API incluye las opciones válidas), así el modelo puede corregir el argumento."""
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v})
    url = f"{API_URL}{ruta}" + (f"?{query}" if query else "")
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8")
    except urllib.error.URLError as e:
        return json.dumps({"error": f"no se pudo conectar con la API del hospital: {e.reason}"},
                          ensure_ascii=False)


def buscar_documentos(consulta: str) -> str:
    """Busca en los documentos del hospital (normas y procedimientos que casi no cambian):
    horarios de visita, preparación para estudios y ayunos, documentos que hay que llevar,
    coberturas y autorizaciones, altas, derechos del paciente, donación de sangre, triage
    de la guardia, requisitos para retirar medicamentos, etc. Usala para preguntas de
    "cómo", "qué necesito", "cuándo se puede" o "quiénes pueden". NO informa el estado de
    hoy (camas libres, quién está de guardia, turnos, stock, esperas): eso está en las
    herramientas consultar_*. `consulta` es la pregunta o el tema, en español."""
    from recuperar import buscar  # import tardío: cargar el encoder tarda varios segundos
    return "\n\n---\n\n".join(buscar(consulta))


def consultar_camas(sector: str) -> str:
    """Estado de hoy de las camas de un sector del hospital: total, ocupadas y libres.
    Usala para "¿hay lugar / camas libres / disponibilidad para internar?". `sector` es el
    nombre del sector, por ejemplo "pediatria" o "terapia intensiva". Si el nombre no
    existe, devuelve la lista de sectores válidos."""
    return _get("/camas", sector=sector)


def consultar_guardia(especialidad: str) -> str:
    """Profesionales que están de guardia HOY en una especialidad y su horario. Usala para
    "¿quién está de guardia?" o "¿hay un médico de X esta noche?". `especialidad` es por
    ejemplo "cardiologia" o "pediatria". Si no existe, devuelve las opciones válidas."""
    return _get("/guardia", especialidad=especialidad)


def consultar_turnos(especialidad: str) -> str:
    """Próximos turnos disponibles (fecha y hora) para pedir cita con una especialidad.
    Usala para "¿cuándo es el próximo turno?" o "¿hay turnos con X?". `especialidad` es
    por ejemplo "traumatologia" o "cardiologia". No dice qué documentos llevar: eso está
    en buscar_documentos. Si no existe, devuelve las opciones válidas."""
    return _get("/turnos", especialidad=especialidad)


def consultar_farmacia(medicamento: str) -> str:
    """Stock actual de un medicamento en la farmacia del hospital y, si no hay, la fecha
    de reposición. Usala para "¿tienen X?" o "¿cuándo vuelve a haber X?". `medicamento`
    es el nombre con la concentración si la hay, por ejemplo "enalapril 10 mg" o
    "insulina NPH". No dice qué se necesita para retirarlo: eso está en buscar_documentos.
    Si no existe, devuelve la lista de medicamentos válidos."""
    return _get("/farmacia", medicamento=medicamento)


def consultar_espera() -> str:
    """Minutos de espera actuales en la guardia para cada nivel de triage (rojo, naranja,
    amarillo, verde, azul). Usala para "¿cuánto se está esperando hoy en la guardia?".
    No recibe argumentos. Los máximos que fija el triage están en buscar_documentos."""
    return _get("/espera")


HERRAMIENTAS = [buscar_documentos, consultar_camas, consultar_guardia,
                consultar_turnos, consultar_farmacia, consultar_espera]
