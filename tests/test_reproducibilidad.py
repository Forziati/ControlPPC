"""Verifica que las corridas en corridas/ sean reproducibles: mismo input, mismo output."""

import json
import sys
import unittest
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_REPO))

from corridas.generar_corrida import calcular_resultado_corrida, listar_corridas

# Valores conocidos de cada corrida de referencia, para anclar que no cambien sin darse cuenta.
VALORES_ESPERADOS = {
    "semana_01": {"ppc": 16.67, "monto_programado": 2240000.0, "monto_ejecutado": 1315000.0, "cantidad_cnc": 3},
    "semana_02": {"ppc": 83.33, "monto_programado": 2240000.0, "monto_ejecutado": 2195000.0, "cantidad_cnc": 2},
    "semana_03": {"ppc": 0.0, "monto_programado": 2240000.0, "monto_ejecutado": 1075000.0, "cantidad_cnc": 5},
}


class TestReproducibilidad(unittest.TestCase):
    def test_hay_al_menos_tres_corridas(self):
        self.assertGreaterEqual(len(listar_corridas()), 3)

    def test_todas_las_corridas_declaradas_tienen_valores_esperados(self):
        # Si se agrega una corrida nueva, este test avisa que hay que sumarla a VALORES_ESPERADOS.
        self.assertEqual(set(listar_corridas()), set(VALORES_ESPERADOS.keys()))

    def test_corridas_son_reproducibles(self):
        """Re-ejecuta cada corrida y compara contra el resultado versionado en el repo.

        Se excluyen a propósito `fecha_ejecucion`, `commit_codigo` y `costo_ia`: son
        metadata de auditoría (cuándo/sobre qué commit se generó la foto, tarifa vigente
        al momento de generarla), no resultados del cálculo de PPC/inversión/CNC — cambian
        legítimamente en cada commit posterior sin que eso implique que el cálculo dejó de
        ser reproducible. Lo que sí tiene que coincidir exactamente, siempre, corriendo el
        mismo input, es `metricas` y `cnc_top5`.
        """
        claves_resultado = {"semana", "metricas", "cnc_top5"}

        for corrida_id, datos in VALORES_ESPERADOS.items():
            with self.subTest(corrida=corrida_id):
                semana = int(corrida_id.split("_")[-1])
                ruta_esperado = RAIZ_REPO / "corridas" / corrida_id / "output" / f"s{semana}_cierre.json"
                with open(ruta_esperado, "r", encoding="utf-8") as archivo:
                    esperado = json.load(archivo)

                obtenido = calcular_resultado_corrida(corrida_id, semana)

                esperado_resultado = {clave: valor for clave, valor in esperado.items() if clave in claves_resultado}
                obtenido_resultado = {clave: valor for clave, valor in obtenido.items() if clave in claves_resultado}
                self.assertEqual(obtenido_resultado, esperado_resultado)

    def test_valores_conocidos_por_corrida(self):
        for corrida_id, datos in VALORES_ESPERADOS.items():
            with self.subTest(corrida=corrida_id):
                semana = int(corrida_id.split("_")[-1])
                resultado = calcular_resultado_corrida(corrida_id, semana)

                self.assertEqual(resultado["metricas"]["ppc_semanal"][0]["ppc"], datos["ppc"])
                self.assertEqual(resultado["metricas"]["monto_programado"], datos["monto_programado"])
                self.assertEqual(resultado["metricas"]["monto_ejecutado"], datos["monto_ejecutado"])
                self.assertEqual(len(resultado["cnc_top5"]), datos["cantidad_cnc"])

    def test_costo_ia_de_cada_corrida_es_cero_y_reproducible(self):
        for corrida_id in VALORES_ESPERADOS:
            with self.subTest(corrida=corrida_id):
                semana = int(corrida_id.split("_")[-1])
                resultado = calcular_resultado_corrida(corrida_id, semana)

                costo = resultado["costo_ia"]
                self.assertEqual(costo["tokens_entrada"], 0)
                self.assertEqual(costo["tokens_salida"], 0)
                self.assertEqual(costo["costo_total_usd"], 0.0)
                self.assertGreater(costo["tarifa_salida_usd_por_mtok"], 0)


if __name__ == "__main__":
    unittest.main()
