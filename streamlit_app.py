"""Sistema de Control Semanal de Avance de Obra - Aplicación Streamlit."""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analizador_cnc import (
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
from src.comparador_curva_s import (
    calcular_curva_s_esperada_desde_cronograma,
    calcular_desviacion,
    clasificar_estado,
)
from src.gestor_acciones import (
    ESTADOS_VALIDOS,
    actualizar_estado,
    crear_accion,
    generar_tabla_acciones_dict,
    listar_acciones_vencidas,
    obtener_accion_vigente_por_cnc,
)
from src.persistencia import (
    actualizar_acumulados,
    cargar_acciones,
    cargar_cierre,
    cargar_ejecucion_historica,
    cargar_ejecucion_semana,
    guardar_acciones,
    guardar_cierre,
    guardar_ejecucion_semana,
    listar_semanas_procesadas,
)
from src.validador import (
    validar_consistencia,
    validar_cronograma,
    validar_ejecucion,
    validar_precios,
    validar_precios_faltantes,
)

RUTA_DATOS = os.path.join(os.path.dirname(__file__), "data")
RUTA_HISTORICO = os.path.join(RUTA_DATOS, "historico")

ARCHIVOS_DEFAULT = {
    "cronograma_df": "cronograma_semanal.csv",
    "precios_df": "precios_unitarios.csv",
}

DIAS_DISPONIBLES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]
COLUMNAS_EDITOR = ["dia", "actividad", "frente", "volumen_ejecutado", "cnc"]

CAUSAS_DF = pd.read_csv(os.path.join(RUTA_DATOS, "causas_incumplimiento.csv"))


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


def _agregar_accion_responsable(cnc_df: pd.DataFrame, acciones_list: list) -> pd.DataFrame:
    """Agrega columnas 'accion' y 'responsable' con la acción vigente para cada causa CNC."""
    cnc_df = cnc_df.copy()
    acciones_col, responsables_col = [], []
    for codigo in cnc_df["codigo"]:
        vigente = obtener_accion_vigente_por_cnc(codigo, acciones_list)
        acciones_col.append(vigente["descripcion"] if vigente else "Sin acción registrada")
        responsables_col.append(vigente["responsable"] if vigente else "—")
    cnc_df["accion"] = acciones_col
    cnc_df["responsable"] = responsables_col
    return cnc_df


