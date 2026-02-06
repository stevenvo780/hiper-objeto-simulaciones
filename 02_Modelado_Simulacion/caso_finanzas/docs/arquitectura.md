# Arquitectura de Modelos (Capas)

## Conceptual
- Hiperobjeto: mercado financiero global con persistencia y acoplamientos internos.
- Mecanismo: interaccion local (contagio de expectativas) + forcing externo (macro).
- Delimitacion: indice amplio como proxy de dinamica agregada.

## Formal
- Estado micro por celda: sentimiento `S` y posicion `P`.
- Dinamica micro: contagio local + respuesta a forcing + ruido.
- Estado macro: precio agregado `X`.
- Dinamica macro: ODE de balance de presion compradora/vendedora.
- Variable puente: `X` acopla al micro y el micro alimenta `X`.

## Computacional
- Modelo micro: lattice 2D de agentes.
- Modelo macro: ODE discreta de balance agregado.
- Simulacion: pasos mensuales con semillas controladas.

## Validacion
- Convergencia ABM vs ODE sobre datos sinteticos y reales.
- Robustez ante perturbaciones de parametros.
- Replicacion con semillas alternativas.
- Validez interna/constructiva y reporte de incertidumbre.

Regla: si una capa falta, el modelo se invalida.

## Dialectica de modelado
- Representacion vs realidad: el modelo solo se acepta si valida externamente.
- Simplificacion vs complejidad: complejidad solo si mejora ajuste o explicacion.
- Determinismo vs estocasticidad: se usa ruido para reproducir volatilidad observada.
- Escalabilidad vs interpretabilidad: se prioriza interpretabilidad del modelo base.

## Apéndice: Hipótesis de Reflexividad (¿Por qué falla?)
El fracaso del modelo en finanzas no es un error de código, sino un hallazgo ontológico. Siguiendo a George Soros, el mercado es un sistema **reflexivo**: los agentes no solo observan la realidad, sino que sus expectativas cambian la realidad misma (loop de retroalimentación positiva). 
- **Inconsistencia de la ODE:** Una Ecuación Diferencial asume un atractor físico o una inercia estructural estable.
- **Aliasing Temporal:** Los cambios en el SPY ocurren a una frecuencia mayor que nuestra resolución mensual, rompiendo la coherencia de la Capa Macro.
