# Indicadores, Metricas y Reglas (Postverdad en Redes)

Basado en `00_03_Tablas_Correspondencia.md` y `01_02_Indicadores_Metricas.md`.

## Symploke (cohesion)
- Metrica: correlacion media entre agentes vecinos vs correlacion con forcing externo.
- Regla: cohesion interna > externa.

## Emergencia fuerte
- Metrica: degradacion al remover acople macro.
- Regla: el modelo reducido incrementa el error por encima de umbral.

## No-localidad funcional
- Metrica: dominancia de fuentes (max share de influencia).
- Regla: ninguna fuente supera el umbral definido por caso.

## Persistencia estructural
- Metrica: estabilidad de regimen (varianza de ventanas largas).
- Regla: estabilidad bajo perturbaciones razonables.

## Causalidad descendente debil
- Metrica: cambios en distribuciones micro al variar condiciones macro.
- Regla: diferencias micro significativas bajo cambios macro controlados.