def _procesar_datos(semana_actual: int) -> list:
    """Valida y procesa todos los datos disponibles. Devuelve la lista de errores encontrados."""
    cronograma_df = st.session_state["cronograma_df"]
    precios_df = st.session_state["precios_df"]

    errores = []
    errores += validar_cronograma(cronograma_df)
    errores += validar_precios(precios_df)
    if errores:
        return errores

    ejecucion_df = cargar_ejecucion_historica(RUTA_HISTORICO)
    if not ejecucion_df.empty:
        errores += validar_ejecucion(ejecucion_df)
        errores += validar_consistencia(cronograma_df, ejecucion_df)
        errores += validar_precios_faltantes(ejecucion_df, precios_df)
    if errores:
        return errores

    curva_s_df = calcular_curva_s_esperada_desde_cronograma(cronograma_df, precios_df)

    ppc_por_actividad = calcular_ppc_por_actividad(cronograma_df, ejecucion_df)
    ppc_acumulado = calcular_ppc_acumulado(ppc_por_actividad)

    monto_programado = calcular_monto_programado(cronograma_df, precios_df)
    if ejecucion_df.empty:
        monto_ejecutado = pd.DataFrame(columns=["semana", "monto_ejecutado"])
    else:
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
    frecuencias_semana = contar_cnc_frecuencias(ejecucion_semana)
    cnc_semana_df = enriquecer_con_descripciones(obtener_top_5(frecuencias_semana), CAUSAS_DF)

    frecuencias_total = contar_cnc_frecuencias(ejecucion_df)
    cnc_total_df = enriquecer_con_descripciones(obtener_top_5(frecuencias_total), CAUSAS_DF)

    acciones_semana = _obtener_acciones(semana_actual)
    acciones_todas = []
    for semana in range(1, semana_actual + 1):
        acciones_todas.extend(_obtener_acciones(semana))

    cnc_semana_df = _agregar_accion_responsable(cnc_semana_df, acciones_semana)
    cnc_total_df = _agregar_accion_responsable(cnc_total_df, acciones_todas)

    st.session_state["resultados"] = {
        "ppc_por_actividad": ppc_por_actividad,
        "ppc_acumulado": ppc_acumulado,
        "montos_acumulados": montos_acumulados,
        "total_presupuesto": total_presupuesto,
        "comparacion_curva_s": comparacion_curva_s,
        "cnc_semana_df": cnc_semana_df,
        "cnc_total_df": cnc_total_df,
        "frecuencias_semana_total": sum(frecuencias_semana.values()),
        "frecuencias_total_total": sum(frecuencias_total.values()),
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

    guardar_cierre(semana_actual, metricas, cnc_semana_df, RUTA_HISTORICO)
    actualizar_acumulados({"semana": semana_actual, **metricas}, RUTA_HISTORICO)

    return []


def _semaforo_ppc(ppc: float) -> str:
    if ppc >= 85:
        return "🟢 En meta"
    if ppc >= 70:
        return "🟡 Atención"
    return "🔴 Crítico"


def _color_ppc(ppc: float) -> str:
    if ppc >= 85:
        return "#2ecc71"
    if ppc >= 70:
        return "#f1c40f"
    return "#e74c3c"


st.set_page_config(page_title="Control de Avance de Obra", layout="wide")
_inicializar_estado()

with st.sidebar:
    st.title("Control de Avance de Obra")
    st.caption("Sistema semanal de PPC, inversión, curva S y acciones correctivas")
    semana_actual = st.number_input("Semana actual", min_value=1, max_value=52, value=1, step=1)
    semanas_procesadas = listar_semanas_procesadas(RUTA_HISTORICO)
    if semanas_procesadas:
        st.markdown(f"**Semanas procesadas:** {', '.join(str(s) for s in semanas_procesadas)}")
    else:
        st.markdown("**Semanas procesadas:** ninguna todavía")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["Datos y Registro", "Curva S", "PPC", "CNC y Acciones", "Acciones", "Seguimiento", "Histórico"]
)

