# Validacion C1-C5 (Conciencia Fenomenica)

## C1 Convergencia
- Fase sintetica: ABM y ODE deben ajustar la serie sintetica con error bajo umbral.
- Fase real: ABM y ODE deben ajustar la serie real con error bajo umbral.
- Datos reales: OWID Cantril ladder (proxy de bienestar subjetivo).
- Umbral definido por caso: `0.6 * sigma` del conjunto de validacion.

## Verificacion (escenario controlado)
- La fase sintetica funciona como escenario simple con resultado conocido.
- Si falla, el modelo se invalida antes de pasar a datos reales.

## C2 Robustez
- Parametros se perturban en rango +/-10%.
- Resultados deben permanecer estables.

## C3 Replicacion
- Dos semillas/condiciones iniciales distintas.
- Se espera misma conclusion cualitativa (persistencia y no-localidad).

## C4 Validez
- Interna: reglas causales coherentes.
- Externa: respuesta detectable a forcing alterno.
- Constructiva: correspondencia concepto-indicador documentada.
 - Regla operativa: cambio detectable en media/varianza o pico ante forcing alterno.

## C5 Incertidumbre explicita
- Sensibilidad reportada en `outputs/metrics.json`.
- Limites y supuestos declarados en `outputs/report.md`.

## Emergencia fuerte (criterio operativo)
- Se compara el modelo completo vs reducido (sin acople macro y sin nudging).
- La degradacion debe superar `0.2 * sigma` del conjunto de validacion.
