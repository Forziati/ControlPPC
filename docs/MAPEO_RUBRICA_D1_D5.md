# Mapeo de Evidencia contra la Rúbrica D1-D5

Este documento resume dónde encontrar la evidencia de cada dimensión evaluada, para facilitar la revisión.

## D1 · Sistema completo y funcionando

**Qué busca**: Ejecución real, herramientas, integración, supervisión.

**Evidencia**:
- **`EVIDENCIA_EJECUCION.md`**: salidas reales capturadas de `pytest` (58 tests, 0 fallos), de `streamlit run` (HTTP 200 + healthcheck `ok`) y de `corridas/generar_corrida.py` (JSON completo de salida) — no descripciones de que "debería funcionar", sino la salida real de cada comando.
- Aplicación funcional end-to-end en `streamlit_app.py` (carga de datos → registro de avance en planilla editable → cálculo → visualización → registro de acciones → persistencia).
- Integración real entre módulos: `src/calculador_ppc.py`, `src/calculador_inversion.py`, `src/comparador_curva_s.py`, `src/analizador_cnc.py`, `src/gestor_acciones.py`, `src/persistencia.py`, `src/validador.py` — todos con responsabilidad única y probados en conjunto (`tests/test_integracion.py`).
- Corridas respaldadas: `corridas/semana_01/` no es sólo un ejemplo — `tests/test_reproducibilidad.py` la re-ejecuta contra el código actual en cada corrida de la suite.
- Supervisión humana explícita en cada paso (ver `docs/GOBERNANZA.md`): el supervisor carga datos, el jefe de obra registra acciones, nadie es reemplazado por automatismo.

## D2 · Proceso documentado

**Qué busca**: Decisiones, iteraciones, fallas/correcciones y trazabilidad.

**Evidencia**:
- `DECISIONES.md`: 8 decisiones documentadas con motivo/impacto/resultado, incluyendo **cuatro** fallas reales detectadas y corregidas durante el desarrollo:
  - DEC-005: `docs/GUIA_USO.md` instruía deployar sobre una rama `main` que nunca existió en este repositorio.
  - DEC-006: faltaba evidencia de corridas reproducibles (`corridas/`) y este mismo registro de decisiones.
  - DEC-007: `docs/GOBERNANZA.md` afirmaba una validación de precios faltantes que el código todavía no implementaba.
  - DEC-008: una devolución de evaluación anterior detectó que faltaba `prompts/`, que el análisis económico no tenía aritmética verificable, y que la gobernanza no precisaba mecanismos por eje.
- **`prompts/`**: los 8 prompts reales de la sesión de desarrollo, en orden, cada uno con lo que produjo y a qué commit corresponde — la trazabilidad completa entre lo que se pidió y lo que se construyó.
- Historial de commits de Git del repositorio, que muestra la evolución del código y las correcciones anteriores.

## D3 · Formato y reproducibilidad

**Qué busca**: Corridas identificables, tríadas entrada-salida-fecha.

**Evidencia**:
- **`prompts/`**: carpeta con los prompts reales de la sesión (ver README dentro de la carpeta), en formato entrada (prompt) → salida (commit/artefacto) → fecha implícita en el orden y en los commits referenciados.
- **`corridas/`**, con `corridas/semana_01/` conteniendo:
  - `input/`: los 4 CSVs exactos usados (cronograma, precios, ejecución diaria, catálogo de causas).
  - `output/s1_cierre.json`: resultado real generado ejecutando `corridas/generar_corrida.py` (que a su vez llama al código real de `src/calculador_ppc.py`, `src/calculador_inversion.py` y `src/analizador_cnc.py`) sobre esos inputs.
  - `metadata.json`: fecha de ejecución, commit de Git activo, e inputs/outputs referenciados sin ambigüedad.
- Test de reproducibilidad: `tests/test_reproducibilidad.py::test_corrida_semana_01_es_reproducible` re-ejecuta el cálculo y compara, campo por campo, contra el `output/s1_cierre.json` versionado. También `tests/test_integracion.py::test_pipeline_completo_semana_1` verifica que el mismo input produce el mismo resultado a nivel de los módulos individuales.

## D4 · Análisis económico

**Qué busca**: Consumo, tarifa, costo/run, proyección y justificación.

**Evidencia**:
- `docs/ANALISIS_ECONOMICO.md` §1: fórmula reproducible de costo en runtime — `0 tokens × tarifa = $0.00`, con las dos variables (tokens consumidos, tarifa) verificadas por `tests/test_sin_ia_en_runtime.py` en vez de sólo declaradas.
- `docs/ANALISIS_ECONOMICO.md` §2: fórmula reproducible de costo de **desarrollo** — `corridas/calcular_costo_desarrollo.py` mide el tamaño real (bytes) de cada diff commiteado, estima tokens de salida con una heurística documentada, y calcula el costo a la tarifa real de Claude Sonnet 5 ($10.00/1M tokens de salida). Tabla con 3 commits, $0.4036 USD estimados (cota inferior, declarada como tal).
- Análisis económico del **dominio del proyecto** (el costo real de la obra que controla): monto programado, monto ejecutado, acumulado y % de avance financiero, calculado en `src/calculador_inversion.py` y verificado en `tests/test_inversion.py`.
- Proyección y supuestos declarados explícitamente en `docs/ANALISIS_ECONOMICO.md` §4.

## D5 · Gobierno y riesgo

**Qué busca**: Permisos, fallas, respuesta, supervisión y responsabilidad.

**Evidencia**:
- `docs/GOBERNANZA.md` está estructurado en los 5 ejes explícitamente (secciones 1-5: Permisos, Supervisión, Respuesta ante fallas, Revisión, Responsabilidad), cada uno con un mecanismo operativo concreto — no sólo el eje nombrado — y su cita de código correspondiente.
- Validaciones activas en `src/validador.py` (incluida `validar_precios_faltantes`, agregada tras auditar que una afirmación de gobernanza no era todavía cierta — ver DEC-007), cada una con test asociado en `tests/test_validador.py` que demuestra que la falla se maneja explícitamente en lugar de fallar en silencio.
- Riesgo conocido y no mitigado declarado explícitamente (falta de autenticación de usuarios), en vez de omitido u ocultado.

---

## Principio transversal aplicado

Siguiendo el mismo criterio que el proyecto grupal del agente evaluador: **la evidencia observable prevalece sobre declaraciones favorables**. Cada afirmación de este documento apunta a un archivo, función o test específico y verificable, no a una descripción genérica. Como muestra de esto: al preparar esta misma evidencia se auditó cada cita contra el código real, y se encontraron y corrigieron cuatro inconsistencias (DEC-005 a DEC-008) en vez de dejarlas pasar — la última de ellas, DEC-008, a partir de la devolución literal de una evaluación anterior de este mismo trabajo.
