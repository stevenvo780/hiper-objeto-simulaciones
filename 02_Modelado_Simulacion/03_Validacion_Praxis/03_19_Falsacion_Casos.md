# 03_19 Falsacion: Casos Donde H1 Deberia Fallar

## Proposito
Definir casos y condiciones bajo las cuales el marco debe fallar. La teoria es falsable solo si existen dominios donde C1–C5 no se sostienen.

## Casos propuestos (alto riesgo de falla)
1. **Mercados financieros intradia**
- Razon: alta no‑estacionariedad, ruido exogeno y reflexividad extrema.
- Esperado: fallo en C4 (validez) y/o C2 (robustez).

2. **Memetica ultra‑rapida (viralidad de minutos)**
- Razon: dinamica dominada por shocks exogenos y plataformas.
- Esperado: fallo en symploke y no‑localidad (dominancia de una sola fuente).

3. **Conciencia fenomenica sin proxy confiable**
- Razon: ausencia de observables directos invalida la validacion externa.
- Esperado: fallo en C1 por proxy insuficiente o en C4 por constructo debil.

4. **Justicia en estados fallidos (datos fragmentarios)**
- Razon: cobertura y calidad insuficiente rompe C1 y C5.
- Esperado: fallo por cobertura y sesgos.

## Regla de falsacion operativa
- Si **C1** y **C4** fallan simultaneamente en fase real, el caso se considera refutacion fuerte del marco en ese dominio.

## Uso
- Estos casos no se fuerzan a pasar. Se ejecutan para evidenciar limites y mejorar la teoria.

## Ejecuciones realizadas
- Exogeneidad y shock: `02_Modelado_Simulacion/caso_falsacion_exogeneidad`.
- Observabilidad insuficiente: `02_Modelado_Simulacion/caso_falsacion_observabilidad`.
- No‑estacionariedad extrema: `02_Modelado_Simulacion/caso_falsacion_no_estacionariedad`.
