"""Genera una corrida reproducible ejecutando el código real de src/ sobre inputs fijos.

Uso:
    python corridas/generar_corrida.py semana_01

Lee los CSVs de `corridas/<corrida_id>/input/`, ejecuta calculador_ppc.py,
calculador_inversion.py y analizador_cnc.py (el código real del repositorio, sin
recalcular nada "a mano"), y escribe `corridas/<corrida_id>/output/s<semana>_cierre.json`
y `corridas/<corrida_id>/metadata.json`.

Este formato de "cierre de corrida" es una foto de auditoría para D3 (reproducibilidad),
distinta del JSON que genera `src/persistencia.py::guardar_cierre` para el uso normal
de la app (ese incluye además montos acumulados y curva S, pensados para varias semanas).
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_REPO))

import pandas as pd

from src.analizador_cnc import contar_cnc_frecuencias, enriquecer_con_descripciones, obtener_top_5
from src.calculador_inversion import calcular_monto_ejecutado, calcular_monto_programado
from src.calculador_ppc import calcular_ppc_acumulado, calcular_ppc_por_actividad


def _commit_actual() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=RAIZ_REPO, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "desconocido (no se pudo leer git rev-parse HEAD)"


def calcular_resultado_corrida(corrida_id: str, semana: int) -> dict:
    """Ejecuta el cálculo real sobre los inputs fijos de la corrida y devuelve el resultado.

    No escribe ningún archivo: es la parte "pura" que reutiliza tanto `generar_corrida`
    (para persistir la evidencia) como el test de reproducibilidad (para verificarla sin
    pisar el archivo versionado en cada corrida de la suite de tests).
    """
    ruta_input = RAIZ_REPO / "corridas" / corrida_id / "input"

    cronograma_df = pd.read_csv(ruta_input / "cronograma_semanal.csv")
    precios_df = pd.read_csv(ruta_input / "precios_unitarios.csv")
    ejecucion_df = pd.read_csv(ruta_input / "ejecucion_diaria.csv")
    causas_df = pd.read_csv(ruta_input / "causas_incumplimiento.csv")

    ppc_por_actividad = calcular_ppc_por_actividad(cronograma_df, ejecucion_df)
    ppc_semanal = calcular_ppc_acumulado(ppc_por_actividad)

    monto_programado_df = calcular_monto_programado(cronograma_df, precios_df)
    monto_ejecutado_df = calcular_monto_ejecutado(ejecucion_df, precios_df)

    frecuencias = contar_cnc_frecuencias(ejecucion_df)
    top5 = obtener_top_5(frecuencias)
    cnc_top5_df = enriquecer_con_descripciones(top5, causas_df)

    fila_ppc = ppc_semanal[ppc_semanal["semana"] == semana]
    monto_programado = float(monto_programado_df.loc[monto_programado_df["semana"] == semana, "monto_programado"].iloc[0])
    monto_ejecutado = float(monto_ejecutado_df.loc[monto_ejecutado_df["semana"] == semana, "monto_ejecutado"].iloc[0])

    return {
        "semana": semana,
        "fecha_ejecucion": datetime.now().isoformat(),
        "commit_codigo": _commit_actual(),
        "metricas": {
            "ppc_semanal": fila_ppc.to_dict(orient="records"),
            "monto_programado": monto_programado,
            "monto_ejecutado": monto_ejecutado,
        },
        "cnc_top5": cnc_top5_df.to_dict(orient="records"),
    }


def generar_corrida(corrida_id: str, semana: int) -> dict:
    """Calcula el resultado de la corrida y lo persiste en output/ y metadata.json."""
    ruta_corrida = RAIZ_REPO / "corridas" / corrida_id
    ruta_output = ruta_corrida / "output"
    ruta_output.mkdir(parents=True, exist_ok=True)

    resultado = calcular_resultado_corrida(corrida_id, semana)

    ruta_salida = ruta_output / f"s{semana}_cierre.json"
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        json.dump(resultado, archivo, ensure_ascii=False, indent=2)

    metadata = {
        "corrida_id": corrida_id,
        "fecha_ejecucion": resultado["fecha_ejecucion"],
        "commit_codigo": resultado["commit_codigo"],
        "inputs_utilizados": [
            "cronograma_semanal.csv",
            "precios_unitarios.csv",
            "ejecucion_diaria.csv",
            "causas_incumplimiento.csv",
        ],
        "outputs_generados": [f"s{semana}_cierre.json"],
        "reproducible": True,
        "nota": (
            "Corrida generada ejecutando directamente src/calculador_ppc.py, "
            "src/calculador_inversion.py y src/analizador_cnc.py sobre los CSVs fijos "
            "en corridas/{}/input/ (no sobre data/, para que la corrida no cambie si los "
            "datos de ejemplo del repo se actualizan). Reproducibilidad verificada en "
            "tests/test_reproducibilidad.py."
        ).format(corrida_id),
    }
    with open(ruta_corrida / "metadata.json", "w", encoding="utf-8") as archivo:
        json.dump(metadata, archivo, ensure_ascii=False, indent=2)

    return resultado


if __name__ == "__main__":
    corrida = sys.argv[1] if len(sys.argv) > 1 else "semana_01"
    numero_semana = int(corrida.split("_")[-1])
    salida = generar_corrida(corrida, numero_semana)
    print(json.dumps(salida, ensure_ascii=False, indent=2))
