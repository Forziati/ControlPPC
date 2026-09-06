# Prompt 7 - Documentos de evaluación

**Prompt real del usuario** (adjuntando `GOBERNANZA.md`, `MAPEO_RUBRICA_D1_D5.md`,
`metadata.json`, `s1_cierre.json` y `ANALISIS_ECONOMICO.md`):

> necesito actualizar estos documentos para que el agente evaluador apruebe el
> trabajo

**Resultado:** en vez de incorporar los 5 documentos tal cual, se auditó cada
afirmación contra el código real antes de aceptarlos, porque varios se
presentaban como "evidencia real de ejecutar el código". Se encontraron y
corrigieron tres inconsistencias reales (documentadas como DEC-005, DEC-006 y
DEC-007 en `DECISIONES.md`):

1. `docs/GUIA_USO.md` indicaba deployar sobre una rama `main` que nunca existió
   en este repositorio.
2. No existían `DECISIONES.md` ni una carpeta `corridas/` con evidencia
   reproducible, pese a que los documentos las citaban.
3. `GOBERNANZA.md` afirmaba que un precio unitario faltante para una actividad
   ejecutada no se calculaba silenciosamente en $0 — pero el código sí lo hacía.

Se agregó `src/validador.py::validar_precios_faltantes` (con tests), se
construyó `corridas/semana_01/` ejecutando de verdad
`corridas/generar_corrida.py` sobre el código de `src/`, y se escribió
`DECISIONES.md` con 7 decisiones reales. Se corrigió además un `.gitignore` que
ocultaba silenciosamente `corridas/*/output/` del control de versiones.
Commit `92a119b`.
