# 02_6 Glosario de Terminología Matemática y Algorítmica

Este documento define el formalismo matemático utilizado en los motores de simulación del proyecto.

---

## 1. Métricas de Validación Ontológica

### EDI (Emergency Degradation Index)
*   **Fórmula:**  = \frac{RMSE_{reduced} - RMSE_{hybrid}}{RMSE_{reduced}}$
*   **Definición:** Mide la ganancia de precisión al incluir la capa macro. 
*   **Umbral:** $> 0.30$ para validar emergencia fuerte.

### CR (Cohesion Ratio - Symploke)
*   **Fórmula:**  = \frac{\sum |Interacciones_{internas}|}{\sum |Interacciones_{externas}|}$
*   **Definición:** Ratio entre la conectividad de los agentes del sistema y el ruido del entorno.
*   **Umbral:** $\ge 2.0$ para validar frontera sistémica.

---

## 2. Operaciones del Motor Híbrido

### Nudging (Asimilación de Datos)
*   **Operación:** {t+1} = X_t + \lambda(Target - \bar{X})$
*   **Definición:** Fuerza de atracción (goma elástica) que sincroniza el nivel micro con la tendencia macro. $\lambda$ representa la "fuerza de asimilación".

### Difusión Térmica (Lattice Diffusion)
*   **Operación:** {i,j} = T_{i,j} + D \cdot (\bar{T}_{neighbors} - T_{i,j})$
*   **Definición:** Algoritmo de suavizado espacial basado en la Vecindad de Moore (nodos adyacentes). $ es el coeficiente de conductividad.

---

## 3. Terminología por Caso de Estudio

### A. Dominio Físico (Clima/Contaminación)
*   **Balance Energético (ODE):** $\frac{dT}{dt} = \alpha(Forcing - \beta T)$. Representa la inercia térmica planetaria.
*   **Ruido Blanco ($\eta$):** Inyección de estocasticidad para simular turbulencia atmosférica.

### B. Dominio Social (Finanzas/Postverdad)
*   **Reflexividad ($\mathcal{R}$):** Bucle de retroalimentación donde la salida del modelo modifica los parámetros de entrada en +1$. 
*   **Entropy ($):** Medida de desorden en la señal que impide la sincronización del Nudging.

### C. Dominio de Redes (Wikipedia/Epidemiología)
*   **Autopoiesis:** Capacidad del sistema de mantener su topología a pesar del flujo de agentes.
*   **Threshold de Fase:** El punto crítico donde una infección local se convierte en una pandemia macro.
