# 04_19 Caso de Estudio: Paradigmas Cientificos (Ejecutado)

## Contexto
- Fenomeno: transiciones de regimen intelectual (adopcion de paradigmas).
- Justificacion: proxies cuantificables via conteos bibliometricos.

## Datos
- Fase sintetica: serie controlada 1950-2023 con transicion logistic.
- Fase real: OpenAlex (share anual de publicaciones quantum vs classical), 1950-2023.
- Archivos de resultados: `02_Modelado_Simulacion/caso_paradigmas/report.md` y `02_Modelado_Simulacion/caso_paradigmas/metrics.json`.

## Modelado
- Modelo micro: ABM de difusion de ideas con acople macro.
- Modelo macro: ODE agregado de adopcion con forcing externo.
- Variable puente: share anual del paradigma emergente.

## Resultados
- Fase sintetica: `overall_pass = True`.
- Fase real: `overall_pass = True`.
- Convergencia en ambas fases bajo umbral `0.6 * sigma`.
- Symploke interna > externa, no-localidad funcional y persistencia verificadas.
- Emergencia: el modelo reducido degrada el error por encima del umbral.

## Criterio de aceptacion
- Cumplimiento C1-C5 y reglas de indicadores en ambas fases.

## Limites y criterio de paro
- Limites: proxy bibliometrico y agregacion anual.
- Criterio de paro: estabilidad de patrones y costo marginal > beneficio.
