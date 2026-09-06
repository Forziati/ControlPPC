# Análisis Económico - ControlPPC

## 0. Costo por corrida — ledger machine-readable

Cada corrida en `corridas/<id>/` trae, en su propio `metadata.json` (y en la
raíz de su `output/*.json`), un bloque `costo_ia` con las variables ya
resueltas — no hay que ir a buscar la fórmula a este documento para calcular
el costo de una corrida puntual:

```json
"costo_ia": {
  "modelo": "ninguno (0 llamadas a un modelo de lenguaje en esta corrida)",
  "tokens_entrada": 0,
  "tokens_salida": 0,
  "tarifa_entrada_usd_por_mtok": 2.0,
  "tarifa_salida_usd_por_mtok": 10.0,
  "costo_entrada_usd": 0.0,
  "costo_salida_usd": 0.0,
  "costo_total_usd": 0.0,
  "formula": "costo_total_usd = (tokens_entrada / 1e6 * tarifa_entrada_usd_por_mtok) + (tokens_salida / 1e6 * tarifa_salida_usd_por_mtok)",
  "verificado_por": "tests/test_sin_ia_en_runtime.py"
}
```

`corridas/costos_por_corrida.json` agrega este bloque de las 3 corridas
(`semana_01`, `semana_02`, `semana_03`) en un único ledger, regenerado por
`python corridas/generar_corrida.py --todas` — nunca tipeado a mano.

## 1. Costo de IA en producción (runtime) — fórmula reproducible

| Variable | Valor | Cómo se verifica |
|---|---|---|
| Tokens consumidos por corrida | **0** | `tests/test_sin_ia_en_runtime.py`: ningún archivo de `src/` ni `streamlit_app.py` importa un SDK de IA generativa; `requirements.txt` no incluye ninguno. Además, `tests/test_reproducibilidad.py::test_costo_ia_de_cada_corrida_es_cero_y_reproducible` verifica que las 3 corridas reales dan `tokens=0` y `costo_total_usd=0.0` |
| Tarifa del modelo en runtime | **N/A (no se invoca ningún modelo)**; se referencia igual la tarifa real de Sonnet 5 ($2.00/$10.00 por 1M tokens) en el bloque `costo_ia` de cada corrida, para que la fórmula sea evaluable con una tarifa real, no un placeholder | `corridas/generar_corrida.py::calcular_costo_ia_corrida` |
| **Costo por corrida** | **`0 tokens × tarifa = $0.00 USD`**, igual en las 3 corridas | Reproducible corriendo `python corridas/generar_corrida.py --todas` o `python -m pytest tests/test_sin_ia_en_runtime.py tests/test_reproducibilidad.py -v` |

Esto no es una afirmación cualitativa: es una ecuación con sus dos variables
verificadas por un test automatizado que falla si alguna vez se agrega una
llamada a un modelo de lenguaje en el camino de cálculo (`src/calculador_ppc.py`,
`src/calculador_inversion.py`, `src/comparador_curva_s.py`,
`src/analizador_cnc.py`, `src/gestor_acciones.py`, `src/persistencia.py`,
`src/validador.py`) o en `streamlit_app.py`. Justificación de diseño: ver
`DECISIONES.md` (DEC-001) — se prioriza reproducibilidad total (mismo input →
mismo output) y costo operativo nulo para el equipo de obra que use la
herramienta semana a semana.

## 2. Costo de IA en desarrollo — fórmula reproducible

El desarrollo se hizo con Claude Code (modelo **Claude Sonnet 5**, tarifa
pública: $2.00 / 1M tokens de entrada, $10.00 / 1M tokens de salida). A
diferencia del runtime, acá sí hay tokens consumidos — por la sesión de
desarrollo, no por el sistema construido — y por eso corresponde reportarlos y
calcular el costo, no descartarlos.

**Medición**: este entorno no expone un contador de tokens en vivo de la
conversación, así que en vez de inventar una cifra precisa, `corridas/calcular_costo_desarrollo.py`
mide algo real y reproducible por cualquiera que clone el repo: el tamaño en
bytes de cada diff commiteado (`git show <sha>`), y estima tokens de salida con
una heurística documentada (~4 bytes/token). Es una **cota inferior**, no el
costo total de la sesión: no cuenta tokens de entrada/contexto (que en un
agente de código suelen ser el componente más grande) ni el texto conversacional
que no terminó plasmado en el repo.

