# Caso Estetica y Evolucion de Estilos Artistico

Este caso evalua transiciones estilisticas con dos modelos no isomorfos:
- Modelo micro (ABM de difusion de preferencias) con interaccion local y acople macro.
- Modelo macro (ODE agregado) con dinamica de adopcion y forcing externo.

Objetivo:
- Probar limites del marco 00/01 en dominios simbolicos.
- Validar C1-C5 con fase sintetica y fase real.

## Estructura
- `docs/arquitectura.md`
- `docs/protocolo_simulacion.md`
- `docs/indicadores_metricas.md`
- `docs/validacion_c1_c5.md`
- `docs/reproducibilidad.md`
- `src/` implementacion
- `outputs/` reportes de corrida

## Como correr

```bash
pip install -r requirements.txt
python3 src/validate.py
```

Genera:
- `outputs/metrics.json`
- `outputs/report.md`

## Datos reales
- Fuente: MoMA Collection (Artworks.csv).
- Serie: share anual de "Painting" frente a "Sculpture".
- Cache: `data/moma_artworks.csv`.
