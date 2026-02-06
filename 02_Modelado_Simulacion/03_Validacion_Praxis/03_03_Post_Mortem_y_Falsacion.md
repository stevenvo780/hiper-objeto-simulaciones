# 03_03 Post-Mortem: El Valor del Fracaso y la Falsación

En esta tesis, un fallo del modelo es tan valioso como un éxito. El fracaso delimita la frontera del Hiperobjeto.

## 1. El Fracaso de las Finanzas (SPY)
*   **Diagnóstico:** EDI 0.05 | CR 1.1.
*   **Causa Ontológica (Reflexividad):** A diferencia del clima, el mercado financiero es un sistema donde el conocimiento del modelo altera el objeto modelado. La "inercia" en finanzas es psicológica y altamente volátil.
*   **Causa Técnica (Aliasing):** La frecuencia de los eventos financieros es órdenes de magnitud superior a la resolución de nuestra simulación. El sistema no es un Hiperobjeto estable, sino un campo de batalla de alta frecuencia.

## 2. El Test de Falsación (Control de Calidad)
Sometimos a los casos exitosos a tres pruebas de estrés para descartar falsos positivos:
1.  **Exogeneidad Total:** ¿Sigue funcionando el modelo si eliminamos la retroalimentación macro? (Respuesta: No, el error sube >30%, validando el EDI).
2.  **Ruido Blanco:** ¿Puede el modelo validar una serie aleatoria? (Respuesta: No, el CR cae a <1.0, validando el CR).
3.  **Invisibilidad de Agentes:** ¿Basta con la ODE para predecir? (Respuesta: No, se pierde la varianza local necesaria para la resiliencia).

## 3. Conclusión de la Praxis
La validación C1-C5 no es un sello de goma; es un filtro. El hecho de que las Finanzas hayan sido **Rechazadas** le da credibilidad científica a la validación del Clima y la Energía.
