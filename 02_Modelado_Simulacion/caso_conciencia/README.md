# Caso Conciencia Fenomenica (Hard Problem)

Este caso explora un proxy observable de experiencia subjetiva con dos modelos no isomorfos:
- Modelo micro (ABM de diffusion de estados afectivos) con interaccion local y acople macro.
- Modelo macro (ODE agregado) con dinamica de satisfaccion reportada.

Objetivo:
- Probar limites del marco 00/01 en dominios fenomenicos no observables directamente.
- Validar C1-C5 con fase sintetica y fase real (proxy).

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
- Fuente: Our World in Data (Cantril ladder, promedio anual).
- Serie: promedio mundial (o fallback USA si no hay "World").
- Cache: `data/owid_happiness.csv`.
