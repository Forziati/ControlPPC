import shutil
import tempfile
import unittest

import pandas as pd

from src.persistencia import (
    actualizar_acumulados,
    cargar_acciones,
    cargar_cierre,
    cargar_ejecucion_historica,
    cargar_ejecucion_semana,
    guardar_acciones,
    guardar_cierre,
    guardar_ejecucion_semana,
    listar_semanas_con_ejecucion,
    listar_semanas_procesadas,
)


class TestPersistencia(unittest.TestCase):
    def setUp(self):
        self.ruta_temporal = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.ruta_temporal, ignore_errors=True)

    def test_guardar_y_cargar_cierre(self):
        metricas = {"ppc": 78.0, "monto_ejecutado_acumulado": 1000}
        guardar_cierre(1, metricas, [], self.ruta_temporal)
        cierre = cargar_cierre(1, self.ruta_temporal)
        self.assertIsNotNone(cierre)
        self.assertEqual(cierre["metricas"]["ppc"], 78.0)

    def test_cargar_cierre_inexistente(self):
        self.assertIsNone(cargar_cierre(99, self.ruta_temporal))

    def test_guardar_y_cargar_acciones(self):
        acciones = [{"id": "1", "cnc": "SM", "estado": "pendiente"}]
        guardar_acciones(1, acciones, self.ruta_temporal)
        cargadas = cargar_acciones(1, self.ruta_temporal)
        self.assertEqual(len(cargadas), 1)
        self.assertEqual(cargadas[0]["cnc"], "SM")

    def test_cargar_acciones_inexistente_devuelve_lista_vacia(self):
        self.assertEqual(cargar_acciones(99, self.ruta_temporal), [])

    def test_actualizar_acumulados(self):
        actualizar_acumulados({"semana": 1, "ppc": 78.0}, self.ruta_temporal)
        acumulados = actualizar_acumulados({"semana": 2, "ppc": 82.0}, self.ruta_temporal)
        self.assertIn("1", acumulados)
        self.assertIn("2", acumulados)
        self.assertEqual(acumulados["2"]["ppc"], 82.0)

    def test_listar_semanas_procesadas(self):
        guardar_cierre(1, {"ppc": 1}, [], self.ruta_temporal)
        guardar_cierre(3, {"ppc": 2}, [], self.ruta_temporal)
        self.assertEqual(listar_semanas_procesadas(self.ruta_temporal), [1, 3])

    def test_guardar_y_cargar_ejecucion_semana(self):
        df = pd.DataFrame(
            [{"semana": 1, "dia": "lunes", "actividad": "Despalme", "frente": "F1", "volumen_ejecutado": 100, "cnc": ""}]
        )
        guardar_ejecucion_semana(1, df, self.ruta_temporal)
        cargada = cargar_ejecucion_semana(1, self.ruta_temporal)
        self.assertEqual(len(cargada), 1)
        self.assertEqual(cargada[0]["actividad"], "Despalme")

    def test_cargar_ejecucion_semana_inexistente_devuelve_lista_vacia(self):
        self.assertEqual(cargar_ejecucion_semana(99, self.ruta_temporal), [])

    def test_listar_semanas_con_ejecucion(self):
        df = pd.DataFrame([{"semana": 1, "dia": "lunes", "actividad": "Despalme", "frente": "F1", "volumen_ejecutado": 10, "cnc": ""}])
        guardar_ejecucion_semana(1, df, self.ruta_temporal)
        guardar_ejecucion_semana(2, df, self.ruta_temporal)
        self.assertEqual(listar_semanas_con_ejecucion(self.ruta_temporal), [1, 2])

    def test_cargar_ejecucion_historica_concatena_semanas(self):
        df1 = pd.DataFrame([{"semana": 1, "dia": "lunes", "actividad": "Despalme", "frente": "F1", "volumen_ejecutado": 10, "cnc": ""}])
        df2 = pd.DataFrame([{"semana": 2, "dia": "lunes", "actividad": "Excavación", "frente": "F1", "volumen_ejecutado": 20, "cnc": "FT"}])
        guardar_ejecucion_semana(1, df1, self.ruta_temporal)
        guardar_ejecucion_semana(2, df2, self.ruta_temporal)

        historico = cargar_ejecucion_historica(self.ruta_temporal)

        self.assertEqual(len(historico), 2)
        self.assertListEqual(sorted(historico["semana"].tolist()), [1, 2])

    def test_cargar_ejecucion_historica_vacia_sin_datos(self):
        historico = cargar_ejecucion_historica(self.ruta_temporal)
        self.assertTrue(historico.empty)
        self.assertIn("actividad", historico.columns)


if __name__ == "__main__":
    unittest.main()
