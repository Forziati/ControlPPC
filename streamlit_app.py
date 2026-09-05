"""Sistema de Control Semanal de Avance de Obra - Aplicación Streamlit."""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analizador_cnc import (
    calcular_porcentajes,
    contar_cnc_frecuencias,
    enriquecer_con_descripciones,
    obtener_top_5,
)
from src.calculador_inversion import (
    calcular_acumulado,
    calcular_monto_ejecutado,
    calcular_monto_programado,
    calcular_porcentaje_financiero,
)
from src.calculador_ppc import calcular_ppc_acumulado, calcular_ppc_por_actividad
from src.comparador_curva_s import calcular_desviacion, clasificar_estado
from src.gestor_acciones import ESTADOS_VALIDOS, crear_accion, generar_tabla_acciones_dict
from src.persistencia import (
    actualizar_acumulados,
    cargar_acciones,
    cargar_cierre,
    guardar_acciones,
    guardar_cierre,
    listar_semanas_procesadas,
)
from src.validador import (
    validar_causas,
    validar_consistencia,
    validar_cronograma,
    validar_ejecucion,
    validar_precios,
)

RUTA_DATOS = os.path.join(os.path.dirname(__file__), "data")
RUTA_HISTORICO = os.path.join(RUTA_DATOS, "historico")

ARCHIVOS_DEFAULT = {
    "cronograma_df": "cronograma_semanal.csv",
    "precios_df": "precios_unitarios.csv",
    "ejecucion_df": "ejecucion_diaria.csv",
    "causas_df": "causas_incumplimiento.csv",
    "curva_s_df": "curva_s_esperada.csv",
}


def _inicializar_estado():
    for clave in ARCHIVOS_DEFAULT:
        if clave not in st.session_state:
            st.session_state[clave] = None
    if "resultados" not in st.session_state:
        st.session_state["resultados"] = {}
    if "acciones_cache" not in st.session_state:
        st.session_state["acciones_cache"] = {}


def _obtener_acciones(semana: int) -> list:
    if semana not in st.session_state["acciones_cache"]:
        st.session_state["acciones_cache"][semana] = cargar_acciones(semana, RUTA_HISTORICO)
    return st.session_state["acciones_cache"][semana]


def _guardar_acciones_semana(semana: int, acciones: list):
    st.session_state["acciones_cache"][semana] = acciones
    guardar_acciones(semana, acciones, RUTA_HISTORICO)


