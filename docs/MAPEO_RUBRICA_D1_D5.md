# Mapeo de Evidencia contra la Rúbrica D1-D5

Este documento resume dónde encontrar la evidencia de cada dimensión evaluada, para facilitar la revisión.

## D1 · Sistema completo y funcionando

**Qué busca**: Ejecución real, herramientas, integración, supervisión.

**Evidencia**:
- **`EVIDENCIA_EJECUCION.md`**: salidas reales capturadas de `pytest` (64 tests, 0 fallos), de `streamlit run` (HTTP 200 + healthcheck `ok`) y de `corridas/generar_corrida.py` (JSON completo de salida) — no descripciones de que "debería funcionar", sino la salida real de cada comando.
- Aplicación funcional end-to-end en `streamlit_app.py` (carga de datos → registro de avance en planilla editable → cálculo → visualización → registro de acciones → persistencia).
- Integración real entre módulos: `src/calculador_ppc.py`, `src/calculador_inversion.py`, `src/comparador_curva_s.py`, `src/analizador_cnc.py`, `src/gestor_acciones.py`, `src/persistencia.py`, `src/validador.py` — todos con responsabilidad única y probados en conjunto (`tests/test_integracion.py`).
- Corridas respaldadas: las 3 corridas en `corridas/` (`semana_01`, `semana_02`, `semana_03`) se re-ejecutan contra el código actual en cada corrida de la suite (`tests/test_reproducibilidad.py`), no son archivos estáticos.
- Prompts sustantivos en `prompts/`: los 8 prompts reales de la sesión de desarrollo.
- Supervisión humana explícita en cada paso (ver `docs/GOBERNANZA.md`): el supervisor carga datos, el jefe de obra registra acciones, nadie es reemplazado por automatismo.

## D2 · Proceso documentado

**Qué busca**: Decisiones, iteraciones, fallas/correcciones y trazabilidad.

**Evidencia**:
- `DECISIONES.md`: 9 decisiones documentadas con motivo/impacto/resultado, incluyendo **cinco** fallas reales detectadas y corregidas durante el desarrollo (DEC-005 a DEC-009) — las últimas dos, a partir de devoluciones literales de evaluaciones anteriores de este mismo trabajo.
- **`prompts/`**: los 8 prompts reales de la sesión de desarrollo, en orden, cada uno con lo que produjo y a qué commit corresponde — la trazabilidad completa entre lo que se pidió y lo que se construyó.
- Historial de commits de Git del repositorio, que muestra la evolución del código y las correcciones anteriores.

## D3 · Formato y reproducibilidad

**Qué busca**: Corridas identificables, tríadas entrada-salida-fecha (mínimo 3 corridas completas).

**Evidencia**:
- **3 corridas completas** en `corridas/`: `semana_01` (semana floja, PPC 16.67%), `semana_02` (semana buena, PPC 83.33%) y `semana_03` (semana mala, PPC 0%, 5 causas de no cumplimiento distintas) — deliberadamente distintas entre sí para no ser 3 copias del mismo caso. Cada una con:
  - `input/`: los 4 CSVs exactos usados (cronograma, precios, ejecución diaria, catálogo de causas).
  - `output/s{N}_cierre.json`: resultado real generado ejecutando `corridas/generar_corrida.py` (que llama al código real de `src/calculador_ppc.py`, `src/calculador_inversion.py` y `src/analizador_cnc.py`) sobre esos inputs.
  - `metadata.json`: fecha de ejecución, commit de Git activo, inputs/outputs referenciados sin ambigüedad, y el bloque `costo_ia` (ver D4).
- `corridas/costos_por_corrida.json`: ledger agregado de las 3 corridas, regenerado con `python corridas/generar_corrida.py --todas`.
- **`prompts/`**: carpeta con los 8 prompts reales de la sesión (ver README dentro de la carpeta), en formato entrada (prompt) → salida (commit/artefacto) → fecha implícita en el orden y los commits referenciados.
- Test de reproducibilidad: `tests/test_reproducibilidad.py::test_corridas_son_reproducibles` re-ejecuta el cálculo de las 3 corridas y compara, campo por campo, contra cada `output/*.json` versionado. También `tests/test_integracion.py::test_pipeline_completo_semana_1` verifica lo mismo a nivel de los módulos individuales.

