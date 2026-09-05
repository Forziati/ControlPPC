"""Comparación del avance real contra la curva S esperada del proyecto."""

import pandas as pd

UMBRAL_DESVIACION = 2.0


def cargar_curva_s_esperada(archivo) -> pd.DataFrame:
    """Carga el archivo CSV de curva S esperada.

    `archivo` puede ser una ruta o un objeto tipo archivo (ej. de st.file_uploader).
    Devuelve un DataFrame con columnas: semana, porcentaje_acumulado_esperado.
    """
    return pd.read_csv(archivo)


def calcular_desviacion(real_acumulado: pd.DataFrame, esperado: pd.DataFrame) -> pd.DataFrame:
    """Calcula la desviación entre el % real acumulado y el % esperado, por semana.

    `real_acumulado` debe tener columnas: semana, porcentaje_acumulado_real.
    `esperado` debe tener columnas: semana, porcentaje_acumulado_esperado.
    Devuelve un DataFrame con columnas: semana, porcentaje_acumulado_real,
    porcentaje_acumulado_esperado, desviacion.
    """
    combinado = real_acumulado.merge(esperado, on="semana", how="left")
    combinado["desviacion"] = (
        combinado["porcentaje_acumulado_real"] - combinado["porcentaje_acumulado_esperado"]
    ).round(2)
    return combinado


def clasificar_estado(desviacion, umbral: float = UMBRAL_DESVIACION):
    """Clasifica una desviación (o serie de desviaciones) en Adelantado/En Plan/Atrasado."""

    def _clasificar(valor):
        if pd.isna(valor):
            return "Sin datos"
        if valor > umbral:
            return "Adelantado"
        if valor < -umbral:
            return "Atrasado"
        return "En Plan"

    if isinstance(desviacion, pd.Series):
        return desviacion.apply(_clasificar)
    return _clasificar(desviacion)
