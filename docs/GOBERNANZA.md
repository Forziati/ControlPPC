# Gobierno y Riesgo - ControlPPC

## Roles y responsables

| Rol | Responsabilidad | Qué puede hacer en el sistema |
|---|---|---|
| **Supervisor de obra** | Carga el avance diario ejecutado | Completa la planilla de ejecución diaria; no edita precios ni cronograma |
| **Jefe de obra / PM** | Revisa el cierre semanal, define acciones correctivas | Ve el tablero, registra acciones con responsable y plazo |
| **Responsable de acción** | Ejecuta la acción correctiva asignada | Recibe la acción con su nombre; su cumplimiento se revisa en la semana siguiente (`Seguimiento`) |

El catálogo de causas de no cumplimiento (`data/causas_incumplimiento.csv`) es de solo lectura para todos los roles: ningún usuario lo edita desde la interfaz, para mantener consistencia histórica (ver `DECISIONES.md`, DEC-004).

## Supervisión humana — el sistema no decide, reporta

El sistema **nunca** asigna automáticamente una acción correctiva ni un responsable. Su única función es:

1. Calcular métricas (PPC, inversión, curva S) a partir de datos que un humano cargó.
2. Identificar y priorizar (Top 5 CNC por frecuencia, semanal y acumulado).
3. Ofrecer un formulario para que **un humano** registre la acción, el responsable y el plazo.

Ninguna decisión de gestión de personas, presupuesto o cronograma queda delegada al sistema.

## Manejo de fallas y validaciones

| Situación de falla | Cómo responde el sistema | Evidencia en código |
|---|---|---|
| CSV de cronograma sin la columna esperada | Se rechaza la carga con mensaje de error explícito | `src/validador.py::validar_cronograma` |
| Volumen ejecutado negativo o inconsistente | Se rechaza la fila / se marca para revisión | `src/validador.py::validar_ejecucion` |
| Actividad ejecutada que no figura en el cronograma de esa semana/frente | Se rechaza la carga y se lista cada inconsistencia encontrada | `src/validador.py::validar_consistencia` |
| Precio unitario faltante para una actividad ejecutada | Se rechaza la carga en vez de calcular esa actividad como $0 de forma silenciosa (comportamiento real de `calcular_monto_ejecutado` si no se valida antes) | `src/validador.py::validar_precios_faltantes`, cubierto por `tests/test_validador.py::test_validar_precios_faltantes_detecta_actividad_sin_precio` — ver `DECISIONES.md`, DEC-007 |
| Total del proyecto = 0 al calcular % financiero | Se lanza `ValueError` explícito en lugar de devolver un resultado engañoso (ej. división por cero silenciosa) | `src/calculador_inversion.py::calcular_porcentaje_financiero`, cubierto por `tests/test_inversion.py::test_porcentaje_financiero_total_cero_lanza_error` |
| Acción correctiva sin responsable o sin descripción | No se guarda; se exige completar campos obligatorios | `src/gestor_acciones.py::validar_accion`, cubierto por `tests/test_acciones.py::test_crear_accion_campos_faltantes` |
| Semana histórica solicitada que no existe | Devuelve lista/estructura vacía en lugar de error no controlado | `src/persistencia.py`, cubierto por `tests/test_persistencia.py::test_cargar_cierre_inexistente` |

## Permisos y acceso a datos

- El sistema corre localmente o en una instancia de Streamlit Cloud controlada por el equipo del proyecto; no expone una API pública de escritura.
- Los datos históricos (`data/historico/`) son archivos JSON versionables; cualquier cambio queda en el historial de Git del repositorio, permitiendo auditoría de quién modificó qué y cuándo.
- No se almacenan credenciales, tokens ni datos personales sensibles en el repositorio (verificado: `requirements.txt` no incluye SDKs de IA ni librerías que requieran API key).

## Riesgo conocido y no mitigado (declarado explícitamente)

- El sistema no verifica que el usuario que carga el avance diario sea efectivamente el supervisor de obra asignado (no hay autenticación de usuarios). En la versión actual, el control de "quién cargó qué" es organizacional (un único responsable de carga por obra), no técnico. Se declara como mejora futura, no como funcionalidad ya cubierta.
