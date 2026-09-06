import unittest

import pandas as pd

from src.validador import (
    validar_causas,
    validar_consistencia,
    validar_cronograma,
    validar_ejecucion,
    validar_precios,
    validar_precios_faltantes,
)


class TestValidador(unittest.TestCase):
    def setUp(self):
        self.cronograma = pd.DataFrame(
            [{"semana": 1, "actividad": "Despalme", "volumen": 100, "unidad": "m3", "dias_duracion": 5, "frente": "F1"}]
        )
        self.precios = pd.DataFrame([{"actividad": "Despalme", "precio_unitario": 500, "moneda": "USD"}])
        self.ejecucion = pd.DataFrame(
            [{"semana": 1, "dia": "lunes", "actividad": "Despalme", "volumen_ejecutado": 50, "frente": "F1", "cnc": ""}]
        )
        self.causas = pd.DataFrame([{"codigo": "SM", "descripcion": "Falta de materiales", "categoria": "Recursos"}])

    def test_validar_cronograma_valido(self):
        self.assertEqual(validar_cronograma(self.cronograma), [])

    def test_validar_cronograma_columna_faltante(self):
        errores = validar_cronograma(self.cronograma.drop(columns=["volumen"]))
        self.assertTrue(errores)

    def test_validar_cronograma_volumen_invalido(self):
        cronograma_invalido = self.cronograma.copy()
        cronograma_invalido.loc[0, "volumen"] = 0
        errores = validar_cronograma(cronograma_invalido)
        self.assertTrue(any("volumen" in error for error in errores))

    def test_validar_ejecucion_valida(self):
        self.assertEqual(validar_ejecucion(self.ejecucion), [])

    def test_validar_ejecucion_volumen_negativo(self):
        ejecucion_invalida = self.ejecucion.copy()
        ejecucion_invalida.loc[0, "volumen_ejecutado"] = -10
        errores = validar_ejecucion(ejecucion_invalida)
        self.assertTrue(any("negativo" in error for error in errores))

    def test_validar_precios_valido(self):
        self.assertEqual(validar_precios(self.precios), [])

    def test_validar_precios_duplicados(self):
        precios_duplicados = pd.concat([self.precios, self.precios], ignore_index=True)
        errores = validar_precios(precios_duplicados)
        self.assertTrue(any("duplicadas" in error for error in errores))

    def test_validar_causas_valido(self):
        self.assertEqual(validar_causas(self.causas), [])

    def test_validar_causas_codigo_duplicado(self):
        causas_duplicadas = pd.concat([self.causas, self.causas], ignore_index=True)
        errores = validar_causas(causas_duplicadas)
        self.assertTrue(any("duplicados" in error for error in errores))

    def test_validar_consistencia_sin_errores(self):
        self.assertEqual(validar_consistencia(self.cronograma, self.ejecucion), [])

    def test_validar_consistencia_actividad_no_programada(self):
        ejecucion_invalida = pd.DataFrame(
            [{"semana": 1, "dia": "lunes", "actividad": "Actividad Fantasma", "volumen_ejecutado": 10, "frente": "F1", "cnc": ""}]
        )
        errores = validar_consistencia(self.cronograma, ejecucion_invalida)
        self.assertTrue(any("Actividad Fantasma" in error for error in errores))

    def test_validar_precios_faltantes_sin_errores(self):
        self.assertEqual(validar_precios_faltantes(self.ejecucion, self.precios), [])

    def test_validar_precios_faltantes_detecta_actividad_sin_precio(self):
        ejecucion_sin_precio = pd.DataFrame(
            [{"semana": 1, "dia": "lunes", "actividad": "Actividad Sin Precio", "volumen_ejecutado": 10, "frente": "F1", "cnc": ""}]
        )
        errores = validar_precios_faltantes(ejecucion_sin_precio, self.precios)
        self.assertEqual(len(errores), 1)
        self.assertIn("Actividad Sin Precio", errores[0])

    def test_validar_precios_faltantes_ejecucion_vacia(self):
        ejecucion_vacia = pd.DataFrame(columns=["semana", "dia", "actividad", "volumen_ejecutado", "frente", "cnc"])
        self.assertEqual(validar_precios_faltantes(ejecucion_vacia, self.precios), [])


if __name__ == "__main__":
    unittest.main()
