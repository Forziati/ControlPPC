# Control de Avance de Obra - Sistema de PPC, Inversión y Acciones

Sistema interactivo para gestionar el avance semanal de proyectos de construcción.

## Características

- **PPC (Porcentaje de Plan Cumplido)**: Calcula el avance semanal por actividad y el PPC consolidado.
- **Inversión Acumulada**: Sigue el monto programado vs. ejecutado, semanal y acumulado.
- **Curva S**: Compara el avance financiero real con el plan esperado de construcción.
- **Causas de No Cumplimiento (CNC)**: Identifica y clasifica el top 5 de problemas de la semana.
- **Acciones Correctivas**: Registra acciones con responsables, plazos y hace seguimiento semana a semana.
- **Histórico**: Series temporales de PPC, avance financiero y desviaciones a lo largo del proyecto.

## Estructura del Proyecto

```
control-avance-obra/
├── streamlit_app.py        # Aplicación principal (Streamlit)
├── src/                     # Módulos de lógica de negocio
├── data/                    # CSVs de entrada y data/historico/ con cierres en JSON
├── tests/                   # Tests unitarios y de integración
└── docs/                    # Documentación (metodología y guía de uso)
```

## Instalación Local

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución de Tests

```bash
python -m pytest tests/ -v
```

## Ejecución de la App

```bash
streamlit run streamlit_app.py
```

Abrir [http://localhost:8501](http://localhost:8501)

## Deploy en Streamlit Cloud

1. Sube este repositorio a GitHub.
2. Entra a [streamlit.io/cloud](https://streamlit.io/cloud) e inicia sesión con GitHub.
3. Elige el repositorio, la rama y `streamlit_app.py` como script principal.
4. Deploy automático. La URL tendrá la forma `https://usuario-control-avance-obra.streamlit.app`.

## Datos de Entrada

Sólo se suben dos archivos (o se usan los de ejemplo incluidos en `data/`) desde la
pestaña "Datos y Registro":

- `cronograma_semanal.csv` (programa de obra — de acá sale la curva S esperada, calculada
  automáticamente)
- `precios_unitarios.csv`

El resto se carga **directo en la app**, sin subir CSVs:

- El avance diario se registra en una planilla editable estilo Excel (día, actividad,
  frente, volumen ejecutado, causa CNC).
- El catálogo de causas de no cumplimiento (CNC) es fijo dentro del sistema
  (`data/causas_incumplimiento.csv`, no se sube ni se edita).

## Flujo de Uso

1. **Datos y Registro**: sube el programa de obra y los precios (o usa los de ejemplo),
   cargá el avance de la semana en la planilla y presioná "Guardar y calcular semana".
2. **Curva S**: compara el avance real acumulado contra el plan esperado.
3. **PPC**: revisa el PPC de la semana (gráfico de líneas) y el detalle por actividad.
4. **CNC y Acciones**: frecuencia de causas semanal y acumulada, con la acción correctiva
   y el responsable vigente para cada una.
5. **Acciones**: registra nuevas acciones correctivas para las causas detectadas.
6. **Seguimiento**: en la semana siguiente, revisa y cierra las acciones pendientes.
7. **Histórico**: analiza tendencias a lo largo de las semanas procesadas.

## Documentación

- [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md): explicación de los conceptos (PPC, curva S, CNC).
- [`docs/GUIA_USO.md`](docs/GUIA_USO.md): cómo usar la app paso a paso.
- [`docs/GOBERNANZA.md`](docs/GOBERNANZA.md): roles, supervisión humana y manejo de fallas.
- [`docs/ANALISIS_ECONOMICO.md`](docs/ANALISIS_ECONOMICO.md): costo de IA (nulo en runtime) y análisis económico del proyecto.
- [`DECISIONES.md`](DECISIONES.md): decisiones de diseño y proceso, incluyendo fallas detectadas y corregidas.
- [`corridas/`](corridas/): corridas reproducibles (input → output → metadata) generadas con `corridas/generar_corrida.py`.
- [`prompts/`](prompts/): historial real de los prompts usados para construir este sistema, en orden.
- [`EVIDENCIA_EJECUCION.md`](EVIDENCIA_EJECUCION.md): salidas reales capturadas de tests, la app y las corridas (no descripciones).

## Licencia

MIT

## Autor

Franco
