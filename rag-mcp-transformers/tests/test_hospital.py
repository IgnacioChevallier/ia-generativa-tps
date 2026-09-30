"""Tests de las herramientas de hospital.py contra la API real de la cátedra, levantada
en un puerto libre dentro del test (solo biblioteca estándar)."""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import hospital  # noqa: E402

PUERTO = 8791


@pytest.fixture(scope="module", autouse=True)
def api():
    proc = subprocess.Popen([sys.executable, str(RAIZ / "api" / "servidor.py"), "--puerto", str(PUERTO)],
                            stdout=subprocess.DEVNULL)
    url = f"http://localhost:{PUERTO}"
    for _ in range(50):
        try:
            urllib.request.urlopen(f"{url}/espera", timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    anterior, hospital.API_URL = hospital.API_URL, url
    yield
    hospital.API_URL = anterior
    proc.terminate()


def test_camas_devuelve_libres():
    d = json.loads(hospital.consultar_camas("pediatria"))
    assert d["datos"]["libres"] == 7


def test_nombre_con_tildes_y_espacios():
    d = json.loads(hospital.consultar_camas("Terapia Intensiva"))
    assert d["datos"]["libres"] == 0


def test_sector_inexistente_devuelve_opciones_como_texto():
    d = json.loads(hospital.consultar_camas("marte"))
    assert "error" in d and "pediatria" in d["opciones"]


def test_farmacia_sin_stock_trae_reposicion():
    assert "2026-10-09" in hospital.consultar_farmacia("enalapril 10 mg")


def test_turnos_guardia_y_espera():
    assert "2026-10-07" in hospital.consultar_turnos("traumatologia")
    assert "Benítez" in hospital.consultar_guardia("cardiologia")
    assert json.loads(hospital.consultar_espera())["minutos_por_nivel"]["verde"] == 135


def test_api_caida_devuelve_error_como_texto():
    anterior, hospital.API_URL = hospital.API_URL, "http://localhost:1"
    try:
        assert "error" in json.loads(hospital.consultar_espera())
    finally:
        hospital.API_URL = anterior


def test_nombres_y_docstrings_de_las_herramientas():
    nombres = [f.__name__ for f in hospital.HERRAMIENTAS]
    assert nombres == ["buscar_documentos", "consultar_camas", "consultar_guardia",
                       "consultar_turnos", "consultar_farmacia", "consultar_espera"]
    assert all(f.__doc__ and len(f.__doc__) > 80 for f in hospital.HERRAMIENTAS)
