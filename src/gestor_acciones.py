"""Gestión de acciones correctivas: creación, validación, actualización y listado."""

import re
import uuid
from datetime import date, datetime

from . import persistencia

ESTADOS_VALIDOS = ["pendiente", "en_curso", "completada", "cancelada"]
RESULTADOS_VALIDOS = ["positivo", "negativo", "parcial", None]

_REGEX_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def crear_accion(cnc: str, descripcion: str, responsable: str, email: str, fecha_plazo) -> dict:
    """Crea una nueva acción correctiva en estado 'pendiente'.

    Lanza ValueError si los datos no son válidos.
    """
    if isinstance(fecha_plazo, (date, datetime)):
        fecha_plazo = fecha_plazo.isoformat()

    accion = {
        "id": str(uuid.uuid4()),
        "cnc": cnc,
        "descripcion": descripcion,
        "responsable": responsable,
        "email": email,
        "fecha_plazo": fecha_plazo,
        "fecha_creacion": datetime.now().isoformat(),
        "estado": "pendiente",
        "resultado": None,
        "observaciones": "",
    }

    errores = validar_accion(accion)
    if errores:
        raise ValueError("Acción inválida: " + "; ".join(errores))

    return accion


def validar_accion(accion_dict: dict) -> list:
    """Valida los campos obligatorios de una acción. Devuelve una lista de errores (vacía si es válida)."""
    errores = []
    for campo in ["cnc", "descripcion", "responsable", "email", "fecha_plazo"]:
        valor = accion_dict.get(campo)
        if valor is None or str(valor).strip() == "":
            errores.append(f"El campo '{campo}' es obligatorio.")

    email = accion_dict.get("email")
    if email and not _REGEX_EMAIL.match(str(email)):
        errores.append("El formato del email no es válido.")

    return errores


def listar_acciones(semana: int, ruta_historico: str) -> list:
    """Lista las acciones registradas para una semana, usando el módulo de persistencia."""
    return persistencia.cargar_acciones(semana, ruta_historico)


def actualizar_estado(acciones_list: list, id_accion: str, nuevo_estado: str, resultado=None, observaciones=None) -> list:
    """Actualiza el estado (y opcionalmente resultado/observaciones) de una acción por su id.

    Devuelve la lista de acciones actualizada. Lanza ValueError si el id no existe
    o si el estado no es válido.
    """
    if nuevo_estado not in ESTADOS_VALIDOS:
        raise ValueError(f"Estado inválido: {nuevo_estado}. Debe ser uno de {ESTADOS_VALIDOS}.")

    encontrada = False
    for accion in acciones_list:
        if accion.get("id") == id_accion:
            accion["estado"] = nuevo_estado
            if resultado is not None:
                accion["resultado"] = resultado
            if observaciones is not None:
                accion["observaciones"] = observaciones
            encontrada = True
            break

    if not encontrada:
        raise ValueError(f"No se encontró la acción con id {id_accion}.")

    return acciones_list


def generar_tabla_acciones_dict(acciones_list: list) -> dict:
    """Convierte una lista de acciones en un diccionario de columnas, listo para st.dataframe."""
    columnas = ["id", "cnc", "descripcion", "responsable", "email", "fecha_plazo", "estado", "resultado", "observaciones"]
    tabla = {columna: [] for columna in columnas}
    for accion in acciones_list:
        for columna in columnas:
            tabla[columna].append(accion.get(columna))
    return tabla


def obtener_accion_vigente_por_cnc(cnc: str, acciones_list: list):
    """Devuelve la acción más reciente registrada para una causa CNC, o None si no hay ninguna."""
    candidatas = [accion for accion in acciones_list if accion.get("cnc") == cnc]
    if not candidatas:
        return None
    return max(candidatas, key=lambda accion: accion.get("fecha_creacion", ""))


def listar_acciones_vencidas(acciones_list: list, fecha_referencia: date = None) -> list:
    """Devuelve las acciones 'pendiente'/'en_curso' cuya fecha_plazo ya pasó.

    Es el mecanismo de respuesta ante una acción correctiva que no se resolvió a
    tiempo: se usa en la pestaña Seguimiento para que una acción vencida no pueda
    pasar desapercibida entre las demás, en vez de depender de que alguien la
    note a simple vista.
    """
    if fecha_referencia is None:
        fecha_referencia = date.today()

    vencidas = []
    for accion in acciones_list:
        if accion.get("estado") not in ("pendiente", "en_curso"):
            continue
        fecha_plazo_str = accion.get("fecha_plazo")
        if not fecha_plazo_str:
            continue
        try:
            fecha_plazo = date.fromisoformat(str(fecha_plazo_str))
        except ValueError:
            continue
        if fecha_plazo < fecha_referencia:
            vencidas.append(accion)

    return vencidas
