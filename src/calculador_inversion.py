"""Cálculo de inversión programada, ejecutada y acumulada."""

import pandas as pd


def calcular_monto_programado(cronograma_df: pd.DataFrame, precios_df: pd.DataFrame) -> pd.DataFrame:
    """Calcula el monto programado por semana a partir del cronograma y los precios unitarios.

    Devuelve un DataFrame con columnas: semana, monto_programado.
    """
    combinado = cronograma_df.merge(precios_df, on="actividad", how="left")
    combinado["monto"] = combinado["volumen"] * combinado["precio_unitario"]
    resultado = combinado.groupby("semana", as_index=False)["monto"].sum()
    return resultado.rename(columns={"monto": "monto_programado"})


def calcular_monto_ejecutado(ejecucion_df: pd.DataFrame, precios_df: pd.DataFrame) -> pd.DataFrame:
    """Calcula el monto ejecutado por semana a partir de la ejecución diaria y los precios unitarios.

    Devuelve un DataFrame con columnas: semana, monto_ejecutado.
    """
    agrupado = ejecucion_df.groupby(["semana", "actividad"], as_index=False)["volumen_ejecutado"].sum()
    combinado = agrupado.merge(precios_df, on="actividad", how="left")
    combinado["monto"] = combinado["volumen_ejecutado"] * combinado["precio_unitario"]
    resultado = combinado.groupby("semana", as_index=False)["monto"].sum()
    return resultado.rename(columns={"monto": "monto_ejecutado"})


def calcular_acumulado(montos_semanales: pd.DataFrame) -> pd.DataFrame:
    """Calcula el acumulado de cada columna numérica de un DataFrame ordenado por semana.

    Añade una columna `<columna>_acumulado` por cada columna numérica distinta de `semana`.
    """
    resultado = montos_semanales.sort_values("semana").reset_index(drop=True).copy()
    columnas_numericas = [c for c in resultado.columns if c != "semana"]
    for columna in columnas_numericas:
        resultado[f"{columna}_acumulado"] = resultado[columna].cumsum()
    return resultado


def calcular_porcentaje_financiero(acumulado, total: float):
    """Calcula el % financiero de un acumulado respecto de un monto total.

    `acumulado` puede ser un número o una serie/columna; `total` es el monto total del proyecto.
    """
    if total is None or total == 0:
        raise ValueError("El monto total debe ser distinto de cero.")
    if isinstance(acumulado, pd.Series):
        return (acumulado / total * 100).round(2)
    return round(acumulado / total * 100, 2)