def _procesar_datos(semana_actual: int) -> list:
    """Valida y procesa todos los datos cargados. Devuelve la lista de errores encontrados."""
    cronograma_df = st.session_state["cronograma_df"]
    precios_df = st.session_state["precios_df"]
    ejecucion_df = st.session_state["ejecucion_df"]
    causas_df = st.session_state["causas_df"]
    curva_s_df = st.session_state["curva_s_df"]

    errores = []
    errores += validar_cronograma(cronograma_df)
    errores += validar_precios(precios_df)
    errores += validar_ejecucion(ejecucion_df)
    errores += validar_causas(causas_df)
    errores += validar_consistencia(cronograma_df, ejecucion_df)
    if errores:
        return errores

    ppc_por_actividad = calcular_ppc_por_actividad(cronograma_df, ejecucion_df)
    ppc_acumulado = calcular_ppc_acumulado(ppc_por_actividad)

    monto_programado = calcular_monto_programado(cronograma_df, precios_df)
    monto_ejecutado = calcular_monto_ejecutado(ejecucion_df, precios_df)
    montos = monto_programado.merge(monto_ejecutado, on="semana", how="outer").fillna(0)
    montos = montos.sort_values("semana").reset_index(drop=True)
    montos_acumulados = calcular_acumulado(montos)

    total_presupuesto = monto_programado["monto_programado"].sum()
    montos_acumulados["porcentaje_acumulado_real"] = calcular_porcentaje_financiero(
        montos_acumulados["monto_ejecutado_acumulado"], total_presupuesto
    )

    real_para_curva = montos_acumulados[["semana", "porcentaje_acumulado_real"]]
    comparacion_curva_s = calcular_desviacion(real_para_curva, curva_s_df)
    comparacion_curva_s["estado"] = clasificar_estado(comparacion_curva_s["desviacion"])

    ejecucion_semana = ejecucion_df[ejecucion_df["semana"] == semana_actual]
    frecuencias = contar_cnc_frecuencias(ejecucion_semana)
    top5 = obtener_top_5(frecuencias)
    cnc_top5_df = enriquecer_con_descripciones(top5, causas_df)

    st.session_state["resultados"] = {
        "ppc_por_actividad": ppc_por_actividad,
        "ppc_acumulado": ppc_acumulado,
        "montos_acumulados": montos_acumulados,
        "total_presupuesto": total_presupuesto,
        "comparacion_curva_s": comparacion_curva_s,
        "cnc_top5_df": cnc_top5_df,
    }

    fila_semana = ppc_acumulado[ppc_acumulado["semana"] == semana_actual]
    ppc_semana = float(fila_semana["ppc"].iloc[0]) if not fila_semana.empty else 0.0

    fila_montos = montos_acumulados[montos_acumulados["semana"] == semana_actual]
    fila_curva = comparacion_curva_s[comparacion_curva_s["semana"] == semana_actual]

    metricas = {
        "ppc": ppc_semana,
        "monto_programado_semana": float(fila_montos["monto_programado"].iloc[0]) if not fila_montos.empty else 0.0,
        "monto_ejecutado_semana": float(fila_montos["monto_ejecutado"].iloc[0]) if not fila_montos.empty else 0.0,
        "monto_programado_acumulado": float(fila_montos["monto_programado_acumulado"].iloc[0]) if not fila_montos.empty else 0.0,
        "monto_ejecutado_acumulado": float(fila_montos["monto_ejecutado_acumulado"].iloc[0]) if not fila_montos.empty else 0.0,
        "porcentaje_financiero_acumulado": float(fila_montos["porcentaje_acumulado_real"].iloc[0]) if not fila_montos.empty else 0.0,
        "desviacion_curva_s": float(fila_curva["desviacion"].iloc[0]) if not fila_curva.empty else None,
        "estado_curva_s": str(fila_curva["estado"].iloc[0]) if not fila_curva.empty else "Sin datos",
    }

    guardar_cierre(semana_actual, metricas, cnc_top5_df, RUTA_HISTORICO)
    actualizar_acumulados({"semana": semana_actual, **metricas}, RUTA_HISTORICO)

    return []


def _semaforo_ppc(ppc: float) -> str:
    if ppc >= 85:
        return "🟢"
    if ppc >= 70:
        return "🟡"
    return "🔴"


st.set_page_config(page_title="Control de Avance de Obra", layout="wide")
_inicializar_estado()

with st.sidebar:
    st.title("Control de Avance de Obra")
    st.caption("Sistema semanal de PPC, inversión y acciones correctivas")
    semana_actual = st.number_input("Semana actual", min_value=1, max_value=52, value=1, step=1)
    semanas_procesadas = listar_semanas_procesadas(RUTA_HISTORICO)
    if semanas_procesadas:
        st.markdown(f"**Semanas procesadas:** {', '.join(str(s) for s in semanas_procesadas)}")
    else:
        st.markdown("**Semanas procesadas:** ninguna todavía")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Cargar Datos", "Tablero", "Curva S", "Acciones", "Seguimiento", "Histórico"]
)