with tab1:
    st.subheader("Datos base y registro de avance")

    st.markdown("##### A · Documentos base del proyecto")
    st.caption("Se suben una sola vez (o al re-programar la obra).")
    usar_ejemplo = st.checkbox("Usar datos de ejemplo incluidos en el repositorio", value=True)

    col_a, col_b = st.columns(2)
    with col_a:
        archivo_cronograma = st.file_uploader("Programa de obra / cronograma", type="csv")
    with col_b:
        archivo_precios = st.file_uploader("Precios unitarios", type="csv")

    if archivo_cronograma is not None:
        st.session_state["cronograma_df"] = pd.read_csv(archivo_cronograma)
    elif usar_ejemplo:
        st.session_state["cronograma_df"] = pd.read_csv(os.path.join(RUTA_DATOS, ARCHIVOS_DEFAULT["cronograma_df"]))

    if archivo_precios is not None:
        st.session_state["precios_df"] = pd.read_csv(archivo_precios)
    elif usar_ejemplo:
        st.session_state["precios_df"] = pd.read_csv(os.path.join(RUTA_DATOS, ARCHIVOS_DEFAULT["precios_df"]))

    cronograma_df = st.session_state["cronograma_df"]
    precios_df = st.session_state["precios_df"]
    datos_base_listos = cronograma_df is not None and precios_df is not None

    st.info(
        "La curva S esperada se calcula automáticamente a partir del programa de obra y los precios "
        "unitarios: ya no hace falta subirla aparte. El catálogo de causas de no cumplimiento (CNC) "
        "es fijo dentro del sistema (ver panel C)."
    )

    if not datos_base_listos:
        st.warning("Subí el programa de obra y los precios unitarios (o activá 'Usar datos de ejemplo') para continuar.")
    else:
        st.markdown("---")
        st.markdown(f"##### B · Registro diario de avance — Semana {int(semana_actual)}")
        st.caption("Cargá el avance directo acá, estilo planilla. No hace falta subir ningún CSV de ejecución.")

        actividades_disponibles = sorted(cronograma_df["actividad"].unique().tolist())
        frentes_disponibles = sorted(cronograma_df["frente"].unique().tolist())
        cnc_disponibles = [""] + CAUSAS_DF["codigo"].tolist()

        registros_guardados = cargar_ejecucion_semana(int(semana_actual), RUTA_HISTORICO)
        if registros_guardados:
            df_editor_base = pd.DataFrame(registros_guardados)[COLUMNAS_EDITOR]
        else:
            actividades_semana = (
                cronograma_df[cronograma_df["semana"] == semana_actual][["actividad", "frente"]].drop_duplicates()
            )
            if actividades_semana.empty:
                df_editor_base = pd.DataFrame(columns=COLUMNAS_EDITOR)
            else:
                df_editor_base = pd.DataFrame(
                    {
                        "dia": "lunes",
                        "actividad": actividades_semana["actividad"].values,
                        "frente": actividades_semana["frente"].values,
                        "volumen_ejecutado": 0,
                        "cnc": "",
                    }
                )

        df_editado = st.data_editor(
            df_editor_base,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_ejecucion_{int(semana_actual)}",
            column_config={
                "dia": st.column_config.SelectboxColumn("Día", options=DIAS_DISPONIBLES, required=True),
                "actividad": st.column_config.SelectboxColumn("Actividad", options=actividades_disponibles, required=True),
                "frente": st.column_config.SelectboxColumn("Frente", options=frentes_disponibles, required=True),
                "volumen_ejecutado": st.column_config.NumberColumn("Vol. ejecutado", min_value=0, step=1, required=True),
                "cnc": st.column_config.SelectboxColumn("Causa (CNC)", options=cnc_disponibles),
            },
        )

        if st.button("Guardar y calcular semana", type="primary"):
            df_para_guardar = df_editado.copy()
            df_para_guardar["cnc"] = df_para_guardar["cnc"].fillna("")
            df_para_guardar["semana"] = int(semana_actual)

            errores = (
                validar_ejecucion(df_para_guardar)
                + validar_consistencia(cronograma_df, df_para_guardar)
                + validar_precios_faltantes(df_para_guardar, precios_df)
            )
            if errores:
                st.error("Se encontraron errores de validación:")
                for error in errores:
                    st.markdown(f"- {error}")
            else:
                guardar_ejecucion_semana(int(semana_actual), df_para_guardar, RUTA_HISTORICO)
                errores_generales = _procesar_datos(int(semana_actual))
                if errores_generales:
                    st.error("Se encontraron errores al procesar todos los datos:")
                    for error in errores_generales:
                        st.markdown(f"- {error}")
                else:
                    st.success(f"Semana {int(semana_actual)} guardada y calculada correctamente.")

        st.markdown("---")
        st.markdown("##### C · Catálogo de causas de no cumplimiento (CNC)")
        st.caption("Fijo en el sistema — no se sube ni se edita.")
        st.markdown(
            " &nbsp; ".join(f"`{fila.codigo}` {fila.descripcion}" for fila in CAUSAS_DF.itertuples())
        )

with tab2:
    st.subheader("Curva S: Real vs. Esperado")
    resultados = st.session_state.get("resultados")

    if not resultados:
        st.info("Procesá los datos en la pestaña 'Datos y Registro' para ver la curva S.")
    else:
        comparacion = resultados["comparacion_curva_s"]
        fila_actual = comparacion[comparacion["semana"] == semana_actual]

        col1, col2, col3 = st.columns(3)
        real_actual = float(fila_actual["porcentaje_acumulado_real"].iloc[0]) if not fila_actual.empty else 0.0
        esperado_actual = float(fila_actual["porcentaje_acumulado_esperado"].iloc[0]) if not fila_actual.empty else 0.0
        col1.metric("Avance real acumulado", f"{real_actual:.1f}%")
        col2.metric("Esperado a la semana actual", f"{esperado_actual:.1f}%")
        if not fila_actual.empty:
            desviacion = float(fila_actual["desviacion"].iloc[0])
            estado = str(fila_actual["estado"].iloc[0])
            col3.metric("Desviación", f"{desviacion:+.2f} pp", estado)

        fig_curva = go.Figure()
        fig_curva.add_trace(
            go.Scatter(x=comparacion["semana"], y=comparacion["porcentaje_acumulado_real"], name="Real", mode="lines+markers")
        )
        fig_curva.add_trace(
            go.Scatter(x=comparacion["semana"], y=comparacion["porcentaje_acumulado_esperado"], name="Esperado", mode="lines+markers")
        )
        fig_curva.update_layout(height=400, xaxis_title="Semana", yaxis_title="% Acumulado")
        st.plotly_chart(fig_curva, use_container_width=True)

        st.markdown("#### Tabla comparativa por semana")
        st.dataframe(comparacion, use_container_width=True, hide_index=True)

