"""El oráculo tiene que reproducir las 150 fichas esperadas de la cátedra (50 casos x normas original, b y c)."""

import unittest

from curado.validar_oraculo import validar


class TestOraculo(unittest.TestCase):
    def test_reproduce_las_fichas_esperadas_de_practica(self):
        self.assertEqual(validar(detalle=False), 0)


if __name__ == "__main__":
    unittest.main()
