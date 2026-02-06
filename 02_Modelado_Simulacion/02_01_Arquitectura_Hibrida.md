# 02_01 Arquitectura Híbrida: El Motor de los Hiperobjetos

Para captar la realidad de un hiperobjeto, la arquitectura de software debe ser capaz de procesar dos escalas temporales y espaciales simultáneamente.

## 1. Nivel Micro: Sistemas Adaptativos Complejos (ABM)
El nivel micro se modela mediante **Modelado Basado en Agentes (ABM)**. 
*   **Regla:** Los agentes poseen autonomía local pero su entorno está condicionado por el campo macroscópico.
*   **Referencia:** Holland (1995).

## 2. Nivel Macro: Dinámica de Sistemas (ODE)
El nivel macro se define mediante **Ecuaciones Diferenciales Ordinarias (ODE)** que capturan la inercia estructural del sistema.
*   **Función:** Representa el "Parámetro de Orden" de Haken que esclaviza a los agentes.

## 3. Implementación (Clase Maestra en Python)
```python
class HybridModel:
    def __init__(self, agents, ode_system, nudging=0.4):
        self.agents = agents
        self.ode = ode_system
        self.nudging = nudging

    def step(self, forcing):
        # El macro define el atractor
        target_state = self.ode.solve(forcing)
        
        # El micro evoluciona localmente
        for a in self.agents:
            a.update()
            # Nudging: Causalidad descendente (Top-down)
            a.state += self.nudging * (target_state - a.state)
```
Esta arquitectura garantiza que el hiperobjeto sea una entidad **detectable y falsable**.
