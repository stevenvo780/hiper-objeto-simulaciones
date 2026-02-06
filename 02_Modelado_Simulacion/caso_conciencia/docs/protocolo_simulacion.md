# Protocolo de Simulacion (Conciencia Fenomenica)

1. Cargar datos reales (OWID Cantril ladder) y generar fase sintetica.
2. Normalizar observaciones (z-score).
3. Construir forcing desde tendencia y cambio temporal.
4. Calibrar parametros con fase de entrenamiento.
5. Evaluar fase de validacion con nudging.
6. Ejecutar modelo reducido para criterio de emergencia.
7. Reportar C1-C5 e indicadores.

## Criterio de paro
- Cambios marginales en error < 1% en dos iteraciones de calibracion.
