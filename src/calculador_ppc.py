"""Cálculo del PPC (Porcentaje de Plan Cumplido) por actividad y por semana."""

import pandas as pd


def calcular_ppc_por_actividad(programado_df: pd.DataFrame, ejecutado_df: pd.DataFrame) -> pd.DataFrame:
    """Compara volumen programado vs. ejecutado por semana/actividad/frente.

    Devuelve un DataFrame con columnas:
    semana, actividad, frente, volumen_programado, volumen_ejecutado,
    porcentaje_avance (0-100, capado en 100), cumplida (bool).
    """
    programado = (
        programado_df.groupby(["semana", "actividad", "frente"], as_index=False)["volumen"]
        .sum()
        .rename(columns={"volumen": "volumen_programado"})
    )
    ejecutado = (
        ejecutado_df.groupby(["semana", "actividad", "frente"], as_index=False)["volumen_ejecutado"]
        .sum()
    )

    resultado = programado.merge(ejecutado, on=["semana", "actividad", "frente"], how="left")
    resultado["volumen_ejecutado"] = resultado["volumen_ejecutado"].fillna(0)

    resultado["porcentaje_avance"] = resultado.apply(
        lambda fila: min(fila["volumen_ejecutado"] / fila["volumen_programado"] * 100, 100.0)
        if fila["volumen_programado"] > 0
        else 0.0,
        axis=1,
    )
    resultado["cumplida"] = resultado["porcentaje_avance"] >= 100.0

    return resultado


def calcular_ppc_acumulado(ppc_por_actividad: pd.DataFrame) -> pd.DataFrame:
    """Calcula el PPC semanal: % de actividades cumplidas sobre el total programado.

    Devuelve un DataFrame con columnas: semana, total_actividades, actividades_cumplidas, ppc.
    """
    if ppc_por_actividad.empty:
        return pd.DataFrame(columns=["semana", "total_actividades", "actividades_cumplidas", "ppc"])

    agrupado = ppc_por_actividad.groupby("semana").agg(
        total_actividades=("cumplida", "count"),
        actividades_cumplidas=("cumplida", "sum"),
    )
    agrupado["ppc"] = (agrupado["actividades_cumplidas"] / agrupado["total_actividades"] * 100).round(2)
    return agrupado.reset_index()


def validar_ppc_rango(ppc_series) -> bool:
    """Verifica que todos los valores de PPC estén en el rango [0, 100].

    Lanza ValueError si algún valor está fuera de rango. Devuelve True si es válido.
    """
    valores = pd.Series(ppc_series).dropna()
    if ((valores < 0) | (valores > 100)).any():
        raise ValueError("Existen valores de PPC fuera del rango permitido [0, 100].")
    return True
