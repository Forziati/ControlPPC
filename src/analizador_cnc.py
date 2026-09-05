"""Análisis de Causas de No Cumplimiento (CNC) registradas en la ejecución diaria."""

import pandas as pd


def contar_cnc_frecuencias(ejecucion_diaria_df: pd.DataFrame) -> dict:
    """Cuenta la frecuencia de cada código CNC registrado (ignora valores vacíos)."""
    columna = ejecucion_diaria_df["cnc"].dropna()
    columna = columna[columna.astype(str).str.strip() != ""]
    return columna.value_counts().to_dict()


def obtener_top_5(frecuencias_dict: dict) -> list:
    """Devuelve las 5 causas más frecuentes como lista de tuplas (codigo, frecuencia)."""
    ordenado = sorted(frecuencias_dict.items(), key=lambda item: item[1], reverse=True)
    return ordenado[:5]


def calcular_porcentajes(frecuencias_dict: dict) -> dict:
    """Calcula el % que representa cada causa sobre el total de registros CNC."""
    total = sum(frecuencias_dict.values())
    if total == 0:
        return {codigo: 0.0 for codigo in frecuencias_dict}
    return {codigo: round(frecuencia / total * 100, 2) for codigo, frecuencia in frecuencias_dict.items()}


def enriquecer_con_descripciones(top5: list, causas_df: pd.DataFrame) -> pd.DataFrame:
    """Combina el top 5 de CNC con su descripción y categoría.

    `top5` es una lista de tuplas (codigo, frecuencia).
    Devuelve un DataFrame con columnas: codigo, frecuencia, descripcion, categoria, porcentaje.
    """
    df_top5 = pd.DataFrame(top5, columns=["codigo", "frecuencia"])
    if df_top5.empty:
        return pd.DataFrame(columns=["codigo", "frecuencia", "descripcion", "categoria", "porcentaje"])

    total = df_top5["frecuencia"].sum()
    df_top5["porcentaje"] = (df_top5["frecuencia"] / total * 100).round(2) if total else 0.0

    resultado = df_top5.merge(causas_df, on="codigo", how="left")
    return resultado[["codigo", "frecuencia", "descripcion", "categoria", "porcentaje"]]
