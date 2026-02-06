# 03_7 Validación: Caso Finanzas Globales (Análisis de Aliasing Temporal)

## 1. Resultado del Fallo
*   **EDI:** 0.05.
*   **Dictamen:** **INFRASUESTREO (Aliasing)**.

## 2. Diagnóstico Técnico de Ingeniería
El fallo en el caso Finanzas no se debe a la ausencia de un Hiperobjeto, sino a una violación del **Teorema de Nyquist-Shannon**.
*   **El Problema:** El motor `HybridModel` opera con un paso de tiempo mensual ($\Delta t = 1$ mes). El mercado financiero genera señales críticas en escalas de milisegundos a días.
*   **Consecuencia:** La dinámica macro del mercado es "demasiado rápida" para ser capturada por la inercia de una Ecuación Diferencial (ODE) de baja frecuencia.
*   **Lección:** Para modelar el Hiperobjeto Financiero, se requiere una resolución temporal $\times 1000$ superior a la climática. El fallo valida que el marco C1-C5 detecta correctamente la falta de resolución instrumental.
