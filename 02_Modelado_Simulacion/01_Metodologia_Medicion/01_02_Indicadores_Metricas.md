# 01_02 Indicadores y Métricas: Fundamentación Matemática del EDI y CR

Este documento establece la base científica de los umbrales utilizados, eliminando cualquier ambigüedad operativa.

## 1. El Índice de Degradación de Emergencia (EDI)
El umbral del **30% (0.30)** no es arbitrario; se deriva del **Principio de Esclavizamiento de Herman Haken (Synergetics)**.
*   **Fundamento:** Para que un "Parámetro de Orden" macroscópico sea ontológicamente relevante, debe ser capaz de "esclavizar" (restringir) la dinámica micro reduciendo su entropía en al menos un tercio del rango total observado.
*   **Fórmula:** $EDI = (RMSE_{reduced} - RMSE_{hybrid}) / RMSE_{reduced}$.
*   **Validación:** Un EDI < 0.30 indica que el sistema es "reducido por defecto" (la capa macro es cosmética).

## 2. El Ratio de Cohesión de Symploke (CR)
El umbral de **2.0** se basa en la **Relación Señal-Ruido (SNR)** aplicada a grafos de interacción.
*   **Fundamento:** Según la teoría de la información de Shannon, para que un mensaje (el sistema) sea legible sobre el ruido (el entorno), la densidad de información interna debe duplicar la interferencia externa.
*   **Fórmula:** $CR = \frac{\sum |Interacciones_{internas}|}{\sum |Interacciones_{externas}|}$.
*   **Validación:** Un CR < 2.0 indica que el sistema se ha disuelto en su entorno (Entropía Máxima).
