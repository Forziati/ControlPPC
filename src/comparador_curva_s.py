"""Comparación del avance real contra la curva S esperada del proyecto."""

import pandas as pd

from .calculador_inversion import calcular_acumulado, calcular_monto_programado, calcular_porcentaje_financiero

UMBRAL_DESVIACION = 2.0


def cargar_curva_s_esperada(archivo) -> pd.DataFrame:
    """Carga el archivo CSV de curva S esperada.

    `archivo` puede ser una ruta o un objeto tipo archivo (ej. de st.file_uploader).
    Devuelve un DataFrame con columnas: semana, porcentaje_acumulado_esperado.
    """
    return pd.read_csv(archivo)


def calcular_curva_s_esperada_desde_cronograma(cronograma_df: pd.DataFrame, precios_df: pd.DataFrame) -> pd.DataFrame:
    """Deriva la curva S esperada directamente del cronograma y los precios unitarios.

    No requiere un CSV aparte: el % acumulado esperado de cada semana es el monto
    programado acumulado hasta esa semana sobre el monto programado total del proyecto.
    Devuelve un DataFrame con columnas: semana, porcentaje_acumulado_esperado.
    """
    montos = calcular_monto_programado(cronograma_df, precios_df)
    montos = calcular_acumulado(montos.sort_values("semana").reset_index(drop=True))
    total_programado = montos["monto_programado"].sum()
    montos["porcentaje_acumulado_esperado"] = calcular_porcentaje_financiero(
        montos["monto_programado_acumulado"], total_programado
    )
    return montos[["semana", "porcentaje_acumulado_esperado"]]


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
