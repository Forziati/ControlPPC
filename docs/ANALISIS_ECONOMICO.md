# Análisis Económico - ControlPPC

## Costo de IA en producción (runtime)

| Concepto | Valor |
|---|---|
| Tokens generativos consumidos por corrida | **0** |
| Costo de API generativa por corrida | **0 USD** |
| Modelo de IA utilizado en runtime | **Ninguno** |

**Justificación**: Ver `DECISIONES.md` (DEC-001). El sistema calcula PPC, curva S, inversión y CNC con lógica determinística (pandas). No existe ninguna llamada a un modelo de lenguaje durante el uso normal de la aplicación. Esto es una decisión de diseño explícita, no una omisión: se prioriza reproducibilidad total (mismo input → mismo output, sin variabilidad de generación) y costo operativo nulo para el equipo de obra que use la herramienta semana a semana.

## Costo de IA en desarrollo

El desarrollo del código (`src/`, `tests/`, `streamlit_app.py`, documentación) se realizó con asistencia de Claude Code. Ese uso:

- Ocurrió **una sola vez** durante la construcción del sistema, no se repite en cada corrida operativa.
- No está incluido en el costo de "uso" del sistema, de la misma manera que el costo de un IDE o de un compilador no se contabiliza como costo por corrida de un programa ya compilado.

## Análisis económico del **dominio** (lo que la herramienta mide)

Aunque no hay costo de IA que reportar, el sistema sí realiza un análisis económico sustantivo del proyecto de construcción que controla:

| Métrica | Qué mide | Dónde se calcula |
|---|---|---|
| Monto programado | Σ (volumen planificado × precio unitario) por semana | `src/calculador_inversion.py::calcular_monto_programado` |
| Monto ejecutado | Σ (volumen ejecutado × precio unitario) por semana | `src/calculador_inversion.py::calcular_monto_ejecutado` |
| Acumulado financiero | Suma corrida semana a semana | `src/calculador_inversion.py::calcular_acumulado` |
| % de avance financiero | Ejecutado acumulado / total programado | `src/calculador_inversion.py::calcular_porcentaje_financiero` |
| Desviación vs. curva S | Real acumulado − esperado según cronograma | `src/comparador_curva_s.py` |

Ejemplo real (corrida `corridas/semana_01/`, reproducible con `python corridas/generar_corrida.py semana_01` y verificada en `tests/test_reproducibilidad.py`):

```
Monto programado (Semana 1): $2.240.000
Monto ejecutado (Semana 1):  $1.315.000
```

Este es el análisis económico central del proyecto: no es sobre el costo de la IA, sino sobre el costo real de la obra que la herramienta ayuda a controlar.

## Proyección y supuestos

- El monto programado total del proyecto es la suma de `volumen × precio_unitario` de todas las filas de `cronograma_semanal.csv`.
- Se asume que los precios unitarios (`precios_unitarios.csv`) permanecen constantes durante el horizonte del proyecto; si cambian (por inflación o renegociación), deben actualizarse manualmente y quedará reflejado en la próxima corrida.
- No se proyecta automáticamente el costo final estimado (EAC); esa es una mejora futura declarada, no una funcionalidad actual.
