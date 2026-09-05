import unittest

import pandas as pd

from src.comparador_curva_s import calcular_desviacion, clasificar_estado


class TestComparadorCurvaS(unittest.TestCase):
    def test_desviacion_positiva_adelanto(self):
        real = pd.DataFrame([{"semana": 1, "porcentaje_acumulado_real": 15}])
        esperado = pd.DataFrame([{"semana": 1, "porcentaje_acumulado_esperado": 8}])
        resultado = calcular_desviacion(real, esperado)
        self.assertEqual(resultado.loc[0, "desviacion"], 7)
        self.assertEqual(clasificar_estado(resultado.loc[0, "desviacion"]), "Adelantado")

    def test_desviacion_negativa_atraso(self):
        real = pd.DataFrame([{"semana": 1, "porcentaje_acumulado_real": 3}])
        esperado = pd.DataFrame([{"semana": 1, "porcentaje_acumulado_esperado": 8}])
        resultado = calcular_desviacion(real, esperado)
        self.assertEqual(resultado.loc[0, "desviacion"], -5)
        self.assertEqual(clasificar_estado(resultado.loc[0, "desviacion"]), "Atrasado")

    def test_desviacion_en_plan(self):
        real = pd.DataFrame([{"semana": 1, "porcentaje_acumulado_real": 8}])
        esperado = pd.DataFrame([{"semana": 1, "porcentaje_acumulado_esperado": 8}])
        resultado = calcular_desviacion(real, esperado)
        self.assertEqual(clasificar_estado(resultado.loc[0, "desviacion"]), "En Plan")

    def test_curva_s_monotona(self):
        esperado = pd.DataFrame(
            [
                {"semana": 1, "porcentaje_acumulado_esperado": 8},
                {"semana": 2, "porcentaje_acumulado_esperado": 15},
                {"semana": 3, "porcentaje_acumulado_esperado": 24},
            ]
        )
        diferencias = esperado["porcentaje_acumulado_esperado"].diff().dropna()
        self.assertTrue((diferencias > 0).all())


if __name__ == "__main__":
    unittest.main()
