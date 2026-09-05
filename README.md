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

La app incluye datos de ejemplo en `data/` y permite cargar los propios desde la pestaña "Cargar Datos":

- `cronograma_semanal.csv`
- `precios_unitarios.csv`
- `ejecucion_diaria.csv`
- `causas_incumplimiento.csv`
- `curva_s_esperada.csv`

## Flujo de Uso

1. **Cargar Datos**: sube los 5 CSV (o usa los de ejemplo) y procesa la semana actual.
2. **Tablero**: revisa avance financiero, PPC y top 5 CNC de la semana.
3. **Curva S**: compara el avance real contra el plan esperado.
4. **Acciones**: registra acciones correctivas para las causas detectadas.
5. **Seguimiento**: en la semana siguiente, revisa y cierra las acciones pendientes.
6. **Histórico**: analiza tendencias a lo largo de las semanas procesadas.

## Documentación

- [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md): explicación de los conceptos (PPC, curva S, CNC).
- [`docs/GUIA_USO.md`](docs/GUIA_USO.md): cómo usar la app paso a paso.

## Licencia

MIT

## Autor

Franco
