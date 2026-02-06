# Reproducibilidad (Conciencia Fenomenica)

## Versionado
- Repositorio principal con commit hash registrado en `metrics.json`.

## Entorno
- Python 3.10+
- Dependencias: `numpy`, `pandas`, `requests`.

## Sensibilidad
- Se reportan min/max de medias bajo perturbaciones de parametros.

## Datos
- Fuente OWID (Cantril ladder), cache local en `data/owid_happiness.csv`.
- Para estabilidad, se agrega por anio y se guarda la serie resultante.
