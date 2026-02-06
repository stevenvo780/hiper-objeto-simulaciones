# 04_22 Caso de Estudio: Conciencia Fenomenica (Ejecutado)

## Contexto
- Fenomeno: experiencia subjetiva aproximada por proxies reportados.
- Justificacion: el hard problem exige proxies observables para validacion.

## Datos
- Fase sintetica: serie controlada 2011-2023 con transicion suave.
- Fase real: OWID Cantril ladder (World), 2011-2023.
- Archivos de resultados: `02_Modelado_Simulacion/caso_conciencia/report.md` y `02_Modelado_Simulacion/caso_conciencia/metrics.json`.

## Modelado
- Modelo micro: ABM de diffusion de estados afectivos con acople macro.
- Modelo macro: ODE agregado de satisfaccion reportada.
- Variable puente: promedio anual de satisfaccion.

## Resultados
- Fase sintetica: `overall_pass = True`.
- Fase real: `overall_pass = True`.
- Convergencia en ambas fases bajo umbral `0.6 * sigma`.
- Symploke interna > externa, no-localidad funcional y persistencia verificadas.
- Emergencia: el modelo reducido degrada el error por encima del umbral.

## Criterio de aceptacion
- Cumplimiento C1-C5 y reglas de indicadores en ambas fases.

## Limites y criterio de paro
- Limites: proxy subjetivo y agregacion anual.
- Criterio de paro: estabilidad de patrones y costo marginal > beneficio.
