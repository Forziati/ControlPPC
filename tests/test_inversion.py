import unittest

import pandas as pd

from src.calculador_inversion import (
    calcular_acumulado,
    calcular_monto_ejecutado,
    calcular_monto_programado,
    calcular_porcentaje_financiero,
)


class TestCalculadorInversion(unittest.TestCase):
    def setUp(self):
        self.precios = pd.DataFrame(
            [
                {"actividad": "Despalme", "precio_unitario": 500, "moneda": "USD"},
                {"actividad": "Excavación", "precio_unitario": 600, "moneda": "USD"},
            ]
        )

    def test_monto_programado_basico(self):
        cronograma = pd.DataFrame(
            [{"semana": 1, "actividad": "Despalme", "volumen": 10, "unidad": "m3", "dias_duracion": 1, "frente": "F1"}]
        )
        resultado = calcular_monto_programado(cronograma, self.precios)
        self.assertEqual(resultado.loc[0, "monto_programado"], 5000)

    def test_monto_ejecutado_vs_programado(self):
        cronograma = pd.DataFrame(
            [{"semana": 1, "actividad": "Despalme", "volumen": 10, "unidad": "m3", "dias_duracion": 1, "frente": "F1"}]
        )
        ejecucion = pd.DataFrame(
            [{"semana": 1, "dia": "lunes", "actividad": "Despalme", "volumen_ejecutado": 5, "frente": "F1", "cnc": None}]
        )
        programado = calcular_monto_programado(cronograma, self.precios)
        ejecutado = calcular_monto_ejecutado(ejecucion, self.precios)
        self.assertEqual(programado.loc[0, "monto_programado"], 5000)
        self.assertEqual(ejecutado.loc[0, "monto_ejecutado"], 2500)

    def test_acumulado_semanal(self):
        montos = pd.DataFrame([{"semana": 1, "monto": 100}, {"semana": 2, "monto": 150}])
        resultado = calcular_acumulado(montos)
        self.assertEqual(resultado.loc[0, "monto_acumulado"], 100)
        self.assertEqual(resultado.loc[1, "monto_acumulado"], 250)

    def test_porcentaje_financiero(self):
        self.assertEqual(calcular_porcentaje_financiero(50, 200), 25.0)

    def test_porcentaje_financiero_total_cero_lanza_error(self):
        with self.assertRaises(ValueError):
            calcular_porcentaje_financiero(50, 0)


if __name__ == "__main__":
    unittest.main()
