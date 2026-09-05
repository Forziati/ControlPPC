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

## 2. Pestaña "Cargar Datos"

- Marca **"Usar datos de ejemplo"** para trabajar con los CSV incluidos en `data/`, o sube
  tus propios archivos (deben respetar las mismas columnas):
  - `cronograma_semanal.csv`
  - `precios_unitarios.csv`
  - `ejecucion_diaria.csv`
  - `causas_incumplimiento.csv`
  - `curva_s_esperada.csv`
- Selecciona la **semana actual** en la barra lateral.
- Presiona **"Procesar Datos"**. El sistema valida los archivos, calcula todas las métricas
  y guarda un cierre en `data/historico/s{semana}_cierre.json`.
- Si hay errores de validación (columnas faltantes, valores negativos, actividades no
  programadas, etc.), se listan en pantalla y no se guarda nada hasta corregirlos.

## 3. Pestaña "Tablero"

Muestra tres columnas para la semana seleccionada:

- **Avance Financiero**: métrica de inversión ejecutada vs. programada, barra de progreso
  y gráfico de barras + línea acumulada.
- **PPC Semanal**: métrica de PPC con semáforo (🟢 ≥85%, 🟡 ≥70%, 🔴 <70%) y gráfico de
  barras coloreado por semana.
- **Top 5 CNC**: gráfico de barras horizontales y tabla con frecuencia y % de cada causa.

## 4. Pestaña "Curva S"

Gráfico de líneas con el avance real vs. el esperado, la desviación de la semana actual
con su clasificación (Adelantado / En Plan / Atrasado) y una tabla comparativa por semana.

## 5. Pestaña "Acciones"

- **Registrar Acción**: elige la causa CNC, describe la acción, indica responsable, email
  y fecha de plazo, y presiona "Registrar Acción".
- **Tabla de Acciones**: lista todas las acciones de la semana. Selecciona una acción y un
  nuevo estado (`pendiente`, `en_curso`, `completada`, `cancelada`) y presiona
  "Actualizar Estado".

## 6. Pestaña "Seguimiento"

Al iniciar una nueva semana:

1. Elige la semana anterior a revisar.
2. Para cada acción pendiente o en curso, marca si se completó, si el resultado fue
   positivo/parcial/negativo y agrega observaciones.
3. Presiona "Guardar Seguimiento" para actualizar el histórico de esa semana.

## 7. Pestaña "Histórico"

Selecciona un rango de semanas ya procesadas para ver:

- PPC por semana (línea)
- % financiero acumulado (área)
- Desviación de la curva S por semana (barras)
- Top CNC de cada semana (tablas)
- Descarga de un reporte resumen en CSV.

## 8. Deploy en Streamlit Cloud

1. Sube el repositorio a GitHub.
2. Entra a [streamlit.io/cloud](https://streamlit.io/cloud) y conecta tu cuenta de GitHub.
3. Selecciona el repositorio, la rama (`main`) y `streamlit_app.py` como archivo principal.
4. Streamlit Cloud instala `requirements.txt` y despliega la app automáticamente.
