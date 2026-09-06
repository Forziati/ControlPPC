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

# Tarifa pública de Claude Sonnet 5 (el modelo usado para desarrollar este repositorio),
# citada acá únicamente para que la fórmula de costo por corrida sea evaluable con una
# tarifa real y no un placeholder — no porque esta corrida invoque el modelo.
TARIFA_ENTRADA_SONNET5_USD_POR_MTOK = 2.00
TARIFA_SALIDA_SONNET5_USD_POR_MTOK = 10.00


def _commit_actual() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=RAIZ_REPO, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "desconocido (no se pudo leer git rev-parse HEAD)"


def calcular_costo_ia_corrida() -> dict:
    """Costo de IA de ESTA corrida (ejecutar el cálculo) — no el costo de desarrollar el sistema.

    tokens_entrada y tokens_salida son 0 porque `calcular_resultado_corrida` sólo llama
    a funciones puras de `src/` (pandas): no hay ningún request a un modelo de lenguaje
    en este camino. Esto no es una afirmación: `tests/test_sin_ia_en_runtime.py` falla si
    algún archivo de `src/` o `streamlit_app.py` alguna vez importa un SDK de IA generativa,
    lo que haría falsos estos ceros.
    """
    tokens_entrada = 0
    tokens_salida = 0
    costo_entrada_usd = round(tokens_entrada / 1_000_000 * TARIFA_ENTRADA_SONNET5_USD_POR_MTOK, 6)
    costo_salida_usd = round(tokens_salida / 1_000_000 * TARIFA_SALIDA_SONNET5_USD_POR_MTOK, 6)

    return {
        "modelo": "ninguno (0 llamadas a un modelo de lenguaje en esta corrida)",
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "tarifa_entrada_usd_por_mtok": TARIFA_ENTRADA_SONNET5_USD_POR_MTOK,
        "tarifa_salida_usd_por_mtok": TARIFA_SALIDA_SONNET5_USD_POR_MTOK,
        "costo_entrada_usd": costo_entrada_usd,
        "costo_salida_usd": costo_salida_usd,
        "costo_total_usd": round(costo_entrada_usd + costo_salida_usd, 6),
        "formula": (
            "costo_total_usd = (tokens_entrada / 1e6 * tarifa_entrada_usd_por_mtok) "
            "+ (tokens_salida / 1e6 * tarifa_salida_usd_por_mtok)"
        ),
        "verificado_por": "tests/test_sin_ia_en_runtime.py",
    }


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
        "costo_ia": calcular_costo_ia_corrida(),
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
        "costo_ia": resultado["costo_ia"],
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


def listar_corridas() -> list:
    """Devuelve los ids de todas las carpetas corridas/<id>/ que tengan un input/ válido."""
    return sorted(
        directorio.name
        for directorio in (RAIZ_REPO / "corridas").iterdir()
        if directorio.is_dir() and (directorio / "input").is_dir()
    )


def generar_todas_las_corridas() -> dict:
    """Regenera output/metadata de cada corrida y escribe el ledger agregado de costo por corrida."""
    ledger = {"corridas": {}, "costo_total_usd": 0.0}

    for corrida_id in listar_corridas():
        semana = int(corrida_id.split("_")[-1])
        resultado = generar_corrida(corrida_id, semana)
        ledger["corridas"][corrida_id] = resultado["costo_ia"]
        ledger["costo_total_usd"] = round(ledger["costo_total_usd"] + resultado["costo_ia"]["costo_total_usd"], 6)

    ledger["cantidad_corridas"] = len(ledger["corridas"])
    ledger["nota"] = (
        "Ledger agregado de costo de IA por corrida (tokens x tarifa), uno por cada "
        "carpeta corridas/<id>/. Generado por corridas/generar_corrida.py; cada valor "
        "es recalculado, nunca tipeado a mano."
    )

    with open(RAIZ_REPO / "corridas" / "costos_por_corrida.json", "w", encoding="utf-8") as archivo:
        json.dump(ledger, archivo, ensure_ascii=False, indent=2)

    return ledger


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--todas":
        resultado_ledger = generar_todas_las_corridas()
        print(json.dumps(resultado_ledger, ensure_ascii=False, indent=2))
    else:
        corrida = sys.argv[1] if len(sys.argv) > 1 else "semana_01"
        numero_semana = int(corrida.split("_")[-1])
        salida = generar_corrida(corrida, numero_semana)
        print(json.dumps(salida, ensure_ascii=False, indent=2))
