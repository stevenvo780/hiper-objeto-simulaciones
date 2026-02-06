# 04_20 Caso de Estudio: Estetica y Estilos (Ejecutado)

## Contexto
- Fenomeno: transiciones esteticas y cambio de estilos.
- Justificacion: proxy bibliometrico curatorial via clasificacion de obras.

## Datos
- Fase sintetica: serie controlada 1929-2023 con transicion logistic.
- Fase real: MoMA Collection (share anual de Painting vs Sculpture), 1929-2023.
- Archivos de resultados: `02_Modelado_Simulacion/caso_estetica/report.md` y `02_Modelado_Simulacion/caso_estetica/metrics.json`.

## Modelado
- Modelo micro: ABM de preferencias estilisticas con acople macro.
- Modelo macro: ODE agregado de adopcion con forcing externo.
- Variable puente: share anual del estilo (painting).

## Resultados
- Fase sintetica: `overall_pass = True`.
- Fase real: `overall_pass = True`.
- Convergencia en ambas fases bajo umbral `0.6 * sigma`.
- Symploke interna > externa, no-localidad funcional y persistencia verificadas.
- Emergencia: el modelo reducido degrada el error por encima del umbral.

## Criterio de aceptacion
- Cumplimiento C1-C5 y reglas de indicadores en ambas fases.

## Limites y criterio de paro
- Limites: proxy curatorial y agregacion anual.
- Criterio de paro: estabilidad de patrones y costo marginal > beneficio.
