# Gobierno y Riesgo - ControlPPC

Este documento cubre, como secciones separadas y explícitas, los cinco ejes de
gobierno: **permisos**, **fallas**, **respuesta**, **supervisión** y
**responsable**. Cada uno indica el mecanismo operativo concreto — quién, ante
qué condición, hace qué, y en qué plazo cuando corresponde — no sólo la
intención, con su cita de código o test.

## 1. Permisos — quién puede hacer qué, y cómo se aplica

| Rol | Puede | Mecanismo que lo aplica (no sólo lo declara) |
|---|---|---|
| **Supervisor de obra** | Cargar avance diario en la planilla de la semana actual | La planilla (`st.data_editor` en `streamlit_app.py`, tab "Datos y Registro") es el único punto de entrada de ejecución diaria; no existe endpoint ni editor de UI para escribir directamente en `data/historico/*.json` |
| **Jefe de obra / PM** | Ver el tablero, registrar y cerrar acciones correctivas | Formulario de alta (`crear_accion`) y selector de cambio de estado (`actualizar_estado`) en la tab "Acciones"; son los únicos dos puntos de escritura sobre acciones |
| **Responsable de acción** | Recibir una acción con su nombre y ejecutarla | El campo `responsable` es obligatorio (`validar_accion`); no se puede guardar una acción sin nombrar a alguien |
| *(nadie, por diseño)* | Editar el catálogo de causas (CNC) | `CAUSAS_DF` se carga en `streamlit_app.py` directamente desde `data/causas_incumplimiento.csv`; ninguna pestaña tiene un `file_uploader` ni un editor para ese archivo |

**Brecha declarada**: estos permisos son por rol de la interfaz, no por usuario
autenticado — no hay login (ver sección 6).

## 2. Fallas — catálogo de riesgos identificados

Dos tipos de falla distintos, porque requieren respuestas distintas (sección 3):

**Fallas técnicas** (dato mal cargado — se detectan al instante, al validar):

| Falla | Dónde se detecta |
|---|---|
| CSV de cronograma sin la columna esperada | `src/validador.py::validar_cronograma` |
| Volumen ejecutado negativo | `src/validador.py::validar_ejecucion` |
| Actividad ejecutada que no figura en el cronograma de esa semana/frente | `src/validador.py::validar_consistencia` |
| Precio unitario faltante para una actividad ejecutada | `src/validador.py::validar_precios_faltantes` (ver DEC-007) |
| Total del proyecto = 0 al calcular % financiero | `src/calculador_inversion.py::calcular_porcentaje_financiero` |
| Acción correctiva sin responsable o sin descripción | `src/gestor_acciones.py::validar_accion` |
| Semana histórica solicitada que no existe | `src/persistencia.py` (devuelve vacío, no error no controlado) |

**Riesgos operativos** (el dato está bien cargado, pero el proyecto va mal):

| Riesgo | Cómo se hace visible |
|---|---|
| PPC crítico (<70%) una o más semanas | Tab "PPC": semáforo 🔴 y línea de referencia "mínimo 70%" |
| Curva S "Atrasado" (desviación real vs. esperado) | Tab "Curva S": estado calculado por `clasificar_estado` |
| Una causa CNC se repite semana a semana | Tab "CNC y Acciones": sección "CNC acumulado" |
| Acción correctiva vencida (pasó `fecha_plazo` sin resolverse) | `src/gestor_acciones.py::listar_acciones_vencidas` (ver sección 3) |

## 3. Respuesta — qué pasa cuando una falla ocurre, y en qué plazo

| Falla | Respuesta | Plazo / disparador |
|---|---|---|
| Cualquier falla técnica de la sección 2 | Se rechaza la carga completa (no se guarda nada parcial) y se listan todos los errores encontrados, no un mensaje genérico | Inmediato — la carga no continúa hasta corregir |
| Acción correctiva vencida | `listar_acciones_vencidas` la marca; la tab "Seguimiento" la muestra con la etiqueta "⚠️ VENCIDA" y un aviso agregado en la parte superior | Se evalúa cada vez que se abre la tab "Seguimiento", contra la fecha del día |
| PPC crítico (<70%) en la semana | El jefe de obra debe registrar al menos una acción correctiva para una causa del Top 5 de esa semana | Antes de cerrar el ciclo de la semana siguiente (mecanismo organizacional — el sistema lo hace visible, no lo bloquea todavía; ver brecha declarada en sección 6) |
| Curva S "Atrasado" dos semanas seguidas | Escalar a nivel gerencial fuera del sistema | El histórico (tab "Histórico") es la fuente para detectarlo: dos filas consecutivas en "Atrasado" |