```
tokens_salida_estimados = bytes_del_diff / 4
costo_estimado_usd = tokens_salida_estimados / 1,000,000 × $10.00
```

Corrida real (`python corridas/calcular_costo_desarrollo.py`, reproducible en
cualquier checkout de este repositorio):

| Commit | Fecha | Asunto | Bytes del diff | Tokens de salida (estimados) | Costo estimado |
|---|---|---|---|---|---|
| `9280f8f` | 2026-09-05 | Implementar sistema de control de avance de obra | 70.642 | 17.660 | $0.1766 |
| `eaf3009` | 2026-09-05 | Rediseñar carga de datos y agregar vistas de PPC y CNC | 49.869 | 12.467 | $0.1247 |
| `92a119b` | 2026-09-06 | Agregar evidencia de gobernanza y corridas reproducibles | 40.939 | 10.235 | $0.1023 |
| `12d2662` | 2026-09-06 | Responder a la devolución de evaluación (prompts/, D4, D5) | 61.228 | 15.307 | $0.1531 |
| **Total** | | | **222.678** | **55.669** | **$0.5567** |

(Esta tabla queda un commit "atrasada" respecto del HEAD real después de cada
commit posterior, por la misma razón que `commit_codigo` en `corridas/`: no es
posible que un commit se referencie a sí mismo antes de existir. Recalculable
en cualquier momento con `python corridas/calcular_costo_desarrollo.py`.)

**Costo real y completo**: la cifra autoritativa (con tokens de entrada
incluidos) está en el dashboard de uso de la cuenta de Anthropic o en el
comando `/cost` de la sesión de Claude Code — no en este documento. Lo que
este documento garantiza es que la cota inferior de arriba es recalculable por
cualquiera, con un comando, contra el historial real de commits — no una cifra
tipeada a mano.

## 3. Análisis económico del **dominio** (lo que la herramienta mide)

Además de lo anterior, el sistema realiza un análisis económico sustantivo del
proyecto de construcción que controla:

| Métrica | Qué mide | Dónde se calcula |
|---|---|---|
| Monto programado | Σ (volumen planificado × precio unitario) por semana | `src/calculador_inversion.py::calcular_monto_programado` |
| Monto ejecutado | Σ (volumen ejecutado × precio unitario) por semana | `src/calculador_inversion.py::calcular_monto_ejecutado` |
| Acumulado financiero | Suma corrida semana a semana | `src/calculador_inversion.py::calcular_acumulado` |
| % de avance financiero | Ejecutado acumulado / total programado | `src/calculador_inversion.py::calcular_porcentaje_financiero` |
| Desviación vs. curva S | Real acumulado − esperado según cronograma | `src/comparador_curva_s.py` |

Ejemplo real, con las 3 corridas disponibles (`corridas/semana_01/`,
`corridas/semana_02/`, `corridas/semana_03/`, reproducibles con
`python corridas/generar_corrida.py --todas` y verificadas en
`tests/test_reproducibilidad.py`), a propósito con resultados bien distintos
entre sí para mostrar el rango real de lo que la herramienta detecta:

| Corrida | Programado | Ejecutado | PPC | Estado |
|---|---|---|---|---|
| `semana_01` | $2.240.000 | $1.315.000 | 16.67% | Semana floja, recién arrancando |
| `semana_02` | $2.240.000 | $2.195.000 | 83.33% | Semana buena, casi todo cumplido |
| `semana_03` | $2.240.000 | $1.075.000 | 0.00% | Semana mala, 5 causas de no cumplimiento distintas |

## 4. Proyección y supuestos

- El monto programado total del proyecto es la suma de `volumen × precio_unitario` de todas las filas de `cronograma_semanal.csv`.
- Se asume que los precios unitarios (`precios_unitarios.csv`) permanecen constantes durante el horizonte del proyecto; si cambian (por inflación o renegociación), deben actualizarse manualmente y quedará reflejado en la próxima corrida.
- No se proyecta automáticamente el costo final estimado (EAC); esa es una mejora futura declarada, no una funcionalidad actual.
- La estimación de costo de desarrollo (sección 2) es una cota inferior declarada como tal; no reemplaza el reporte de uso real de la cuenta de Anthropic.
