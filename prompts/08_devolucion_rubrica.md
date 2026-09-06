# Prompt 8 - Devolución literal del agente evaluador

**Prompt real del usuario:**

> la devolución fue esta, necesito mejorar la nota
>
> Sistema completo y funcionando — Puntaje: 7.5 / 30.0 pts (Nivel 25%)
> Justificación: Existe un intento inspeccionable, pero no se demuestran los
> gates obligatorios de niveles superiores.
> Faltante para el siguiente nivel: Completar la implementación ejecutable y
> sus corridas respaldadas.
> Evidencia citada: Sin evidencia citada
>
> Proceso documentado — Puntaje: 18.75 / 25.0 pts (Nivel 75%)
> Evidencia citada: DECISIONES.md con 7 decisiones sustantivas
>
> Formato y reproducibilidad — Puntaje: 0.0 / 15.0 pts (Nivel 0%)
> Justificación: Faltan carpetas obligatorias (prompts/ o corridas/) en el
> repositorio.
>
> Análisis económico — Puntaje: 3.75 / 15.0 pts (Nivel 25%)
> Faltante para el siguiente nivel: Vincular tokens consumidos por corrida y
> tarifa del modelo para calcular el costo por corrida.
>
> Gobierno y riesgo — Puntaje: 11.25 / 15.0 pts (Nivel 75%)
> Faltante para el siguiente nivel: Precisar los mecanismos operativos de
> permisos, respuesta, revisión y responsabilidad.

**Diagnóstico:** D3 decía "faltan prompts/ o corridas/" pese a que `corridas/`
ya estaba en el repo (confirmado con `git ls-tree` contra el remoto) — lo que
realmente faltaba era `prompts/`, que no existía. D1 está probablemente atado al
mismo gate (cita "corridas respaldadas"). D4 pedía la aritmética explícita
tokens × tarifa, no sólo la afirmación de "0 tokens". D5 pedía mecanismos
operativos concretos, no sólo los ejes nombrados.

**Resultado:** se agregó esta carpeta `prompts/`; un test que verifica
programáticamente que no hay ningún import de SDK de IA en `src/` ni en
`streamlit_app.py` (para que el "0 tokens en runtime" sea reproducible, no sólo
declarado); una fórmula tokens×tarifa explícita en `docs/ANALISIS_ECONOMICO.md`
para el runtime del sistema y para el costo real de desarrollo con Claude Code
(tarifa de Sonnet 5); un documento de evidencia de ejecución con salidas reales
capturadas (`pytest`, `streamlit`, `corridas/generar_corrida.py`); y mecanismos
operativos concretos por eje en `docs/GOBERNANZA.md`. Ver `DECISIONES.md`,
DEC-008.
