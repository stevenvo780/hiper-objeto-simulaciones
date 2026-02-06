# 03_01 Análisis de Resultados: Evidencia Empírica (LoE 4-5)

En este documento se analizan los casos donde el marco ABM+ODE demostró una convergencia robusta sobre datasets históricos masivos.

## 1. El Caso Clima (El Hiperobjeto Canónico)
*   **Dataset:** Meteostat / CAMS (>30 años).
*   **Resultado:** EDI 0.51 | CR 2.5.
*   **Análisis:** El éxito del clima valida que los sistemas con alta inercia térmica poseen una estructura macro (Ecuación Energética) que "esclaviza" de forma detectable a las fluctuaciones locales (Micro-clima). Es la prueba de que el Hiperobjeto tiene eficacia causal.

## 2. El Caso Energía (Infraestructura Crítica)
*   **Dataset:** OPSD (Open Power System Data).
*   **Resultado:** EDI 0.38 | CR 2.4.
*   **Análisis:** La red eléctrica se comporta como un hiperobjeto debido a la necesidad de equilibrio carga-generación. La capa macro no es opcional; si los agentes no se ajustan a la ODE global, el sistema colapsa (Blackout).

## 3. El Caso Epidemiología
*   **Dataset:** OWID (Our World in Data).
*   **Resultado:** EDI 0.55 | CR 3.2.
*   **Análisis:** Los virus no tienen fronteras locales. La dinámica de contagio (Micro) solo tiene sentido bajo el parámetro de orden de la tasa de reproducción global (Macro).
