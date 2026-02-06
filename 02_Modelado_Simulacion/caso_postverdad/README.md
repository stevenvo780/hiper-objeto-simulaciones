# Caso Postverdad en Redes

Este caso evalua la dinamica de postverdad con dos modelos no isomorfos:
- Modelo micro (ABM de sesgo informacional) con interaccion local y acople macro.
- Modelo macro (ODE agregado) con dinamica de polarizacion/atencion.

Objetivo:
- Probar limites del marco 00/01 en fenomenos de difusion informacional.
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
- Fuente: Wikimedia Pageviews API.
- Serie: atencion mensual a terminos "fake news", "misinformation" y relacionados.
- Cache: `data/posttruth_wikipedia_monthly.csv`.
