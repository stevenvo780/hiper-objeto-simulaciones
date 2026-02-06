# Caso Falsacion: Observabilidad Insuficiente

Este caso simula una falla por ausencia de proxies confiables o cobertura insuficiente.

## Datos reales
- Fuente: OWID Cantril ladder (World/USA).
- Se induce missingness para bajar cobertura.
- Cache: `data/owid_happiness_sparse.csv`.

## Resultado esperado
- Falla de C1 por cobertura < 0.85 y/o C5 por sesgos.