with tab3:
    st.subheader(f"PPC — Semana {int(semana_actual)}")
    resultados = st.session_state.get("resultados")

    if not resultados:
        st.info("Procesá los datos en la pestaña 'Datos y Registro' para ver el PPC.")
    else:
        ppc_df = resultados["ppc_acumulado"]
        fila_ppc = ppc_df[ppc_df["semana"] == semana_actual]
        ppc_valor = float(fila_ppc["ppc"].iloc[0]) if not fila_ppc.empty else 0.0
        total_actividades = int(fila_ppc["total_actividades"].iloc[0]) if not fila_ppc.empty else 0
        cumplidas = int(fila_ppc["actividades_cumplidas"].iloc[0]) if not fila_ppc.empty else 0
        tendencia = ppc_valor - float(ppc_df["ppc"].iloc[0]) if not ppc_df.empty else 0.0

        col1, col2, col3 = st.columns(3)
        col1.metric("PPC semana actual", f"{ppc_valor:.1f}%", _semaforo_ppc(ppc_valor))
        col2.metric("Actividades cumplidas", f"{cumplidas} / {total_actividades}")
        col3.metric("Tendencia", f"{tendencia:+.1f} pp", f"desde semana {int(ppc_df['semana'].min())}" if not ppc_df.empty else None)

        if not ppc_df.empty:
            colores_pt = [_color_ppc(v) for v in ppc_df["ppc"]]
            fig_ppc = go.Figure()
            fig_ppc.add_trace(
                go.Scatter(
                    x=ppc_df["semana"], y=ppc_df["ppc"], mode="lines+markers", name="PPC",
                    line=dict(width=3, color="#2a78d6"), marker=dict(size=11, color=colores_pt),
                )
            )
            fig_ppc.add_hline(y=85, line_dash="dash", line_color="gray", annotation_text="Meta 85%")
            fig_ppc.add_hline(y=70, line_dash="dash", line_color="gray", annotation_text="Mínimo 70%")
            fig_ppc.update_layout(height=380, yaxis_title="PPC (%)", xaxis_title="Semana", yaxis_range=[0, 105])
            st.plotly_chart(fig_ppc, use_container_width=True)
            st.caption("🟢 En meta (≥85%) · 🟡 Atención (70–84%) · 🔴 Crítico (<70%)")

        st.markdown("#### Detalle de actividades — Semana actual")
        detalle = resultados["ppc_por_actividad"]
        detalle_semana = detalle[detalle["semana"] == semana_actual].copy()
        if detalle_semana.empty:
            st.info("No hay actividades registradas para esta semana todavía.")
        else:
            detalle_semana["porcentaje_avance"] = detalle_semana["porcentaje_avance"].round(1)
            detalle_semana["cumplida"] = detalle_semana["cumplida"].map({True: "Sí", False: "No"})
            st.dataframe(
                detalle_semana[
                    ["actividad", "frente", "volumen_programado", "volumen_ejecutado", "porcentaje_avance", "cumplida"]
                ],
                use_container_width=True,
                hide_index=True,
            )

