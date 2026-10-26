"""Las trayectorias de entrenamiento resuelven los 9 controles contra el entorno de la cátedra."""

import random
import unittest
from pathlib import Path

from admision.casos import cargar_casos

from buscador import BuscadorNormas
from curado.generar_datos import a_mensajes
from curado.oraculo import cargar_parametros
from curado.trayectorias import jugar

RAIZ = Path(__file__).resolve().parent.parent


class TestTrayectorias(unittest.TestCase):
    def test_el_experto_resuelve_los_50_casos_de_practica_con_cada_version(self):
        casos = cargar_casos(RAIZ / "practica" / "casos.jsonl")
        for version in ("original", "b", "c"):
            carpeta = RAIZ / "normas" / version
            buscador, p = BuscadorNormas(carpeta), cargar_parametros(carpeta)
            for caso in casos:
                self.assertIsNotNone(jugar(caso, buscador, p, random.Random(0)), f"{version} {caso.id}")

    def test_la_conversacion_empieza_por_sistema_y_termina_en_registrar_decision(self):
        carpeta = RAIZ / "normas" / "original"
        caso = cargar_casos(RAIZ / "practica" / "casos.jsonl")[0]
        t = jugar(caso, BuscadorNormas(carpeta), cargar_parametros(carpeta), random.Random(0))
        mensajes = a_mensajes(t)
        self.assertEqual([m["role"] for m in mensajes[:2]], ["system", "user"])
        self.assertEqual(mensajes[-1]["role"], "assistant")
        self.assertIn("registrar_decision", mensajes[-1]["content"])


if __name__ == "__main__":
    unittest.main()