with tab1:
    st.subheader("Cargar Datos Semanales")
    usar_ejemplo = st.checkbox("Usar datos de ejemplo incluidos en el repositorio", value=True)

    col_a, col_b = st.columns(2)
    uploads = {}
    with col_a:
        uploads["cronograma_df"] = st.file_uploader("cronograma_semanal.csv", type="csv")
        uploads["precios_df"] = st.file_uploader("precios_unitarios.csv", type="csv")
        uploads["ejecucion_df"] = st.file_uploader("ejecucion_diaria.csv", type="csv")
    with col_b:
        uploads["causas_df"] = st.file_uploader("causas_incumplimiento.csv", type="csv")
        uploads["curva_s_df"] = st.file_uploader("curva_s_esperada.csv", type="csv")

    for clave, archivo_subido in uploads.items():
        if archivo_subido is not None:
            st.session_state[clave] = pd.read_csv(archivo_subido)
        elif usar_ejemplo:
            ruta_default = os.path.join(RUTA_DATOS, ARCHIVOS_DEFAULT[clave])
            st.session_state[clave] = pd.read_csv(ruta_default)

    datos_listos = all(st.session_state[clave] is not None for clave in ARCHIVOS_DEFAULT)

    if datos_listos:
        with st.expander("Vista previa de los datos cargados"):
            for clave, nombre_archivo in ARCHIVOS_DEFAULT.items():
                st.markdown(f"**{nombre_archivo}**")
                st.dataframe(st.session_state[clave], use_container_width=True)

    if st.button("Procesar Datos", type="primary", disabled=not datos_listos):
        errores = _procesar_datos(int(semana_actual))
        if errores:
            st.error("Se encontraron errores de validación:")
            for error in errores:
                st.markdown(f"- {error}")
        else:
            st.success(f"Datos de la semana {int(semana_actual)} procesados y guardados correctamente.")

    if not datos_listos:
        st.info("Sube los 5 archivos CSV o activa 'Usar datos de ejemplo' para continuar.")

