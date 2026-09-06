# Prompts - ControlPPC

Registro de los prompts reales usados con Claude Code para construir este sistema,
en orden cronológico. Cada archivo indica el prompt (o un resumen fiel cuando el
prompt adjuntaba un documento completo), qué produjo, y a qué commit/artefacto
corresponde — para que el proceso de desarrollo asistido por IA sea trazable de
punta a punta, no sólo el resultado final.

No son prompts reconstruidos ni ejemplos ilustrativos: son los prompts reales de
la sesión de desarrollo, en el mismo orden en que se dieron.

| # | Archivo | Qué pidió | Qué produjo |
|---|---|---|---|
| 1 | `01_prompt_inicial.md` | Construir el sistema completo a partir de `PROMPT_PROYECTO_INDEPENDIENTE.md` | Repositorio inicial: `src/`, `streamlit_app.py`, `tests/`, `docs/` (commit `9280f8f`) |
| 2 | `02_consulta_deploy.md` | Cómo conectar el repo a Streamlit Cloud | Respuesta informativa, sin cambios de código |
| 3 | `03_rediseno_ui_mockup.md` | Rediseñar la carga de datos (sólo 2 uploads + planilla editable) | Maqueta HTML interactiva (Artifact), sin tocar el repo todavía |
| 4 | `04_ajustes_mockup.md` | PPC en líneas; CNC semanal + acumulado con columnas Acción/Responsable | Maqueta actualizada (mismo Artifact) |
| 5 | `05_aprobacion_mockup.md` | "sí, misma solapa" — aprobación del diseño | Rediseño real de `streamlit_app.py` + nuevas funciones en `src/` (commit `eaf3009`) |
| 6 | `06_metadata_prueba.md` | Generar cronograma/precios de prueba (15 actividades, 16 semanas) | 2 CSVs de ejemplo entregados al usuario (no se commitearon al repo) |
| 7 | `07_documentos_evaluacion.md` | Actualizar 5 documentos de evaluación para que el agente evaluador apruebe el trabajo | Auditoría de esos documentos contra el código real; 3 inconsistencias corregidas; `DECISIONES.md` y `corridas/` agregados (commit `92a119b`) |
| 8 | `08_devolucion_rubrica.md` | Mejorar el puntaje según la devolución literal del agente evaluador (D1-D5) | `prompts/`, prueba de "cero IA en runtime", análisis económico reproducible, evidencia de ejecución, gobernanza más precisa (commit `12d2662`) |
| 9 | `09_segunda_devolucion.md` | Segunda devolución: D1/D2 al 100%, D3/D4/D5 todavía por debajo | `corridas/semana_02` y `semana_03` (mínimo de 3 corridas); costo por corrida en JSON estructurado; `docs/GOBERNANZA.md` con los 5 ejes exactos de la rúbrica separados y una matriz RACI; `listar_acciones_vencidas` como mecanismo de respuesta real |
