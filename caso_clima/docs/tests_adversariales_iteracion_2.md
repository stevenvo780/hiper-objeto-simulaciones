# Tests Adversariales (Iteracion 2)

Este documento resume los tests adversariales reportados en la iteracion 2 del debate. Los resultados deben ser reproducibles con semillas fijas en `caso_clima/src/`.

## 1. Autonomia a Largo Plazo (zero-nudging, 1000 pasos)

Configuracion reportada:
- `assimilation_strength=0.0`
- `assimilation_series=None`
- 1000 iteraciones (ventanas de analisis 0-100, 200-400, 500-700, 800-1000)

Resultados reportados:
- Correlacion ABM-ODE creciente en el tiempo.
- Correlacion global ~0.8172.
- RMSE creciente por ventana, sin colapso de co-evolucion.

## 2. Causalidad Inversa (macro sostenido por micro)

Configuracion reportada:
- ODE forzada por la media del grid ABM (`forcing = grid_means_ABM`).

Resultado reportado:
- Correlacion ODE vs ABM ~0.9969.

## 3. Gradiente de Acoplamiento (no dictadura)

Configuracion reportada:
- Barrido de `forcing_scale` con resto de parametros fijos.

Resultados reportados:
- Respuesta no monotona del ABM (optimo alrededor de `forcing_scale=0.10`).
- Correlacion maxima ~0.567 y descenso para valores mayores, sugiriendo dinamica propia micro.

## 4. Hallazgo C5

Resultado reportado:
- En Clima, `macro_coupling` es nominalmente alto pero operativamente inactivo por baja varianza espacial del grid.
- El acoplamiento efectivo ocurre via `forcing_scale`.

## Reproducibilidad

Los tests fueron reportados con `seed=42/43` y pueden ejecutarse desde `caso_clima/src/` con los mismos parametros. Este documento no reemplaza los reportes automaticos; sirve como registro de debate.
