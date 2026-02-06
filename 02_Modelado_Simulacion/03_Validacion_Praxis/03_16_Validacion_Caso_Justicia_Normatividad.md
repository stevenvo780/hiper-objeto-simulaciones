# 03_16 Validacion Caso Justicia y Normatividad (Ejecucion)

## Objetivo
- Validar el caso justicia con dos fases: sintetica (verificacion interna) y real (evaluacion final).

## Indicadores y umbrales
- C1 Convergencia: RMSE por debajo de `0.6 * sigma` y correlacion >= 0.7.
- C2 Robustez: estabilidad ante perturbaciones +/-10%.
- C3 Replicacion: estabilidad bajo semillas distintas.
- C4 Validez: respuesta detectable a forcing alterno.
- C5 Incertidumbre: sensibilidad acotada.

## Datos y fases
- Fase sintetica: 1996-01-01 a 2023-12-31, split 2010-01-01.
- Fase real: 1996-01-01 a 2023-12-31, split 2010-01-01 (WGI RL.EST, USA).

## Resultados resumidos
- Fase sintetica: `overall_pass = True`.
- Fase real: `overall_pass = True`.
- Errores y umbrales documentados en `02_Modelado_Simulacion/caso_justicia/metrics.json`.

## Auditoria y trazabilidad
- Reporte completo en `02_Modelado_Simulacion/caso_justicia/report.md`.
- Metricas completas y parametros en `02_Modelado_Simulacion/caso_justicia/metrics.json`.
- Semillas y configuracion quedan registradas en el reporte.

## Criterio de cierre
- La validacion queda aceptada si ambas fases pasan C1-C5 y los indicadores.
