import unittest

import pandas as pd

from src.calculador_ppc import (
    calcular_ppc_acumulado,
    calcular_ppc_por_actividad,
    validar_ppc_rango,
)


class TestCalculadorPPC(unittest.TestCase):
    def test_ppc_100_si_se_ejecuta_todo(self):
        programado = pd.DataFrame(
            [{"semana": 1, "actividad": "Despalme", "frente": "Frente 1", "volumen": 100}]
        )
        ejecutado = pd.DataFrame(
            [{"semana": 1, "actividad": "Despalme", "frente": "Frente 1", "volumen_ejecutado": 100}]
        )
        resultado = calcular_ppc_por_actividad(programado, ejecutado)
        self.assertEqual(resultado.loc[0, "porcentaje_avance"], 100.0)
        self.assertTrue(resultado.loc[0, "cumplida"])

    def test_ppc_0_si_no_se_ejecuta_nada(self):
        programado = pd.DataFrame(
            [{"semana": 1, "actividad": "Despalme", "frente": "Frente 1", "volumen": 100}]
        )
        ejecutado = pd.DataFrame(columns=["semana", "actividad", "frente", "volumen_ejecutado"])
        resultado = calcular_ppc_por_actividad(programado, ejecutado)
        self.assertEqual(resultado.loc[0, "porcentaje_avance"], 0.0)
        self.assertFalse(resultado.loc[0, "cumplida"])

    def test_ppc_nunca_supera_100(self):
        programado = pd.DataFrame(
            [{"semana": 1, "actividad": "Despalme", "frente": "Frente 1", "volumen": 100}]
        )
        ejecutado = pd.DataFrame(
            [{"semana": 1, "actividad": "Despalme", "frente": "Frente 1", "volumen_ejecutado": 250}]
        )
        resultado = calcular_ppc_por_actividad(programado, ejecutado)
        self.assertEqual(resultado.loc[0, "porcentaje_avance"], 100.0)

    def test_ppc_con_multiples_actividades(self):
        programado = pd.DataFrame(
            [
                {"semana": 1, "actividad": "Despalme", "frente": "Frente 1", "volumen": 100},
                {"semana": 1, "actividad": "Excavación", "frente": "Frente 1", "volumen": 200},
            ]
        )
        ejecutado = pd.DataFrame(
            [
                {"semana": 1, "actividad": "Despalme", "frente": "Frente 1", "volumen_ejecutado": 100},
                {"semana": 1, "actividad": "Excavación", "frente": "Frente 1", "volumen_ejecutado": 100},
            ]
        )
        ppc_actividad = calcular_ppc_por_actividad(programado, ejecutado)
        ppc_acumulado = calcular_ppc_acumulado(ppc_actividad)
        fila = ppc_acumulado[ppc_acumulado["semana"] == 1].iloc[0]
        self.assertEqual(fila["total_actividades"], 2)
        self.assertEqual(fila["actividades_cumplidas"], 1)
        self.assertEqual(fila["ppc"], 50.0)

    def test_validar_ppc_rango_valido(self):
        self.assertTrue(validar_ppc_rango(pd.Series([0, 50, 100])))

    def test_validar_ppc_rango_invalido(self):
        with self.assertRaises(ValueError):
            validar_ppc_rango(pd.Series([0, 150]))


if __name__ == "__main__":
    unittest.main()
