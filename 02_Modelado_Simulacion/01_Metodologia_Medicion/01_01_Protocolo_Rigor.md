# 01_01 Protocolo de Rigor y Pipeline de Ejecución

Este documento define el estándar de "Prueba de Existencia" para los Hiperobjetos. No basta con observar una tendencia; el sistema debe sobrevivir a un proceso de auditoría computacional en tres etapas.

## 1. El Pipeline de Validación (C1-C5)
El rigor de la tesis se basa en la superposición de cinco criterios de demarcación:
1.  **C1 (Convergencia):** El modelo ABM (Bottom-up) y el ODE (Top-down) deben converger en un atractor común sobre datos reales.
2.  **C2 (Robustez):** El sistema debe mantener su estabilidad estructural ante perturbaciones del +/-10% en sus parámetros nucleares.
3.  **C3 (Determinismo Aleatorio):** Uso de semillas fijas (`Random Seeds`) para garantizar que cualquier auditor externo obtenga exactamente los mismos decimales de EDI y CR.
4.  **C4 (Linter de Realidad):** Validación cruzada con leyes físicas o lógicas del dominio (ej. la temperatura no puede subir sin energía).
5.  **C5 (Reporte de Fallos):** Publicación obligatoria de la sensibilidad y los límites de confianza.

## 2. Auditoría de Replicabilidad
Siguiendo los estándares de la ciencia abierta, cada experimento cuenta con un archivo `validate.py` autoejecutable. La métrica del éxito no es la opinión del autor, sino el paso de los tests unitarios de emergencia (EDI > 0.30).

## 3. La Capa de Abstracción de Software
Implementamos una arquitectura híbrida donde el macro-estado actúa como una "restricción de frontera" (boundary condition) para los agentes micro. Este acoplamiento se formaliza mediante **Asimilación de Datos**, permitiendo que el modelo "aprenda" de la realidad sin perder su autonomía dinámica.
