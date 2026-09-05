# Metodología

Este documento explica los conceptos de control de avance de obra que implementa el sistema.

## PPC — Porcentaje de Plan Cumplido

Métrica del sistema Last Planner que mide qué porcentaje de las actividades comprometidas
para la semana se cumplieron efectivamente.

1. Para cada actividad programada (`semana`, `actividad`, `frente`), se compara el volumen
   ejecutado contra el volumen programado, obteniendo un `porcentaje_avance` (capado en 100%).
2. Una actividad se considera **cumplida** cuando su `porcentaje_avance` alcanza el 100%.
3. El **PPC semanal** es el porcentaje de actividades cumplidas sobre el total de actividades
   programadas esa semana:

   ```
   PPC = (actividades cumplidas / total de actividades programadas) x 100
   ```

Un PPC bajo indica problemas de planificación o ejecución y debería ir acompañado de un
análisis de causas de no cumplimiento (CNC).

## Inversión Programada vs. Ejecutada

- **Monto programado**: `volumen programado x precio unitario`, agregado por semana.
- **Monto ejecutado**: `volumen ejecutado x precio unitario`, agregado por semana.
- **Acumulado**: suma acumulada semana a semana (curva de inversión).
- **% Financiero acumulado**: `monto ejecutado acumulado / presupuesto total x 100`.

## Curva S

La curva S esperada representa el avance financiero acumulado planificado para cada semana
del proyecto. Se compara contra el avance financiero real:

```
Desviación = % acumulado real - % acumulado esperado
```

Clasificación (umbral configurable, por defecto ±2 puntos porcentuales):

- `Desviación > +2`: **Adelantado**
- `Desviación < -2`: **Atrasado**
- En caso contrario: **En Plan**

## Causas de No Cumplimiento (CNC)

Cada registro de ejecución diaria puede tener asociado un código de causa cuando no se
cumplió lo programado (por ejemplo `SM` = Falta de Suministro de Materiales). El sistema:

1. Cuenta la frecuencia de cada código en la semana.
2. Obtiene el **Top 5** de causas más frecuentes.
3. Calcula el porcentaje que cada causa representa sobre el total de incidencias.
4. Enriquece el resultado con la descripción y categoría del catálogo de causas.

Esto permite priorizar las acciones correctivas sobre los problemas más recurrentes.

## Acciones Correctivas

Por cada causa relevante se registra una acción con responsable, email y fecha de plazo.
Cada acción tiene un ciclo de vida:

```
pendiente -> en_curso -> completada
                       -> cancelada
```

En la semana siguiente se hace seguimiento: se marca si la acción se completó y si el
resultado fue positivo, negativo o parcial, cerrando el ciclo de mejora continua.
