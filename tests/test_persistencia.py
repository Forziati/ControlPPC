import shutil
import tempfile
import unittest

from src.persistencia import (
    actualizar_acumulados,
    cargar_acciones,
    cargar_cierre,
    guardar_acciones,
    guardar_cierre,
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


if __name__ == "__main__":
    unittest.main()
