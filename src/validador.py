"""Validación de los CSVs de entrada del sistema."""

import pandas as pd

COLUMNAS_CRONOGRAMA = ["semana", "actividad", "volumen", "unidad", "dias_duracion", "frente"]
COLUMNAS_EJECUCION = ["semana", "dia", "actividad", "volumen_ejecutado", "frente", "cnc"]
COLUMNAS_PRECIOS = ["actividad", "precio_unitario", "moneda"]
COLUMNAS_CAUSAS = ["codigo", "descripcion", "categoria"]


def _validar_columnas(df: pd.DataFrame, columnas_esperadas: list) -> list:
    faltantes = [columna for columna in columnas_esperadas if columna not in df.columns]
    if faltantes:
        return [f"Faltan columnas requeridas: {', '.join(faltantes)}."]
    return []


def validar_cronograma(df_cronograma: pd.DataFrame) -> list:
    """Valida el cronograma semanal. Devuelve una lista de errores (vacía si es válido)."""
    errores = _validar_columnas(df_cronograma, COLUMNAS_CRONOGRAMA)
    if errores:
        return errores

    if (df_cronograma["volumen"] <= 0).any():
        errores.append("Existen actividades con volumen menor o igual a cero.")
    if (df_cronograma["dias_duracion"] <= 0).any():
        errores.append("Existen actividades con días de duración menor o igual a cero.")
    if df_cronograma["actividad"].isna().any():
        errores.append("Existen filas sin nombre de actividad.")

    return errores


def validar_ejecucion(df_ejecucion: pd.DataFrame) -> list:
    """Valida la ejecución diaria. Devuelve una lista de errores (vacía si es válido)."""
    errores = _validar_columnas(df_ejecucion, COLUMNAS_EJECUCION)
    if errores:
        return errores

    if (df_ejecucion["volumen_ejecutado"] < 0).any():
        errores.append("Existen registros con volumen ejecutado negativo.")
    if df_ejecucion["actividad"].isna().any():
        errores.append("Existen filas sin nombre de actividad.")

    return errores


def validar_precios(df_precios: pd.DataFrame) -> list:
    """Valida el listado de precios unitarios. Devuelve una lista de errores (vacía si es válido)."""
    errores = _validar_columnas(df_precios, COLUMNAS_PRECIOS)
    if errores:
        return errores

    if (df_precios["precio_unitario"] <= 0).any():
        errores.append("Existen precios unitarios menores o iguales a cero.")
    if df_precios["actividad"].duplicated().any():
        errores.append("Existen actividades duplicadas en la tabla de precios.")

    return errores


def validar_causas(df_causas: pd.DataFrame) -> list:
    """Valida el catálogo de causas de no cumplimiento. Devuelve una lista de errores (vacía si es válido)."""
    errores = _validar_columnas(df_causas, COLUMNAS_CAUSAS)
    if errores:
        return errores

    if df_causas["codigo"].duplicated().any():
        errores.append("Existen códigos de causa duplicados.")
    if df_causas["codigo"].isna().any():
        errores.append("Existen causas sin código.")

    return errores


def validar_consistencia(cronograma: pd.DataFrame, ejecucion: pd.DataFrame) -> list:
    """Valida que las actividades ejecutadas existan en el cronograma de la misma semana."""
    errores = []
    for _, fila in ejecucion.iterrows():
        coincidencias = cronograma[
            (cronograma["semana"] == fila["semana"])
            & (cronograma["actividad"] == fila["actividad"])
            & (cronograma["frente"] == fila["frente"])
        ]
        if coincidencias.empty:
            errores.append(
                f"La actividad '{fila['actividad']}' ejecutada en semana {fila['semana']} "
                f"({fila['frente']}) no está programada en el cronograma."
            )

    return sorted(set(errores))
