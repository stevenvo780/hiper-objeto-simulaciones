# 04_26 Caso de Falsacion: Observabilidad Insuficiente (Ejecutado)

## Contexto
- Fenomeno: ausencia de proxy confiable.
- Justificacion: cobertura insuficiente invalida validacion externa.

## Datos
- OWID Cantril ladder con missingness inducido.
- Archivos de resultados: `02_Modelado_Simulacion/caso_falsacion_observabilidad/report.md` y `02_Modelado_Simulacion/caso_falsacion_observabilidad/metrics.json`.

## Resultado
- Fase real: `overall_pass = False`.
- Fallo principal: C1 y C5 por cobertura < 0.85.

## Conclusion
- Caso confirma limite del marco cuando no hay observables robustos.
