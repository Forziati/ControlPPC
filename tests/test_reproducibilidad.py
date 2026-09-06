"""Verifica que las corridas en corridas/ sean reproducibles: mismo input, mismo output."""

import json
import sys
import unittest
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_REPO))

from corridas.generar_corrida import calcular_resultado_corrida


class TestReproducibilidad(unittest.TestCase):
    def test_corrida_semana_01_es_reproducible(self):
        """Re-ejecuta la corrida semana_01 y compara contra el resultado versionado en el repo.

        Se excluyen a propósito `fecha_ejecucion` y `commit_codigo`: son metadata de
        auditoría de *cuándo y sobre qué commit* se generó esa foto, no resultados del
        cálculo — cambian en cada commit posterior sin que eso implique que el cálculo
        dejó de ser reproducible. Lo que sí tiene que coincidir exactamente, siempre,
        corriendo el mismo input, es `metricas` y `cnc_top5`.
        """
        ruta_esperado = RAIZ_REPO / "corridas" / "semana_01" / "output" / "s1_cierre.json"
        with open(ruta_esperado, "r", encoding="utf-8") as archivo:
            esperado = json.load(archivo)

        obtenido = calcular_resultado_corrida("semana_01", 1)

        claves_resultado = {"semana", "metricas", "cnc_top5"}
        esperado_resultado = {clave: valor for clave, valor in esperado.items() if clave in claves_resultado}
        obtenido_resultado = {clave: valor for clave, valor in obtenido.items() if clave in claves_resultado}

        self.assertEqual(obtenido_resultado, esperado_resultado)

    def test_corrida_semana_01_ppc_y_montos_conocidos(self):
        """Ancla los valores concretos de la corrida de referencia (evita que cambien sin darse cuenta)."""
        resultado = calcular_resultado_corrida("semana_01", 1)

        self.assertEqual(resultado["metricas"]["ppc_semanal"][0]["ppc"], 16.67)
        self.assertEqual(resultado["metricas"]["monto_programado"], 2240000.0)
        self.assertEqual(resultado["metricas"]["monto_ejecutado"], 1315000.0)
        self.assertEqual(len(resultado["cnc_top5"]), 3)


if __name__ == "__main__":
    unittest.main()
