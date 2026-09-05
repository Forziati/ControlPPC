import os
import shutil
import tempfile
import unittest

import pandas as pd

from src.analizador_cnc import contar_cnc_frecuencias, enriquecer_con_descripciones, obtener_top_5
from src.calculador_inversion import calcular_acumulado, calcular_monto_ejecutado, calcular_monto_programado
from src.calculador_ppc import calcular_ppc_acumulado, calcular_ppc_por_actividad
from src.comparador_curva_s import calcular_desviacion, clasificar_estado
from src.gestor_acciones import actualizar_estado, crear_accion
from src.persistencia import cargar_acciones, guardar_acciones, guardar_cierre, listar_semanas_procesadas
from src.validador import validar_consistencia, validar_cronograma, validar_ejecucion, validar_precios

RUTA_DATOS = os.path.join(os.path.dirname(__file__), "..", "data")


class TestIntegracion(unittest.TestCase):
    def setUp(self):
        self.ruta_historico = tempfile.mkdtemp()
        self.cronograma = pd.read_csv(os.path.join(RUTA_DATOS, "cronograma_semanal.csv"))
        self.precios = pd.read_csv(os.path.join(RUTA_DATOS, "precios_unitarios.csv"))
        self.ejecucion = pd.read_csv(os.path.join(RUTA_DATOS, "ejecucion_diaria.csv"))
        self.causas = pd.read_csv(os.path.join(RUTA_DATOS, "causas_incumplimiento.csv"))

    def tearDown(self):
        shutil.rmtree(self.ruta_historico, ignore_errors=True)

    def test_pipeline_completo_semana_1(self):
        self.assertEqual(validar_cronograma(self.cronograma), [])
        self.assertEqual(validar_precios(self.precios), [])
        self.assertEqual(validar_ejecucion(self.ejecucion), [])
        self.assertEqual(validar_consistencia(self.cronograma, self.ejecucion), [])

        ppc_actividad = calcular_ppc_por_actividad(self.cronograma, self.ejecucion)
        ppc_semanal = calcular_ppc_acumulado(ppc_actividad)
        self.assertIn(1, ppc_semanal["semana"].values)

        monto_programado = calcular_monto_programado(self.cronograma, self.precios)
        monto_ejecutado = calcular_monto_ejecutado(self.ejecucion, self.precios)
        self.assertGreater(monto_programado["monto_programado"].sum(), 0)
        self.assertGreater(monto_ejecutado["monto_ejecutado"].sum(), 0)

        frecuencias = contar_cnc_frecuencias(self.ejecucion)
        top5 = obtener_top_5(frecuencias)
        cnc_df = enriquecer_con_descripciones(top5, self.causas)
        self.assertLessEqual(len(cnc_df), 5)

        metricas = {"ppc": float(ppc_semanal.iloc[0]["ppc"])}
        ruta_guardada = guardar_cierre(1, metricas, cnc_df, self.ruta_historico)
        self.assertTrue(os.path.exists(ruta_guardada))
        self.assertEqual(listar_semanas_procesadas(self.ruta_historico), [1])

    def test_carga_datos_seguimiento_semana_2(self):
        accion = crear_accion("SM", "Coordinar suministro", "Ana", "ana@example.com", "2026-01-20")
        guardar_acciones(1, [accion], self.ruta_historico)

        acciones_s1 = cargar_acciones(1, self.ruta_historico)
        self.assertEqual(len(acciones_s1), 1)

        actualizar_estado(acciones_s1, accion["id"], "completada", resultado="positivo", observaciones="Resuelto")
        guardar_acciones(1, acciones_s1, self.ruta_historico)

        acciones_actualizadas = cargar_acciones(1, self.ruta_historico)
        self.assertEqual(acciones_actualizadas[0]["estado"], "completada")

        montos = calcular_monto_ejecutado(self.ejecucion, self.precios)
        montos_acumulados = calcular_acumulado(montos)
        curva_esperada = pd.DataFrame([{"semana": 1, "porcentaje_acumulado_esperado": 8}])
        real = pd.DataFrame(
            [{"semana": 1, "porcentaje_acumulado_real": 10.0}]
        )
        comparacion = calcular_desviacion(real, curva_esperada)
        comparacion["estado"] = clasificar_estado(comparacion["desviacion"])
        self.assertIn(comparacion.loc[0, "estado"], ["Adelantado", "En Plan", "Atrasado"])


if __name__ == "__main__":
    unittest.main()
