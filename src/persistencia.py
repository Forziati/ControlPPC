"""Persistencia de cierres semanales y acciones correctivas en archivos JSON."""

import json
import os
import re
from datetime import datetime

import pandas as pd

PATRON_CIERRE = re.compile(r"^s(\d+)_cierre\.json$")


def _ruta_cierre(semana: int, ruta_historico: str) -> str:
    return os.path.join(ruta_historico, f"s{semana}_cierre.json")


def _ruta_acciones(semana: int, ruta_historico: str) -> str:
    return os.path.join(ruta_historico, f"s{semana}_acciones.json")


def _ruta_acumulados(ruta_historico: str) -> str:
    return os.path.join(ruta_historico, "acumulados.json")


def _a_serializable(valor):
    if isinstance(valor, pd.DataFrame):
        return valor.to_dict(orient="records")
    if isinstance(valor, pd.Series):
        return valor.to_dict()
    return valor


def guardar_cierre(semana: int, metricas: dict, cnc_top5, ruta_historico: str) -> str:
    """Guarda el cierre de una semana (métricas + top 5 CNC) como JSON. Devuelve la ruta del archivo."""
    os.makedirs(ruta_historico, exist_ok=True)
    contenido = {
        "semana": semana,
        "fecha_guardado": datetime.now().isoformat(),
        "metricas": _a_serializable(metricas),
        "cnc_top5": _a_serializable(cnc_top5),
    }
    ruta = _ruta_cierre(semana, ruta_historico)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(contenido, archivo, ensure_ascii=False, indent=2, default=str)
    return ruta


def guardar_acciones(semana: int, lista_acciones: list, ruta_historico: str) -> str:
    """Guarda la lista de acciones correctivas de una semana como JSON. Devuelve la ruta del archivo."""
    os.makedirs(ruta_historico, exist_ok=True)
    ruta = _ruta_acciones(semana, ruta_historico)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(lista_acciones, archivo, ensure_ascii=False, indent=2, default=str)
    return ruta


def cargar_cierre(semana: int, ruta_historico: str):
    """Carga el cierre de una semana. Devuelve None si no existe."""
    ruta = _ruta_cierre(semana, ruta_historico)
    if not os.path.exists(ruta):
        return None
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def cargar_acciones(semana: int, ruta_historico: str) -> list:
    """Carga las acciones de una semana. Devuelve lista vacía si no existe el archivo."""
    ruta = _ruta_acciones(semana, ruta_historico)
    if not os.path.exists(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def actualizar_acumulados(nuevos_datos: dict, ruta_historico: str) -> dict:
    """Actualiza (o crea) acumulados.json con los datos de una semana.

    `nuevos_datos` debe incluir la clave 'semana'. Devuelve el diccionario completo actualizado.
    """
    if "semana" not in nuevos_datos:
        raise ValueError("nuevos_datos debe incluir la clave 'semana'.")

    os.makedirs(ruta_historico, exist_ok=True)
    ruta = _ruta_acumulados(ruta_historico)

    acumulados = {}
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as archivo:
            acumulados = json.load(archivo)

    clave_semana = str(nuevos_datos["semana"])
    acumulados[clave_semana] = _a_serializable(nuevos_datos)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(acumulados, archivo, ensure_ascii=False, indent=2, default=str)

    return acumulados


def listar_semanas_procesadas(ruta_historico: str) -> list:
    """Devuelve la lista ordenada de números de semana que ya tienen un cierre guardado."""
    if not os.path.isdir(ruta_historico):
        return []

    semanas = []
    for nombre_archivo in os.listdir(ruta_historico):
        coincidencia = PATRON_CIERRE.match(nombre_archivo)
        if coincidencia:
            semanas.append(int(coincidencia.group(1)))

    return sorted(semanas)
