# 04_21 Caso de Estudio: Justicia y Normatividad (Ejecutado)

## Contexto
- Fenomeno: estabilidad institucional y cumplimiento normativo.
- Justificacion: proxy cuantificable via Rule of Law.

## Datos
- Fase sintetica: serie controlada 1996-2023 con transicion suave.
- Fase real: World Bank WGI RL.EST (USA), 1996-2023.
- Archivos de resultados: `02_Modelado_Simulacion/caso_justicia/report.md` y `02_Modelado_Simulacion/caso_justicia/metrics.json`.

## Modelado
- Modelo micro: ABM de cumplimiento normativo con acople macro.
- Modelo macro: ODE agregado de legitimidad institucional.
- Variable puente: indice anual de rule of law.

## Resultados
- Fase sintetica: `overall_pass = True`.
- Fase real: `overall_pass = True`.
- Convergencia en ambas fases bajo umbral `0.6 * sigma`.
- Symploke interna > externa, no-localidad funcional y persistencia verificadas.
- Emergencia: el modelo reducido degrada el error por encima del umbral.

## Criterio de aceptacion
- Cumplimiento C1-C5 y reglas de indicadores en ambas fases.

## Limites y criterio de paro
- Limites: proxy institucional y agregacion anual.
- Criterio de paro: estabilidad de patrones y costo marginal > beneficio.
