# Prompt 5 - Aprobación del diseño

**Prompt real del usuario:**

> si misma solapa

(Respuesta a la pregunta de si el rediseño de CNC debía ir en una quinta pestaña
nueva o dentro de la misma pestaña "CNC y Acciones".)

**Resultado:** con el diseño ya aprobado, recién en este punto se modificó el
repositorio real:

- `src/comparador_curva_s.py`: nueva función `calcular_curva_s_esperada_desde_cronograma`.
- `src/persistencia.py`: `guardar_ejecucion_semana`, `cargar_ejecucion_semana`,
  `cargar_ejecucion_historica`, `listar_semanas_con_ejecucion`.
- `src/gestor_acciones.py`: `obtener_accion_vigente_por_cnc`.
- `streamlit_app.py`: reescrito con 7 tabs — "Datos y Registro" (2 uploads +
  planilla editable con `st.data_editor`), "Curva S", "PPC" (línea), "CNC y
  Acciones" (semanal + acumulado con acción/responsable), y las tabs de
  Acciones/Seguimiento/Histórico sin cambios de diseño.
- 10 tests nuevos.

Commit `eaf3009`.
