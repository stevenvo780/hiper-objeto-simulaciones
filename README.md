# SimulacionClimatica: Modelado Híbrido de Sistemas Complejos

Repositorio de investigación y simulación para la validación de la **Hipótesis H1 (Eficacia Causal de los Hiperobjetos)**. Utiliza un motor de simulación de doble escala (ABM + ODE) para estudiar dinámicas en 16 dominios críticos.

## Estado de la Simulación (05/02/2026)
Todos los modelos han completado sus fases de validación y cumplen con los criterios **C1-C5**.

### Casos de Estudio Destacados
1.  **Clima Regional:** Dinámica de temperatura y humedad en CONUS.
2.  **Finanzas Globales:** Modelado disipativo del índice SPY.
3.  **Movilidad Urbana:** Flujos de pasajeros en el Metro de NY (MTA).
4.  **Cascadas DeFi (Caso Límite):** Simulación de colapsos sistémicos en redes financieras descentralizadas utilizando **acoplamiento bidireccional**.

## Arquitectura
El proyecto se organiza en capas estrictas:
- **Conceptual:** Axiomas y supuestos del dominio.
- **Formal:** Modelado matemático (Ecuaciones Diferenciales y Reglas de Agente).
- **Computacional:** Implementación en Python.
- **Validación:** Contraste contra datos reales en tiempo real.

Para más detalles, consulte `02_Modelado_Simulacion/index.md`.