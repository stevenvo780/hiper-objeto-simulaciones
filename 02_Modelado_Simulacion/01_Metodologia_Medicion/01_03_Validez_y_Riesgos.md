# 01_03 Validez, Riesgos y Límites del Modelo

En este documento delimitamos dónde termina la ciencia y dónde empieza la especulación, blindando la tesis contra el exceso de confianza.

## 1. Riesgos de Reificación
El mayor peligro metodológico es confundir un **ajuste estadístico** con una **entidad real**. 
*   **Salvaguarda:** Establecemos que un EDI alto (>0.90) es sospechoso de sobreajuste (*overfitting*). La realidad suele ser ruidosa; un modelo "perfecto" suele ser un modelo falso o tautológico.

## 2. El Problema del Aliasing Temporal
Declaramos explícitamente que nuestro marco ABM+ODE tiene una limitación de **resolución**. 
*   **Frontera:** Si la dinámica interna del objeto es más rápida que el paso de tiempo de la simulación (ej. mercados financieros de alta frecuencia), el modelo generará una "ilusión de orden" o fallará en la convergencia. El Caso Finanzas es nuestra prueba de control para este riesgo.

## 3. Evaluación de la Calidad de los Datos
Categorizamos los resultados según la fuente:
*   **Nivel 5 (Duro):** Datos físicos medidos por satélites o sensores (Clima, Energía).
*   **Nivel 3 (Semi-Duro):** Registros de actividad digital (Wikipedia, LinkedIn).
*   **Nivel 1 (Blando):** Encuestas o proxies subjetivos (Bienestar, Justicia). La tesis admite que los niveles 1-2 son solo **Prospectivos**.

## 4. Conclusión Epistémica
El método no busca probar la "verdad absoluta", sino la **Eficacia Causal**. Un hiperobjeto es real en la medida en que su modelo macro es necesario para reducir la incertidumbre del sistema micro por encima de un umbral no trivial (30%).
