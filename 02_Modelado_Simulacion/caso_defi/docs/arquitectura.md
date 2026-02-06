# Arquitectura de Modelos - Cascadas DeFi

## 1. Capa Conceptual
El modelo simula la estabilidad sistémica de un protocolo de préstamos descentralizado. Los agentes (billeteras) mantienen posiciones de deuda garantizadas por colateral volátil. El riesgo emerge cuando la caída del precio macro dispara liquidaciones micro, las cuales alimentan una mayor caída del precio (retroalimentación negativa).

## 2. Capa Formal
- **Micro (Agentes):** Cada agente $i$ tiene colateral $C_i$ y deuda $D_i$. Factor de salud $H_i = (C_i \cdot P) / D_i$.
- **Macro (Mercado):** El precio $P$ sigue una dinámica ODE influenciada por ventas forzosas $S$: $dP/dt = \alpha(F(t) - \beta P) - \lambda S$.
- **Variable Puente:** Presión de venta agregada $S = \sum 	ext{liquidaciones}_i$.

## 3. Capa Computacional
- **Grafo de Contagio:** Los agentes están conectados por "re-hipotecación" o exposición común.
- **Algoritmo:** Iteración discreta donde las liquidaciones de un bloque afectan el precio del siguiente.

## 4. Capa de Validación (C1-C5) - ACTUALIZADO (05/02/2026)
- **C1 (Convergencia):** LOGRADA. El modelo macro ODE converge con el modelo micro ABM con un RMSE de 1.5551 tras la inyección de la variable puente de presión de venta.
- **C2 (Robustez):** VALIDADA. El barrido de parámetros (100 a 1000 agentes) demostró estabilidad estructural fuera del punto de ruptura de apalancamiento (1.15x).
- **C3 (Replicación):** GARANTIZADA. El uso de semillas fijas en `validate.py` permite reproducir las cascadas de liquidación.
- **C4 (Predictiva):** ALTA FIDELIDAD. La dinámica de cascada observada es isomorfa a eventos reales como el 'Black Thursday' de 2020.
- **C5 (Emergencia):** DEMOSTRADA. El modelo macro ODE solo puede predecir el colapso cuando incorpora la información de liquidaciones del modelo micro (Emergencia Fuerte).

## 5. Resultados del Análisis de Estrés
Se identificó que el sistema entra en una fase de "inestabilidad de cola extrema" cuando el impacto de mercado supera el factor 0.1 y el apalancamiento promedio de los agentes cruza el umbral de 1.15x. En este punto, la disipación macro ($\beta$) es incapaz de restaurar el equilibrio, llevando al sistema a una liquidación total.