with tab4:
    st.subheader("CNC y Acciones Correctivas")
    resultados = st.session_state.get("resultados")

    if not resultados:
        st.info("Procesá los datos en la pestaña 'Datos y Registro' para ver esta vista.")
    else:
        cnc_semana_df = resultados["cnc_semana_df"]
        cnc_total_df = resultados["cnc_total_df"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Incidencias · semana", int(resultados["frecuencias_semana_total"]))
        if not cnc_semana_df.empty:
            principal_semana = cnc_semana_df.iloc[0]
            col2.metric("Principal · semana", principal_semana["codigo"], f"{principal_semana['porcentaje']:.0f}%")
        else:
            col2.metric("Principal · semana", "—")
        col3.metric("Incidencias · acumulado", int(resultados["frecuencias_total_total"]))
        if not cnc_total_df.empty:
            principal_total = cnc_total_df.iloc[0]
            col4.metric("Principal · acumulado", principal_total["codigo"], f"{principal_total['porcentaje']:.0f}%")
        else:
            col4.metric("Principal · acumulado", "—")

        columnas_tabla = ["codigo", "descripcion", "categoria", "frecuencia", "porcentaje", "accion", "responsable"]

        st.markdown("---")
        st.markdown(f"##### CNC de la semana — Semana {int(semana_actual)}")
        if cnc_semana_df.empty:
            st.info("No se registraron causas de no cumplimiento esta semana.")
        else:
            fig_semana = px.bar(cnc_semana_df.sort_values("frecuencia"), x="frecuencia", y="codigo", orientation="h", text="porcentaje")
            fig_semana.update_layout(height=220, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_semana, use_container_width=True)
            st.dataframe(cnc_semana_df[columnas_tabla], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("##### CNC acumulado — Proyecto completo")
        if cnc_total_df.empty:
            st.info("Todavía no hay causas de no cumplimiento registradas.")
        else:
            fig_total = px.bar(cnc_total_df.sort_values("frecuencia"), x="frecuencia", y="codigo", orientation="h", text="porcentaje")
            fig_total.update_layout(height=250, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_total, use_container_width=True)
            st.dataframe(cnc_total_df[columnas_tabla], use_container_width=True, hide_index=True)

        st.caption("La 'acción correctiva' mostrada es la más reciente registrada para esa causa en la pestaña 'Acciones'.")

with tab5:
    st.subheader("Acciones Correctivas")

    st.markdown("#### Registro de Nuevas Acciones")
    with st.form("form_nueva_accion", clear_on_submit=True):
        cnc = st.selectbox("Causa CNC", options=CAUSAS_DF["codigo"].tolist())
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
                actualizar_estado(acciones_actuales, id_seleccionado, nuevo_estado)
                _guardar_acciones_semana(int(semana_actual), acciones_actuales)
                st.success("Estado actualizado.")
                st.rerun()

with tab6:
    st.subheader("Seguimiento de Semana Anterior")
    semanas_disponibles = [s for s in listar_semanas_procesadas(RUTA_HISTORICO) if s < semana_actual]

    if not semanas_disponibles:
        st.info("No hay semanas anteriores procesadas todavía.")
    else:
        semana_revisar = st.selectbox("Semana a revisar", options=semanas_disponibles, index=len(semanas_disponibles) - 1)
        acciones_previas = _obtener_acciones(int(semana_revisar))
        pendientes = [a for a in acciones_previas if a["estado"] in ("pendiente", "en_curso")]
        ids_vencidas = {accion["id"] for accion in listar_acciones_vencidas(acciones_previas)}

        if ids_vencidas:
            st.warning(
                f"⚠️ {len(ids_vencidas)} acción(es) con la fecha de plazo ya vencida — "
                "quedan marcadas abajo para que no pasen desapercibidas."
            )

        if not pendientes:
            st.info("No hay acciones pendientes o en curso en esa semana.")
        else:
            with st.form("form_seguimiento"):
                respuestas = {}
                for accion in pendientes:
                    etiqueta_vencida = " · ⚠️ VENCIDA" if accion["id"] in ids_vencidas else ""
                    st.markdown(
                        f"**{accion['cnc']}** - {accion['descripcion']} "
                        f"(responsable: {accion['responsable']}, plazo: {accion['fecha_plazo']}{etiqueta_vencida})"
                    )
                    completada = st.checkbox("¿Completada?", key=f"completada_{accion['id']}")
                    funciono = st.radio(
                        "¿Funcionó?", options=["positivo", "parcial", "negativo"], key=f"funciono_{accion['id']}", horizontal=True
                    )
                    observaciones = st.text_area("Observaciones", key=f"obs_{accion['id']}")
                    respuestas[accion["id"]] = (completada, funciono, observaciones)
                    st.divider()

                if st.form_submit_button("Guardar Seguimiento"):
                    for id_accion, (completada, funciono, observaciones) in respuestas.items():
                        nuevo_estado = "completada" if completada else "en_curso"
                        actualizar_estado(acciones_previas, id_accion, nuevo_estado, resultado=funciono, observaciones=observaciones)
                    _guardar_acciones_semana(int(semana_revisar), acciones_previas)
                    st.success("Seguimiento guardado. Ya podés cargar los datos de la semana actual.")

with tab7:
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
