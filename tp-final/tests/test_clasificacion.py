"""La clasificación del historial y las costumbres que salen de él."""

import csv
import unittest
from collections import Counter

from curado.clasificar import clasificar
from curado.costumbres import medir_dos_credenciales, medir_voluntariado
from curado.historial import RAIZ, leer_historial
from curado.oraculo import EDAD_AVISO_VOLUNTARIADO


class TestClasificacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resultados = clasificar()

    def test_una_clasificacion_por_fila_con_un_tipo_valido(self):
        self.assertEqual(len(self.resultados), 2000)
        self.assertEqual({r["tipo"] for r in self.resultados}, {"correcta", "error", "ruido"})

    def test_el_csv_entregado_es_el_que_sale_del_script(self):
        with open(RAIZ / "historial_clasificado.csv", encoding="utf-8", newline="") as f:
            entregado = list(csv.reader(f))
        self.assertEqual(entregado[0], ["id", "tipo"])
        self.assertEqual(entregado[1:], [[r["id"], r["tipo"]] for r in self.resultados])

    def test_un_error_nunca_es_ruido_y_viceversa(self):
        for r in self.resultados:
            self.assertEqual(r["tipo"] == "error", bool(r["errores"]))
            if r["tipo"] == "ruido":
                self.assertTrue(r["desvios"])
                self.assertFalse(r["errores"])

    def test_el_ruido_es_de_los_tres_operadores_que_se_apartan(self):
        self.assertEqual({r["operador"] for r in self.resultados if r["tipo"] == "ruido"}, {"OP-04", "OP-11", "OP-17"})


class TestCostumbres(unittest.TestCase):
    def test_el_umbral_medido_es_el_del_oraculo(self):
        self.assertEqual(medir_voluntariado(leer_historial())["umbral"], EDAD_AVISO_VOLUNTARIADO)

    def test_con_dos_credenciales_los_que_siguen_la_costumbre_verifican_la_prepaga(self):
        filas = leer_historial()
        siguen = set(medir_voluntariado(filas)["siguen"])
        por_operador = medir_dos_credenciales(filas)["por_operador"]
        self.assertTrue(all(c["obra social"] == 0 for o, c in por_operador.items() if o in siguen))
        self.assertGreater(sum(c["prepaga"] for c in por_operador.values()), 100)


if __name__ == "__main__":
    unittest.main()
