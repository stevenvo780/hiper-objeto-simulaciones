# Reproducibilidad (Justicia y Normatividad)

## Versionado
- Repositorio principal con commit hash registrado en `metrics.json`.

## Entorno
- Python 3.10+
- Dependencias: `numpy`, `pandas`, `requests`.

## Sensibilidad
- Se reportan min/max de medias bajo perturbaciones de parametros.

## Datos
- Fuente World Bank WGI, cache local en `data/worldbank_rule_of_law_usa.csv`.
- Para estabilidad, se agrega por anio y se guarda la serie resultante.
