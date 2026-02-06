# Caso Sistemas de Justicia y Normatividad

Este caso evalua dinamicas institucionales con dos modelos no isomorfos:
- Modelo micro (ABM de cumplimiento normativo) con interaccion local y acople macro.
- Modelo macro (ODE agregado) con dinamica de legitimidad institucional.

Objetivo:
- Probar limites del marco 00/01 en sistemas normativos.
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
- Fuente: World Bank WGI (Rule of Law, RL.EST) para USA.
- Serie: indice anual de rule of law.
- Cache: `data/worldbank_rule_of_law_usa.csv`.
