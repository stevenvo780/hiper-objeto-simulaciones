# 03_23 Analisis Interpretativo de Fallos

## Proposito
Explicar por que ciertos dominios fallan el marco (C1–C5), sin forzar ajuste.

## Fallos en casos base
- **Finanzas (SPY)**: falla en C4 (validez) y EDI/CR bajos. El sistema es altamente reflexivo y dominado por shocks exogenos y retroalimentacion rapida.
- **Movilidad**: prototipo. Pasa parcialmente pero no alcanza estabilidad plena; requiere mayor granularidad o mejores proxies.

## Fallos por falsacion (ejecutados)
1. **Exogeneidad y shock** (`caso_falsacion_exogeneidad`)
- Motivo: picos exogenos de alta frecuencia rompen la convergencia.
- Criterio: C1 falla por RMSE alto y baja correlacion.

2. **Observabilidad insuficiente** (`caso_falsacion_observabilidad`)
- Motivo: cobertura artificialmente reducida (< 0.85) rompe validez externa.
- Criterio: C1 y C5 fallan por sesgo y falta de datos.

3. **No‑estacionariedad extrema** (`caso_falsacion_no_estacionariedad`)
- Motivo: quiebres de regimen y alta volatilidad reducen correlacion.
- Criterio: C1 y C4 fallan por error alto y baja coherencia causal.

## Caso jefe final (ejecutado)
**Moderacion adversarial** (`caso_moderacion_adversarial`)
- Motivo: retroalimentacion estrategica cambia la distribucion objetivo.
- Criterio: C1 y C4 fallan por baja correlacion y error alto.

## Caso jefe final adicional (ejecutado)
**RTB publicidad** (`caso_rtb_publicidad`)
- Motivo: subastas con agentes estrategicos rompen supuestos de estabilidad.
- Criterio: C1 y C4 fallan por baja correlacion y error alto.

**Politicas estrategicas** (`caso_politicas_estrategicas`)
- Motivo: respuesta endogena al regulador altera el objetivo.
- Criterio: C1 y C4 fallan por baja correlacion y error alto.

## Implicaciones para la teoria
- La teoria no es universal: necesita condiciones de observabilidad, estabilidad de regimen y acople macro significativo.
- La falsacion confirma limites y protege la validez cientifica del marco.