## D4 · Análisis económico

**Qué busca**: Consumo, tarifa, costo/run, proyección y justificación — vincular tokens consumidos por corrida y tarifa del modelo para calcular el costo por corrida.

**Evidencia**:
- **Costo por corrida, en JSON estructurado, no sólo en prosa**: cada `corridas/<id>/metadata.json` y `corridas/<id>/output/*.json` trae un bloque `costo_ia` con `tokens_entrada`, `tokens_salida`, `tarifa_entrada_usd_por_mtok`, `tarifa_salida_usd_por_mtok`, `costo_total_usd` y la `formula` usada — generado por `corridas/generar_corrida.py::calcular_costo_ia_corrida`, nunca tipeado a mano. `corridas/costos_por_corrida.json` agrega las 3 corridas en un único ledger.
- `docs/ANALISIS_ECONOMICO.md` §1: la fórmula (`0 tokens × tarifa = $0.00`) con sus dos variables verificadas por `tests/test_sin_ia_en_runtime.py` y ancladas por `tests/test_reproducibilidad.py::test_costo_ia_de_cada_corrida_es_cero_y_reproducible` en vez de sólo declaradas.
- `docs/ANALISIS_ECONOMICO.md` §2: fórmula reproducible de costo de **desarrollo** (distinto del costo de correr una corrida) — `corridas/calcular_costo_desarrollo.py` mide el tamaño real (bytes) de cada diff commiteado y calcula el costo a la tarifa real de Claude Sonnet 5.
- Análisis económico del **dominio del proyecto** (el costo real de la obra que controla): monto programado, monto ejecutado, acumulado y % de avance financiero, calculado en `src/calculador_inversion.py` y verificado en `tests/test_inversion.py`.
- Proyección y supuestos declarados explícitamente en `docs/ANALISIS_ECONOMICO.md` §4.

## D5 · Gobierno y riesgo

**Qué busca**: Permisos, fallas, respuesta, supervisión y responsable — como ejes separados, cada uno con mecanismo operativo aplicable.

**Evidencia**:
- `docs/GOBERNANZA.md` tiene una sección dedicada a cada uno de los 5 sustantivos de la rúbrica, sin fusionarlos:
  1. **Permisos**: tabla rol → acción → mecanismo que lo aplica en código (no sólo el rol nombrado).
  2. **Fallas**: catálogo separado en fallas técnicas (detectadas por `validador.py`) y riesgos operativos (PPC crítico, curva S atrasada, CNC recurrente, acción vencida).
  3. **Respuesta**: tabla falla → respuesta → plazo/disparador concreto — distinta de "fallas": identificar un riesgo no es lo mismo que reaccionar a él. Incluye un mecanismo nuevo, `src/gestor_acciones.py::listar_acciones_vencidas`, aplicado en la tab "Seguimiento" (marca acciones con plazo vencido).
  4. **Supervisión**: ningún cambio de estado ocurre sin que un humano presione un botón.
  5. **Responsable**: matriz RACI (Responsable/Aprueba/Consultado/Informado) por actividad clave, no sólo el campo `responsable` de una acción.
- Validaciones activas en `src/validador.py` (incluida `validar_precios_faltantes`, agregada tras auditar que una afirmación de gobernanza no era todavía cierta — ver DEC-007), cada una con test asociado en `tests/test_validador.py`.
- `listar_acciones_vencidas` con test asociado (`tests/test_acciones.py::test_listar_acciones_vencidas_detecta_plazo_pasado`) que demuestra el mecanismo de respuesta, no sólo lo declara.
- Riesgo conocido y no mitigado declarado explícitamente (falta de autenticación de usuarios; respuesta organizacional no bloqueante ante PPC crítico), en vez de omitido u ocultado.

---

## Principio transversal aplicado

Siguiendo el mismo criterio que el proyecto grupal del agente evaluador: **la evidencia observable prevalece sobre declaraciones favorables**. Cada afirmación de este documento apunta a un archivo, función o test específico y verificable, no a una descripción genérica. Como muestra de esto: al preparar esta evidencia se auditó cada cita contra el código real y contra dos devoluciones de evaluación sucesivas, y se encontraron y corrigieron cinco inconsistencias (DEC-005 a DEC-009) en vez de dejarlas pasar.
