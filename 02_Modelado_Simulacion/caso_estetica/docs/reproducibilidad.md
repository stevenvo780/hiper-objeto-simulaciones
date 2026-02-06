# Reproducibilidad (Estetica y Estilos)

## Versionado
- Repositorio principal con commit hash registrado en `metrics.json`.

## Entorno
- Python 3.10+
- Dependencias: `numpy`, `pandas`, `requests`.

## Sensibilidad
- Se reportan min/max de medias bajo perturbaciones de parametros.

## Datos
- Fuente MoMA Collection, cache local en `data/moma_artworks.csv`.
- Para estabilidad, se agrega por anio y se guarda la serie resultante.