El mecanismo técnico (rechazo inmediato de datos inválidos, y marcado de
acciones vencidas) está en código y testeado
(`tests/test_validador.py`, `tests/test_acciones.py::test_listar_acciones_vencidas_detecta_plazo_pasado`).
Los mecanismos organizacionales (escalar un PPC crítico o una curva S atrasada)
dependen hoy de que el jefe de obra revise las tabs correspondientes — el
sistema los hace visibles pero no los bloquea automáticamente; se declara así
en vez de sobre-representarlo.

## 4. Supervisión — el sistema no decide, reporta

El sistema **nunca** asigna automáticamente una acción correctiva ni cambia el
estado de una sin que un humano presione un botón:

- `actualizar_estado` sólo se invoca desde el botón "Actualizar Estado" (tab
  Acciones) o "Guardar Seguimiento" (tab Seguimiento) — nunca desde un cálculo.
- Toda acción exige responsable + descripción + plazo antes de guardarse
  (`validar_accion`); si falta alguno, `crear_accion` lanza `ValueError`.
- El sistema calcula y prioriza (PPC, curva S, Top CNC semanal/acumulado);
  decidir qué hacer con esa información es siempre una acción humana explícita.
- La tab "Seguimiento" obliga a revisar cada acción pendiente/en curso de la
  semana anterior (¿se completó?, ¿funcionó?, observaciones) antes de
  considerar cerrado ese ciclo — no hay forma de saltearlo desde la UI.

## 5. Responsable — matriz RACI por actividad

R = Responsable (ejecuta) · A = Aprueba (Accountable) · C = Consultado · I = Informado

| Actividad | R | A | C | I |
|---|---|---|---|---|
| Cargar programa de obra y precios | Jefe de obra | Jefe de obra | — | Supervisor de obra |
| Registrar avance diario (planilla) | Supervisor de obra | Jefe de obra | — | — |
| Procesar y calcular la semana | Jefe de obra | Jefe de obra | Supervisor de obra (si hay error de validación) | — |
| Registrar acción correctiva | Jefe de obra | Jefe de obra | Responsable de acción | Responsable de acción |
| Ejecutar la acción correctiva | Responsable de acción | Jefe de obra | — | Jefe de obra (en Seguimiento) |
| Cerrar / actualizar estado de una acción | Jefe de obra | Jefe de obra | Responsable de acción | — |
| Editar el catálogo de causas (CNC) | *nadie — bloqueado por diseño* | — | — | — |

Además: ninguna acción correctiva se guarda sin `responsable` y `email`
(`validar_accion`, con formato de email verificado por regex), y
`obtener_accion_vigente_por_cnc` permite trazar, para cualquier causa
recurrente, quién es responsable de resolverla hoy — no queda diluida entre
varias acciones históricas sin nombre.

## 6. Permisos y acceso a datos (infraestructura)

- El sistema corre localmente o en una instancia de Streamlit Cloud controlada por el equipo del proyecto; no expone una API pública de escritura.
- Los datos históricos (`data/historico/`) son archivos JSON versionables; cualquier cambio queda en el historial de Git del repositorio, permitiendo auditoría de quién modificó qué y cuándo.
- No se almacenan credenciales, tokens ni datos personales sensibles en el repositorio (verificado: `requirements.txt` no incluye SDKs de IA ni librerías que requieran API key — ver `tests/test_sin_ia_en_runtime.py`).

## Riesgo conocido y no mitigado (declarado explícitamente)

- El sistema no verifica que el usuario que carga el avance diario sea efectivamente el supervisor de obra asignado (no hay autenticación de usuarios). En la versión actual, el control de "quién cargó qué" es organizacional (un único responsable de carga por obra), no técnico.
- La respuesta ante un PPC crítico o una curva S atrasada (sección 3) es organizacional: el sistema la hace visible en el tablero, pero no bloquea el flujo si el jefe de obra no actúa.

Ambas brechas se declaran como mejora futura, no como funcionalidad ya cubierta.
