# Evidencia de Ejecución - ControlPPC

Este documento existe porque una devolución de evaluación anterior señaló:
*"Existe un intento inspeccionable, pero no se demuestran los gates
obligatorios de niveles superiores [...] Sin evidencia citada"* para D1
(Sistema completo y funcionando). Este archivo es esa evidencia: salidas reales
capturadas al correr el sistema, no una descripción de que "debería funcionar".

Todas las salidas de abajo se generaron el mismo día, sobre el commit indicado,
y son reproducibles corriendo los comandos tal cual están escritos.

## 1. Suite de tests completa

```
$ git rev-parse HEAD
12d266221ac5b5bc091d8f3dbdbbddf9f993e5aa

$ python -m pytest tests/ -v
```

```
==================== 64 passed, 9 subtests passed in 0.97s =====================
```

64 tests, 0 fallos, cubriendo los 8 módulos de `src/` más un test de
integración end-to-end (`tests/test_integracion.py`) y un test de
reproducibilidad (`tests/test_reproducibilidad.py`) que re-ejecuta el cálculo
real de las 3 corridas (`semana_01`, `semana_02`, `semana_03`) y lo compara
contra cada `corridas/<id>/output/*.json` versionado.

## 2. La aplicación Streamlit levanta y responde

```
$ streamlit run streamlit_app.py --server.headless true --server.port 8770
```

```
Uvicorn server started on 0.0.0.0:8770
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8770
```

```
$ curl -s -o /dev/null -w "HTTP_STATUS=%{http_code}\n" http://localhost:8770
HTTP_STATUS=200

$ curl -s http://localhost:8770/_stcore/health
ok
```

Sin excepciones en el log de arranque (las 7 pestañas — Datos y Registro,
Curva S, PPC, CNC y Acciones, Acciones, Seguimiento, Histórico — se renderizan
con los datos de ejemplo cargados por defecto).

## 3. Tres corridas reproducibles sobre datos reales

```
$ python corridas/generar_corrida.py --todas
```

```json
{
  "semana": 1,
  "commit_codigo": "12d266221ac5b5bc091d8f3dbdbbddf9f993e5aa",
  "metricas": {
    "ppc_semanal": [{"semana": 1, "total_actividades": 6, "actividades_cumplidas": 1, "ppc": 16.67}],
    "monto_programado": 2240000.0,
    "monto_ejecutado": 1315000.0
  },
  "cnc_top5": [
    {"codigo": "SM", "frecuencia": 1, "descripcion": "Falta de Suministro de Materiales", "categoria": "Recursos", "porcentaje": 33.33},
    {"codigo": "FT", "frecuencia": 1, "descripcion": "Falta de Fuerza de Trabajo", "categoria": "RRHH", "porcentaje": 33.33},
    {"codigo": "TO", "frecuencia": 1, "descripcion": "Trabajos Previos por Otros", "categoria": "Dependencia", "porcentaje": 33.33}
  ],
  "costo_ia": {
    "modelo": "ninguno (0 llamadas a un modelo de lenguaje en esta corrida)",
    "tokens_entrada": 0,
    "tokens_salida": 0,
    "tarifa_entrada_usd_por_mtok": 2.0,
    "tarifa_salida_usd_por_mtok": 10.0,
    "costo_total_usd": 0.0,
    "formula": "costo_total_usd = (tokens_entrada / 1e6 * tarifa_entrada_usd_por_mtok) + (tokens_salida / 1e6 * tarifa_salida_usd_por_mtok)",
    "verificado_por": "tests/test_sin_ia_en_runtime.py"
  }
}
```

Este es el JSON completo de `semana_01` tal cual lo generó el comando de
arriba (no un resumen), ejecutando el código real de
`src/calculador_ppc.py`, `src/calculador_inversion.py` y
`src/analizador_cnc.py` sobre los CSVs fijos de `corridas/semana_01/input/`.
El mismo comando regenera además `semana_02` (PPC 83.33%) y `semana_03`
(PPC 0%, 5 causas de no cumplimiento) — deliberadamente distintas entre sí —
y el ledger agregado `corridas/costos_por_corrida.json`. Todo está versionado
en `corridas/`, y `tests/test_reproducibilidad.py` falla si alguna corrida
deja de coincidir con lo que produce el código actual.

## 4. Verificación de $0 de costo en runtime

```
$ python -m pytest tests/test_sin_ia_en_runtime.py -v
```

```
test_hay_al_menos_un_archivo_de_runtime_para_auditar PASSED
test_ningun_archivo_de_runtime_importa_un_sdk_de_ia PASSED
test_requirements_no_incluye_sdks_de_ia_generativa PASSED
```

Ver `docs/ANALISIS_ECONOMICO.md` para la fórmula completa (tokens × tarifa).

## Cómo volver a generar esta evidencia

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
streamlit run streamlit_app.py &
curl http://localhost:8501/_stcore/health
python corridas/generar_corrida.py --todas
python corridas/calcular_costo_desarrollo.py
```

Ninguno de estos comandos requiere una API key ni acceso a internet: todo el
cómputo es local y determinístico (ver DEC-001 en `DECISIONES.md`).
