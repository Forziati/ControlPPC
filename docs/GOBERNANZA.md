# Gobierno y Riesgo - ControlPPC

Este documento cubre los cinco ejes de gobierno del sistema: **permisos**,
**supervisión**, **respuesta ante fallas**, **revisión** y **responsabilidad**.
Cada uno indica el mecanismo operativo concreto (no sólo la intención) y dónde
verificarlo en el código.

## 1. Permisos — quién puede hacer qué, y cómo se aplica

| Rol | Puede | Mecanismo que lo aplica (no sólo lo declara) |
|---|---|---|
| **Supervisor de obra** | Cargar avance diario en la planilla de la semana actual | La planilla (`st.data_editor` en `streamlit_app.py`, tab "Datos y Registro") es el único punto de entrada de ejecución diaria; no existe endpoint ni editor de UI para escribir directamente en `data/historico/*.json` |
| **Jefe de obra / PM** | Ver el tablero, registrar y cerrar acciones correctivas | Formulario de alta (`crear_accion`) y selector de cambio de estado (`actualizar_estado`) en la tab "Acciones"; son los únicos dos puntos de escritura sobre acciones |
| **Responsable de acción** | Recibir una acción con su nombre y ejecutarla | El campo `responsable` es obligatorio (`validar_accion`); no se puede guardar una acción sin nombrar a alguien |
| *(nadie, por diseño)* | Editar el catálogo de causas (CNC) | `CAUSAS_DF` se carga en `streamlit_app.py` directamente desde `data/causas_incumplimiento.csv`; ninguna pestaña tiene un `file_uploader` ni un editor para ese archivo — el permiso "no se edita" está aplicado por ausencia del control en el código, no sólo escrito acá |

**Brecha declarada** (ver también sección 6): estos permisos son por rol de la
interfaz, no por usuario autenticado — no hay login. Ver riesgo conocido al
final.

## 2. Supervisión humana — el sistema no decide, reporta

El sistema **nunca** asigna automáticamente una acción correctiva ni cambia el
estado de una sin que un humano presione un botón:

- `actualizar_estado` sólo se invoca desde el botón "Actualizar Estado" (tab
  Acciones) o "Guardar Seguimiento" (tab Seguimiento) — nunca desde un cálculo.
- Toda acción exige responsable + descripción + plazo antes de guardarse
  (`gestor_acciones.py::validar_accion`); si falta alguno, `crear_accion`
  lanza `ValueError` y no se persiste nada.
- El sistema calcula y prioriza (PPC, curva S, Top CNC semanal/acumulado);
  decidir qué hacer con esa información es siempre una acción humana explícita.

## 3. Respuesta ante fallas — qué pasa cuando algo sale mal

Mecanismo general: toda carga pasa por `validador.py` **antes** de calcular o
guardar nada. Si hay errores, `_procesar_datos` devuelve la lista completa de
errores (no un mensaje genérico) y el flujo se corta antes de llegar a
`guardar_cierre` / `guardar_ejecucion_semana` — no queda un estado a medio
guardar.

| Situación de falla | Mecanismo de respuesta | Evidencia en código |
|---|---|---|
| CSV de cronograma sin la columna esperada | Se rechaza la carga con mensaje de error explícito | `src/validador.py::validar_cronograma` |
| Volumen ejecutado negativo | Se rechaza la fila / se marca para revisión | `src/validador.py::validar_ejecucion` |
| Actividad ejecutada que no figura en el cronograma de esa semana/frente | Se rechaza la carga y se lista cada inconsistencia encontrada | `src/validador.py::validar_consistencia` |
| Precio unitario faltante para una actividad ejecutada | Se rechaza la carga en vez de calcular esa actividad como $0 de forma silenciosa | `src/validador.py::validar_precios_faltantes`, cubierto por `tests/test_validador.py::test_validar_precios_faltantes_detecta_actividad_sin_precio` — ver `DECISIONES.md`, DEC-007 |
| Total del proyecto = 0 al calcular % financiero | Se lanza `ValueError` explícito en lugar de una división por cero silenciosa | `src/calculador_inversion.py::calcular_porcentaje_financiero`, cubierto por `tests/test_inversion.py::test_porcentaje_financiero_total_cero_lanza_error` |
| Acción correctiva sin responsable o sin descripción | No se guarda; se exige completar campos obligatorios | `src/gestor_acciones.py::validar_accion`, cubierto por `tests/test_acciones.py::test_crear_accion_campos_faltantes` |
| Semana histórica solicitada que no existe | Devuelve lista/estructura vacía en lugar de error no controlado | `src/persistencia.py`, cubierto por `tests/test_persistencia.py::test_cargar_cierre_inexistente` |

## 4. Revisión — el ciclo semanal obliga a mirar hacia atrás

- **Antes de actuar**: el jefe de obra ve PPC, curva S y CNC (semanal y
  acumulado) en tabs dedicadas antes de decidir qué acción registrar — no se
  puede saltar directo del dato crudo a la acción sin pasar por esas vistas.
- **A la semana siguiente**: la tab "Seguimiento" lista todas las acciones en
  estado `pendiente` o `en_curso` de la semana anterior y obliga a revisarlas
  una por una (¿se completó?, ¿funcionó?, observaciones) antes de continuar
  con la semana actual — no hay forma de "saltear" ese repaso desde la UI.
- **Multi-semana**: la tab "Histórico" permite auditar tendencias de varias
  semanas juntas (PPC, % financiero, desviación de curva S, CNC por semana),
  para revisar patrones que una sola semana no muestra.

## 5. Responsabilidad — toda acción tiene un nombre y un correo

- Ninguna acción correctiva se guarda sin `responsable` y `email` (campos
  obligatorios validados por `validar_accion`, con formato de email verificado
  por regex).
- `gestor_acciones.py::obtener_accion_vigente_por_cnc` permite, para cualquier
  causa recurrente, trazar quién es el responsable vigente hoy de resolverla
  — no queda "diluida" entre varias acciones históricas sin nombre.
- El catálogo de causas de no cumplimiento (`data/causas_incumplimiento.csv`)
  es de solo lectura para todos los roles (ver sección 1): mantiene
  consistencia histórica entre semanas (ver `DECISIONES.md`, DEC-004).

## 6. Permisos y acceso a datos (infraestructura)

- El sistema corre localmente o en una instancia de Streamlit Cloud controlada por el equipo del proyecto; no expone una API pública de escritura.
- Los datos históricos (`data/historico/`) son archivos JSON versionables; cualquier cambio queda en el historial de Git del repositorio, permitiendo auditoría de quién modificó qué y cuándo.
- No se almacenan credenciales, tokens ni datos personales sensibles en el repositorio (verificado: `requirements.txt` no incluye SDKs de IA ni librerías que requieran API key — ver `tests/test_sin_ia_en_runtime.py`).

## Riesgo conocido y no mitigado (declarado explícitamente)

- El sistema no verifica que el usuario que carga el avance diario sea efectivamente el supervisor de obra asignado (no hay autenticación de usuarios). En la versión actual, el control de "quién cargó qué" es organizacional (un único responsable de carga por obra), no técnico. Se declara como mejora futura, no como funcionalidad ya cubierta.