with tab2:
    st.subheader(f"Tablero - Semana {int(semana_actual)}")
    resultados = st.session_state.get("resultados")

    if not resultados:
        st.info("Procesa los datos en la pestaña 'Cargar Datos' para ver el tablero.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### Avance Financiero")
            montos = resultados["montos_acumulados"]
            fila = montos[montos["semana"] == semana_actual]
            programado = float(fila["monto_programado_acumulado"].iloc[0]) if not fila.empty else 0.0
            ejecutado = float(fila["monto_ejecutado_acumulado"].iloc[0]) if not fila.empty else 0.0
            st.metric("Inversión Acumulada", f"${ejecutado:,.0f}", f"Programado: ${programado:,.0f}")
            if programado > 0:
                st.progress(min(ejecutado / programado, 1.0))

            fig_fin = go.Figure()
            fig_fin.add_bar(x=montos["semana"], y=montos["monto_programado"], name="Programado (semanal)")
            fig_fin.add_bar(x=montos["semana"], y=montos["monto_ejecutado"], name="Ejecutado (semanal)")
            fig_fin.add_trace(
                go.Scatter(x=montos["semana"], y=montos["monto_ejecutado_acumulado"], name="Ejecutado acumulado", mode="lines+markers")
            )
            fig_fin.update_layout(barmode="group", height=350, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_fin, use_container_width=True)

        with col2:
            st.markdown("#### PPC Semanal")
            ppc_df = resultados["ppc_acumulado"]
            fila_ppc = ppc_df[ppc_df["semana"] == semana_actual]
            ppc_valor = float(fila_ppc["ppc"].iloc[0]) if not fila_ppc.empty else 0.0
            st.metric("PPC", f"{ppc_valor:.1f}%", _semaforo_ppc(ppc_valor))

            colores = ["#2ecc71" if v >= 85 else "#f1c40f" if v >= 70 else "#e74c3c" for v in ppc_df["ppc"]]
            fig_ppc = go.Figure(go.Bar(x=ppc_df["semana"], y=ppc_df["ppc"], marker_color=colores))
            fig_ppc.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="PPC (%)", xaxis_title="Semana")
            st.plotly_chart(fig_ppc, use_container_width=True)

        with col3:
            st.markdown("#### Top 5 CNC")
            cnc_df = resultados["cnc_top5_df"]
            if cnc_df.empty:
                st.info("No se registraron causas de no cumplimiento esta semana.")
            else:
                fig_cnc = px.bar(
                    cnc_df.sort_values("frecuencia"),
                    x="frecuencia",
                    y="codigo",
                    orientation="h",
                    text="porcentaje",
                )
                fig_cnc.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_cnc, use_container_width=True)
                st.dataframe(cnc_df, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Curva S: Real vs. Esperado")
    resultados = st.session_state.get("resultados")

    if not resultados:
        st.info("Procesa los datos en la pestaña 'Cargar Datos' para ver la curva S.")
    else:
        comparacion = resultados["comparacion_curva_s"]

        fig_curva = go.Figure()
        fig_curva.add_trace(
            go.Scatter(x=comparacion["semana"], y=comparacion["porcentaje_acumulado_real"], name="Real", mode="lines+markers")
        )
        fig_curva.add_trace(
            go.Scatter(x=comparacion["semana"], y=comparacion["porcentaje_acumulado_esperado"], name="Esperado", mode="lines+markers")
        )
        fig_curva.update_layout(height=400, xaxis_title="Semana", yaxis_title="% Acumulado")
        st.plotly_chart(fig_curva, use_container_width=True)

        fila_actual = comparacion[comparacion["semana"] == semana_actual]
        if not fila_actual.empty:
            desviacion = float(fila_actual["desviacion"].iloc[0])
            estado = str(fila_actual["estado"].iloc[0])
            st.metric(f"Desviación semana {int(semana_actual)}", f"{desviacion:+.2f} pp", estado)

        st.markdown("#### Tabla comparativa por semana")
        st.dataframe(comparacion, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Acciones Correctivas")
    causas_df = st.session_state.get("causas_df")

    st.markdown("#### Registro de Nuevas Acciones")
    if causas_df is None:
        st.info("Carga los datos en la pestaña 'Cargar Datos' para registrar acciones.")
    else:
        with st.form("form_nueva_accion", clear_on_submit=True):
            cnc = st.selectbox("Causa CNC", options=causas_df["codigo"].tolist())
            descripcion = st.text_input("Descripción")
            responsable = st.text_input("Responsable")
            email = st.text_input("Email")
            fecha_plazo = st.date_input("Fecha plazo")
            enviado = st.form_submit_button("Registrar Acción")

            if enviado:
                try:
                    nueva_accion = crear_accion(cnc, descripcion, responsable, email, fecha_plazo)
                    acciones = _obtener_acciones(int(semana_actual))
                    acciones.append(nueva_accion)
                    _guardar_acciones_semana(int(semana_actual), acciones)
                    st.success("Acción registrada correctamente.")
                except ValueError as error:
                    st.error(str(error))

    st.markdown("#### Acciones de la Semana Actual")
    acciones_actuales = _obtener_acciones(int(semana_actual))

    if not acciones_actuales:
        st.info("No hay acciones registradas para esta semana.")
    else:
        tabla = generar_tabla_acciones_dict(acciones_actuales)
        st.dataframe(pd.DataFrame(tabla), use_container_width=True, hide_index=True)

        ids_acciones = [accion["id"] for accion in acciones_actuales]
        etiquetas = {accion["id"]: f"{accion['cnc']} - {accion['descripcion'][:40]}" for accion in acciones_actuales}
        col_sel, col_estado, col_btn = st.columns([2, 1, 1])
        with col_sel:
            id_seleccionado = st.selectbox(
                "Acción a actualizar", options=ids_acciones, format_func=lambda x: etiquetas[x]
            )
        with col_estado:
            nuevo_estado = st.selectbox("Nuevo estado", options=ESTADOS_VALIDOS)
        with col_btn:
            st.write("")
            st.write("")
            if st.button("Actualizar Estado"):
                from src.gestor_acciones import actualizar_estado

                actualizar_estado(acciones_actuales, id_seleccionado, nuevo_estado)
                _guardar_acciones_semana(int(semana_actual), acciones_actuales)
                st.success("Estado actualizado.")
                st.rerun()

with tab5:
    st.subheader("Seguimiento de Semana Anterior")
    semanas_disponibles = [s for s in listar_semanas_procesadas(RUTA_HISTORICO) if s < semana_actual]

    if not semanas_disponibles:
        st.info("No hay semanas anteriores procesadas todavía.")
    else:
        semana_revisar = st.selectbox("Semana a revisar", options=semanas_disponibles, index=len(semanas_disponibles) - 1)
        acciones_previas = _obtener_acciones(int(semana_revisar))
        pendientes = [a for a in acciones_previas if a["estado"] in ("pendiente", "en_curso")]

        if not pendientes:
            st.info("No hay acciones pendientes o en curso en esa semana.")
        else:
            with st.form("form_seguimiento"):
                respuestas = {}
                for accion in pendientes:
                    st.markdown(f"**{accion['cnc']}** - {accion['descripcion']} (responsable: {accion['responsable']})")
                    completada = st.checkbox("¿Completada?", key=f"completada_{accion['id']}")
                    funciono = st.radio(
                        "¿Funcionó?", options=["positivo", "parcial", "negativo"], key=f"funciono_{accion['id']}", horizontal=True
                    )
                    observaciones = st.text_area("Observaciones", key=f"obs_{accion['id']}")
                    respuestas[accion["id"]] = (completada, funciono, observaciones)
                    st.divider()

                if st.form_submit_button("Guardar Seguimiento"):
                    from src.gestor_acciones import actualizar_estado

                    for id_accion, (completada, funciono, observaciones) in respuestas.items():
                        nuevo_estado = "completada" if completada else "en_curso"
                        actualizar_estado(acciones_previas, id_accion, nuevo_estado, resultado=funciono, observaciones=observaciones)
                    _guardar_acciones_semana(int(semana_revisar), acciones_previas)
                    st.success("Seguimiento guardado. Ya puedes cargar los datos de la semana actual.")

with tab6:
    st.subheader("Histórico y Reportes")
    semanas_disponibles = listar_semanas_procesadas(RUTA_HISTORICO)

    if not semanas_disponibles:
        st.info("Todavía no hay semanas procesadas para mostrar en el histórico.")
    else:
        rango = st.select_slider(
            "Rango de semanas",
            options=semanas_disponibles,
            value=(semanas_disponibles[0], semanas_disponibles[-1]),
        )
        semanas_filtradas = [s for s in semanas_disponibles if rango[0] <= s <= rango[1]]

        registros = []
        cnc_por_semana = {}
        for semana in semanas_filtradas:
            cierre = cargar_cierre(semana, RUTA_HISTORICO)
            if cierre is None:
                continue
            fila = {"semana": semana, **cierre["metricas"]}
            registros.append(fila)
            cnc_por_semana[semana] = cierre.get("cnc_top5", [])

        if registros:
            historico_df = pd.DataFrame(registros).sort_values("semana")

            fig_ppc_hist = px.line(historico_df, x="semana", y="ppc", markers=True, title="PPC por semana")
            st.plotly_chart(fig_ppc_hist, use_container_width=True)

            fig_fin_hist = px.area(
                historico_df, x="semana", y="porcentaje_financiero_acumulado", title="% Financiero acumulado"
            )
            st.plotly_chart(fig_fin_hist, use_container_width=True)

            fig_desv_hist = px.bar(historico_df, x="semana", y="desviacion_curva_s", title="Desviación Curva S por semana")
            st.plotly_chart(fig_desv_hist, use_container_width=True)

            st.markdown("#### Top CNC por semana")
            for semana, top5 in cnc_por_semana.items():
                if top5:
                    st.markdown(f"**Semana {semana}**")
                    st.dataframe(pd.DataFrame(top5), use_container_width=True, hide_index=True)

            st.download_button(
                "Descargar Reporte (CSV)",
                data=historico_df.to_csv(index=False).encode("utf-8"),
                file_name="reporte_historico.csv",
                mime="text/csv",
            )
