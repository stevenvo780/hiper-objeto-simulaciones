# 04_25 Caso de Falsacion: Exogeneidad y Shock (Ejecutado)

## Contexto
- Fenomeno: memetica ultra‑rapida y picos exogenos.
- Justificacion: shocks mediaticos dominan la dinamica.

## Datos
- Wikimedia Pageviews daily (Internet_meme, Meme, TikTok, Deepfake), 2018-2024.
- Archivos de resultados: `02_Modelado_Simulacion/caso_falsacion_exogeneidad/report.md` y `02_Modelado_Simulacion/caso_falsacion_exogeneidad/metrics.json`.

## Resultado
- Fase real: `overall_pass = False`.
- Fallo principal: C1 (convergencia) por spikes exogenos sin nudging.

## Conclusion
- Caso confirma limite del marco frente a shocks exogenos de alta frecuencia.
