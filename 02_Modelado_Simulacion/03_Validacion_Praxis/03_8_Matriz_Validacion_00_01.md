# 03_8 Matriz de Validación Técnica: Verificación de Hiperobjetos

Esta matriz certifica la validez técnica de los casos. Se distingue entre **Validación Empírica** (datos duros de >20 años) y **Validación Prospectiva** (basada en proxies o series cortas).

| Caso de Estudio | Tipo de Validación | EDI | CR | Nivel de Evidencia (LoE) | Estado Final |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Clima Regional** | Empírica (Meteostat) | 0.51 | 2.5 | ★★★★★ | **VALIDADO** |
| **Contaminación** | Empírica (CAMS) | 0.52 | 2.8 | ★★★★☆ | **VALIDADO** |
| **Energía** | Empírica (OPSD) | 0.38 | 2.4 | ★★★★☆ | **VALIDADO** |
| **Epidemiología** | Empírica (OWID) | 0.55 | 3.2 | ★★★★☆ | **VALIDADO** |
| **Finanzas (SPY)** | Empírica (Yahoo) | 0.05 | 1.1 | ★★★★★ | **RECHAZADO** |
| **Wikipedia** | Empírica (Wikimedia) | 0.41 | 2.6 | ★★★☆☆ | **VALIDADO** |
| **Postverdad** | Prospectiva (Proxies) | 0.34 | 2.2 | ★★☆☆☆ | **VALIDADO** |
| **Justicia** | Teórica (Invarianza) | 0.35 | 2.3 | ★★☆☆☆ | **TEÓRICO** |
| **Bienestar** | Teórica (Encuestas) | 0.42 | 2.2 | ★★☆☆☆ | **TEÓRICO** |
| **Estética** | Teórica (Estilos) | 0.33 | 2.1 | ★☆☆☆☆ | **TEÓRICO** |
| **Paradigmas** | Teórica (Citas) | 0.31 | 2.1 | ★☆☆☆☆ | **TEÓRICO** |
| **Movilidad** | Piloto (Local) | 0.32 | 2.1 | ★★☆☆☆ | **PROTOTIPO (Falla C1)** |

## Notas de Blindaje contra la "Pseudo-Ciencia"
1. **LoE 4-5:** Casos con datasets históricos masivos. Son el núcleo de la tesis.
2. **LoE 1-2:** Casos "Teóricos" o "Prospectivos". Se incluyen para demostrar la **extensibilidad del marco**, pero no pretenden ser verdades ontológicas definitivas.
3. **Casos Prototipo:** Sistemas como Movilidad Urbana que, pese a tener un EDI > 0.30, fallan en la **Convergencia C1** en series temporales largas, indicando una inestabilidad del atractor macro.
4. **Umbrales (EDI > 0.30):** Basados en el Principio de Esclavizamiento de Haken (redundancia estructural mínima).