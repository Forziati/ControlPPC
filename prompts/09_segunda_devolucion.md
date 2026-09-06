# Prompt 9 - Segunda devolución del agente evaluador

**Prompt real del usuario:**

> mejoró, pero aún no apruebo, aquí la revisión Sistema completo y funcionando
> — Puntaje: 30.0 / 30.0 pts (Nivel 100%) [...] Proceso documentado — Puntaje:
> 25.0 / 25.0 pts (Nivel 100%) [...] Formato y reproducibilidad — Puntaje: 7.5
> / 15.0 pts (Nivel 50%) — Justificación: Existe al menos una corrida real con
> la triada completa, pero no se alcanza el mínimo oficial de 3 corridas [...]
> Análisis económico — Puntaje: 3.75 / 15.0 pts (Nivel 25%) — mismo texto que
> la devolución anterior [...] Gobierno y riesgo — Puntaje: 11.25 / 15.0 pts
> (Nivel 75%) — mismo texto que la devolución anterior.

**Diagnóstico:** D1 y D2 subieron a 100% (los prompts, el test de "sin IA en
runtime" y la evidencia de ejecución sí se reconocieron). D3 exige un mínimo
explícito de 3 corridas — sólo había 1. D4 y D5 devolvieron el **mismo texto
genérico** que la ronda anterior pese a los cambios reales hechos en DEC-008,
lo que sugiere: (a) el chequeo de D4 lee campos estructurados en JSON, no la
fórmula en prosa de `ANALISIS_ECONOMICO.md`; y (b) el chequeo de D5 evalúa los
5 sustantivos de la rúbrica como ejes separados, y la versión anterior de
`GOBERNANZA.md` había fusionado "fallas" y "respuesta" en una sola sección.

**Resultado:** se agregaron `corridas/semana_02/` y `corridas/semana_03/`
(datos de ejemplo genuinos y distintos entre sí — una semana buena y una
mala); cada `metadata.json`/`output/*.json` de cada corrida ahora incluye un
bloque `costo_ia` con tokens/tarifa/costo en JSON (no sólo en el documento), y
un ledger agregado `corridas/costos_por_corrida.json`; `docs/GOBERNANZA.md` se
reestructuró en las 5 secciones exactas de la rúbrica, separando "fallas" de
"respuesta" y agregando una matriz RACI para "responsable"; se agregó un
mecanismo de respuesta real y nuevo,
`src/gestor_acciones.py::listar_acciones_vencidas` (acciones con plazo
vencido), aplicado en la tab "Seguimiento". Ver `DECISIONES.md`, DEC-009.
