"""El buscador de las normas: forma de los fragmentos, estabilidad entre versiones y un piso de recall."""

import unittest
from pathlib import Path

from admision.evaluar_rag import cargar_dataset, evaluar_buscador

from buscador import BuscadorNormas

RAIZ = Path(__file__).resolve().parent.parent


class TestBuscador(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = BuscadorNormas(RAIZ / "normas" / "original")

    def test_devuelve_k_fragmentos_con_su_codigo_de_seccion(self):
        fragmentos = self.original.recuperar("plazo del ECG por dolor torácico", 3)
        self.assertEqual(len(fragmentos), 3)
        self.assertTrue(all(f.texto.startswith(f.seccion) for f in fragmentos))

    def test_el_fragmento_que_cita_un_parametro_trae_su_valor(self):
        f = self.original.recuperar("plazo del electrocardiograma por dolor torácico", 1)[0]
        self.assertEqual(f.seccion, "NOR-TDE-01")
        self.assertIn("P-TDE-1 = 10 min", f.texto)

    def test_el_valor_sale_de_la_carpeta_que_recibe(self):
        b = BuscadorNormas(RAIZ / "normas" / "b")
        f = b.recuperar("plazo del electrocardiograma por dolor torácico", 1)[0]
        self.assertIn("P-TDE-1 = 15 min", f.texto)

    def test_trae_los_mismos_fragmentos_con_cualquier_version_de_las_normas(self):
        otras = [BuscadorNormas(RAIZ / "normas" / v) for v in ("b", "c")]
        for consulta in ("registro de paciente sin documento", "¿hasta qué nivel se ubica en el box?",
                         "llegó en ambulancia con dolor de pecho"):
            ids = [f.id for f in self.original.recuperar(consulta, 3)]
            for b in otras:
                self.assertEqual([f.id for f in b.recuperar(consulta, 3)], ids)

    def test_trae_lo_mismo_con_las_tres_versiones_en_las_consultas_de_desarrollo_y_propias(self):
        consultas = [q["consulta"] for ruta in ("rag/consultas_dev.jsonl", "datos/consultas_propias.jsonl")
                     for q in cargar_dataset(RAIZ / ruta)]
        self.assertEqual(len(consultas), 101)
        for v in ("b", "c"):
            otra = BuscadorNormas(RAIZ / "normas" / v)
            for consulta in consultas:
                self.assertEqual([f.id for f in otra.recuperar(consulta, 3)],
                                 [f.id for f in self.original.recuperar(consulta, 3)], consulta)

    def test_recall_de_evidencia_no_baja_del_piso(self):
        r = evaluar_buscador(self.original, cargar_dataset(RAIZ / "rag" / "consultas_dev.jsonl"))
        self.assertGreaterEqual(r["recall_evidencia"], 0.875)  # la referencia BM25 de la cátedra
        self.assertLessEqual(r["tokens_por_consulta"], 580)


if __name__ == "__main__":
    unittest.main()
