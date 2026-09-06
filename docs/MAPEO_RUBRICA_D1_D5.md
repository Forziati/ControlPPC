# Mapeo de Evidencia contra la Rúbrica D1-D5

Este documento resume dónde encontrar la evidencia de cada dimensión evaluada, para facilitar la revisión.

## D1 · Sistema completo y funcionando

**Qué busca**: Ejecución real, herramientas, integración, supervisión.

**Evidencia**:
- Aplicación funcional end-to-end en `streamlit_app.py` (carga de datos → registro de avance en planilla editable → cálculo → visualización → registro de acciones → persistencia).
- Integración real entre módulos: `src/calculador_ppc.py`, `src/calculador_inversion.py`, `src/comparador_curva_s.py`, `src/analizador_cnc.py`, `src/gestor_acciones.py`, `src/persistencia.py`, `src/validador.py` — todos con responsabilidad única y probados en conjunto (`tests/test_integracion.py`).
- Ejecución verificable: `streamlit run streamlit_app.py` levanta la app y responde en `http://localhost:8501`.
- Supervisión humana explícita en cada paso (ver `docs/GOBERNANZA.md`): el supervisor carga datos, el jefe de obra registra acciones, nadie es reemplazado por automatismo.

## D2 · Proceso documentado

**Qué busca**: Decisiones, iteraciones, fallas/correcciones y trazabilidad.

**Evidencia**:
- `DECISIONES.md`: 7 decisiones documentadas con motivo/impacto/resultado, incluyendo **tres** fallas reales detectadas y corregidas durante el desarrollo:
  - DEC-005: `docs/GUIA_USO.md` instruía deployar sobre una rama `main` que nunca existió en este repositorio.
  - DEC-006: faltaba evidencia de corridas reproducibles (`corridas/`) y este mismo registro de decisiones.
  - DEC-007: `docs/GOBERNANZA.md` afirmaba una validación de precios faltantes que el código todavía no implementaba.
- Historial de commits de Git del repositorio, que muestra la evolución del código y las correcciones anteriores.

## D3 · Formato y reproducibilidad

**Qué busca**: Corridas identificables, tríadas entrada-salida-fecha.

**Evidencia**:
- Carpeta `corridas/`, con `corridas/semana_01/` conteniendo:
  - `input/`: los 4 CSVs exactos usados (cronograma, precios, ejecución diaria, catálogo de causas).
  - `output/s1_cierre.json`: resultado real generado ejecutando `corridas/generar_corrida.py` (que a su vez llama al código real de `src/calculador_ppc.py`, `src/calculador_inversion.py` y `src/analizador_cnc.py`) sobre esos inputs.
  - `metadata.json`: fecha de ejecución, commit de Git activo, e inputs/outputs referenciados sin ambigüedad.
- Test de reproducibilidad: `tests/test_reproducibilidad.py::test_corrida_semana_01_es_reproducible` re-ejecuta el cálculo y compara, campo por campo, contra el `output/s1_cierre.json` versionado (excluyendo el timestamp, que por definición cambia en cada corrida). También `tests/test_integracion.py::test_pipeline_completo_semana_1` verifica que el mismo input produce el mismo resultado a nivel de los módulos individuales.

## D4 · Análisis económico

**Qué busca**: Consumo, tarifa, costo/run, proyección y justificación.

**Evidencia**:
- `docs/ANALISIS_ECONOMICO.md`: declara explícitamente costo de IA en runtime = 0 USD / 0 tokens, con justificación de diseño (sistema determinístico, ver DEC-001).
- Adicionalmente, el sistema realiza un análisis económico del **dominio del proyecto** (el costo real de la obra que controla): monto programado, monto ejecutado, acumulado y % de avance financiero, calculado en `src/calculador_inversion.py` y verificado en `tests/test_inversion.py`.
- Proyección y supuestos declarados explícitamente en `docs/ANALISIS_ECONOMICO.md` (precios unitarios constantes salvo actualización manual).

## D5 · Gobierno y riesgo

**Qué busca**: Permisos, fallas, respuesta, supervisión y responsable.

**Evidencia**:
- `docs/GOBERNANZA.md`: roles y responsables explícitos (supervisor de obra, jefe de obra, responsable de acción), tabla de manejo de fallas con referencia a código y tests, permisos de acceso a datos, y un riesgo conocido declarado sin mitigar (sin autenticación de usuarios).
- Validaciones activas en `src/validador.py` (incluida `validar_precios_faltantes`, agregada tras auditar que una afirmación de gobernanza no era todavía cierta — ver DEC-007), cada una con test asociado en `tests/test_validador.py` que demuestra que la falla se maneja explícitamente en lugar de fallar en silencio.

---

## Principio transversal aplicado

Siguiendo el mismo criterio que el proyecto grupal del agente evaluador: **la evidencia observable prevalece sobre declaraciones favorables**. Cada afirmación de este documento apunta a un archivo, función o test específico y verificable, no a una descripción genérica. Como muestra de esto: al preparar esta misma evidencia se auditó cada cita contra el código real, y se encontraron y corrigieron tres inconsistencias (DEC-005, DEC-006, DEC-007) en vez de dejarlas pasar.
