# Guía de Uso

## 1. Instalación y ejecución local

```bash
git clone <url-del-repositorio>
cd control-avance-obra
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

La app abre en [http://localhost:8501](http://localhost:8501).

## 2. Pestaña "Datos y Registro"

**A · Documentos base del proyecto** — se suben una sola vez (o al re-programar la obra):

- Programa de obra / cronograma (`cronograma_semanal.csv`)
- Precios unitarios (`precios_unitarios.csv`)

A partir de estos dos archivos el sistema calcula automáticamente la **curva S esperada**:
ya no hace falta subirla como CSV aparte. Marcá **"Usar datos de ejemplo"** para trabajar
con los incluidos en `data/`.

**B · Registro diario de avance** — en vez de subir un CSV de ejecución, la semana se carga
directo en una planilla editable (estilo Excel) dentro de la app: día, actividad, frente,
volumen ejecutado y causa de no cumplimiento (CNC, opcional) por fila. Podés agregar o
borrar filas libremente. Al presionar **"Guardar y calcular semana"**:

- se valida la planilla (consistencia contra el cronograma, volúmenes no negativos, etc.),
- se guarda en `data/historico/s{semana}_ejecucion.json`,
- y se recalculan PPC, curva S real y frecuencia de CNC con el histórico completo del proyecto.

**C · Catálogo de causas (CNC)** — es fijo dentro del sistema (no se sube ni se edita).

## 3. Pestaña "Curva S"

Métricas de avance real acumulado, esperado y desviación de la semana actual, gráfico de
líneas real vs. esperado, clasificación (Adelantado / En Plan / Atrasado) y tabla
comparativa por semana.

## 4. Pestaña "PPC"

Métricas de PPC de la semana con semáforo (🟢 ≥85%, 🟡 ≥70%, 🔴 <70%), actividades
cumplidas y tendencia; gráfico de **líneas** del PPC por semana con las líneas de
referencia de meta (85%) y mínimo aceptable (70%); y el detalle de avance por actividad
de la semana actual.

## 5. Pestaña "CNC y Acciones"

Frecuencia de causas de no cumplimiento en dos niveles:

- **CNC de la semana**: frecuencia registrada en el corte actual.
- **CNC acumulado**: frecuencia total del proyecto a la fecha.

Cada tabla incluye, además del código/descripción/categoría/frecuencia/%, las columnas
**Acción correctiva** y **Responsable** con la acción vigente más reciente registrada para
esa causa en la pestaña "Acciones" (o "Sin acción registrada" si todavía no hay ninguna).

## 6. Pestaña "Acciones"

- **Registrar Acción**: elige la causa CNC, describe la acción, indica responsable, email
  y fecha de plazo, y presiona "Registrar Acción".
- **Tabla de Acciones**: lista todas las acciones de la semana. Selecciona una acción y un
  nuevo estado (`pendiente`, `en_curso`, `completada`, `cancelada`) y presiona
  "Actualizar Estado".

## 7. Pestaña "Seguimiento"

Al iniciar una nueva semana:

1. Elige la semana anterior a revisar.
2. Para cada acción pendiente o en curso, marca si se completó, si el resultado fue
   positivo/parcial/negativo y agrega observaciones.
3. Presiona "Guardar Seguimiento" para actualizar el histórico de esa semana.

## 8. Pestaña "Histórico"

Selecciona un rango de semanas ya procesadas para ver:

- PPC por semana (línea)
- % financiero acumulado (área)
- Desviación de la curva S por semana (barras)
- Top CNC de cada semana (tablas)
- Descarga de un reporte resumen en CSV.

## 9. Deploy en Streamlit Cloud

1. Sube el repositorio a GitHub.
2. Entra a [streamlit.io/cloud](https://streamlit.io/cloud) y conecta tu cuenta de GitHub.
3. Selecciona el repositorio, la rama (`main`) y `streamlit_app.py` como archivo principal.
4. Streamlit Cloud instala `requirements.txt` y despliega la app automáticamente.
