# 04_14 Plan de Caso: Surgimiento de Paradigmas Cientificos

## Objetivo
- Evaluar si el marco 00–01 explica cambios de paradigma sin forzar ajuste.

## Fuente de datos reales
- OpenAlex (conteos anuales por concepto, via `concepts` + `works?filter=concepts.id` + `group_by=publication_year`).

## Metodologia
- Modelos no isomorfos: ABM (difusion de ideas) + modelo macro (transiciones de regimen).
- Variable puente: intensidad de adopcion / dominancia de paradigma.
- Criterios C1–C5 y reglas de indicadores.

## Fases y splits
- Fase real: 1950-2023, split 1990.

## Entregables
- Reporte reproducible y metricas.
- Validacion en 03 y caso ejecutado en 04.
