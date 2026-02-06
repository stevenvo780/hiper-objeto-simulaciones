# 04_23 Caso de Estudio: Postverdad en Redes (Ejecutado)

## Contexto
- Fenomeno: difusion informacional con sesgo y atencion selectiva.
- Justificacion: proxies de atencion capturan intensidad del discurso.

## Datos
- Fase sintetica: serie controlada 2010-2024 con transicion logistic.
- Fase real: Wikimedia Pageviews (terminos fake news, misinformation, disinformation, post-truth, conspiracy theory), 2015-2024.
- Archivos de resultados: `02_Modelado_Simulacion/caso_postverdad/report.md` y `02_Modelado_Simulacion/caso_postverdad/metrics.json`.

## Modelado
- Modelo micro: ABM de sesgo informacional con acople macro.
- Modelo macro: ODE agregado de atencion/polarizacion.
- Variable puente: atencion mensual (log views).

## Resultados
- Fase sintetica: `overall_pass = True`.
- Fase real: `overall_pass = True`.
- Convergencia en ambas fases bajo umbral `0.6 * sigma`.
- Symploke interna > externa, no-localidad funcional y persistencia verificadas.
- Emergencia: el modelo reducido degrada el error por encima del umbral.

## Criterio de aceptacion
- Cumplimiento C1-C5 y reglas de indicadores en ambas fases.

## Limites y criterio de paro
- Limites: proxy de atencion y sesgo, no verdad factual.
- Criterio de paro: estabilidad de patrones y costo marginal > beneficio.
