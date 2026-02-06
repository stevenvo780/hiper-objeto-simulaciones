# 00_02 Glosario Maestro: Ontología Operativa

Este glosario no define palabras; define **herramientas de pensamiento**. Cada término aquí tiene una contraparte directa en el código Python de la tesis.

## A - C

### Aliasing Temporal (Temporal Aliasing)
*   **Definición:** Error ontológico que ocurre cuando la frecuencia de cambio de un Hiperobjeto es superior a la frecuencia de muestreo del modelo.
*   **En la Tesis:** La causa técnica del fallo en el Caso Finanzas. El mercado cambia en milisegundos; nuestra ODE es mensual. El objeto "se escapa" entre los fotogramas.
*   **Código:** `rmse_ode` elevado en validación real.

### Cohesión, Ratio de (CR)
*   **Definición:** Medida termodinámica que establece si un sistema tiene "frontera". Es la relación entre la fuerza de las interacciones internas y las externas (Ruido).
*   **Fórmula:** $CR = \frac{\Sigma|Internal|}{\Sigma|External|}$.
*   **Umbral:** Si $CR < 2.0$, el sistema no es un objeto, es un agregado o un entorno. (Ref: Bueno, Symploke).

## E - H

### Eficacia Causal (Causal Efficacy)
*   **Definición:** Capacidad de una entidad macroscópica para alterar el estado de sus componentes microscópicos. No es una correlación estadística, es una fuerza física descendente (*top-down causation*).
*   **Prueba:** Se verifica mediante el test de **Nudging**. Si forzamos la variable macro en la simulación y los agentes micro se reordenan, existe eficacia causal.

### Emergencia Degradada, Índice de (EDI)
*   **Definición:** Métrica original de esta tesis basada en la **Sinergética de Haken**. Cuantifica cuánta "libertad" pierden los agentes al ser sometidos a un orden macro.
*   **Umbral Crítico (0.30):** Si el modelo híbrido no reduce el error del modelo simple en un 30%, la "emergencia" es una ilusión o una coincidencia.

### Hiperobjeto (Hyperobject)
*   **Definición Operativa:** Entidad caracterizada por **Viscosidad** (adherencia al observador) y **No-Localidad** (distribución masiva).
*   **Traducción al Código:** Un objeto `HybridModel` que pasa los criterios C1-C5. Si no compila o no converge, ontológicamente *no existe* para nosotros.

## N - R

### Nudging (Asimilación)
*   **Definición:** Técnica de "empujón" matemático inspirada en los filtros de Kalman. Es la "goma elástica" que conecta la Ecuación Diferencial (lo que debería pasar) con los Agentes (lo que está pasando).
*   **Función:** Evita que el modelo teórico derive hacia la fantasía, manteniéndolo anclado a los datos empíricos (Realidad).

### Reflexividad (Soros)
*   **Definición:** Propiedad de los sistemas sociales donde la predicción del modelo altera el sistema modelado.
*   **Consecuencia:** Invalida las Ecuaciones Diferenciales estáticas. Un Hiperobjeto reflexivo (como el Mercado) es un blanco móvil que destruye la herramienta que intenta medirlo.

### Retirada (Withdrawal)
*   **Definición (OOO):** La cualidad de los objetos reales de ser irreducibles a sus datos. El mapa no es el territorio.
*   **En la Tesis:** El "residuo" de error que nunca podemos eliminar ($1 - R^2$). Aceptamos este error como prueba de que la realidad excede nuestra simulación.

## S - Z

### Symploke
*   **Definición (Bueno):** Estructura de la realidad donde "no todo está conectado con todo".
*   **Uso:** Nos permite aislar el "Caso Clima" del "Caso Finanzas" sin caer en el holismo místico. Modelamos islas de orden en un mar de caos.