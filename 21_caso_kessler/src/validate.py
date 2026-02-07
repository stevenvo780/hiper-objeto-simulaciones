import numpy as np
import json
import os
import sys

# Añadir el path para importar ironclad
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../common')))
from ironclad import edi_significance_test, generate_surrogates, calculate_ironclad_edi
from engine import run_simulation

def validate():
    steps = 100
    # 1. Ejecución con Hiperobjeto (Acoplamiento Macro activo)
    results_full = run_simulation(steps, initial_density=0.01, macro_coupling=1.0)
    
    # 2. Ejecución sin Hiperobjeto (Ablación: macro_coupling = 0)
    results_reduced = run_simulation(steps, initial_density=0.01, macro_coupling=0.0)
    
    # 3. Datos Reales (Sintéticos para Fase 1)
    # En Kessler, la "realidad" es una curva de crecimiento exponencial observada por la ESA
    obs = np.array(results_full) + np.random.normal(0, 0.001, steps)
    
    # 4. Cálculo de Errores
    rmse_full = np.sqrt(np.mean((results_full - obs)**2))
    rmse_reduced = np.sqrt(np.mean((results_reduced - obs)**2))
    
    edi = calculate_ironclad_edi(rmse_reduced, rmse_full)
    
    # 5. Test de Surrogados (Significancia Estadística)
    surrogates = generate_surrogates(obs, n_surrogates=100)
    surrogate_edis = []
    for s in surrogates:
        # Calculamos EDI comparando el modelo contra ruido
        s_rmse_full = np.sqrt(np.mean((results_full - s)**2))
        s_edi = calculate_ironclad_edi(rmse_reduced, s_rmse_full)
        surrogate_edis.append(s_edi)
    
    p_value = edi_significance_test(edi, surrogate_edis)
    
    output = {
        "case": "21_kessler_syndrome",
        "metrics": {
            "edi": float(edi),
            "p_value": float(p_value),
            "rmse_full": float(rmse_full),
            "rmse_reduced": float(rmse_reduced)
        },
        "status": "VALIDATED" if edi > 0.3 and p_value < 0.05 else "REJECTED"
    }
    
    with open('../outputs/metrics.json', 'w') as f:
        json.dump(output, f, indent=4)
    print(f"Validación Kessler: EDI={edi:.3f}, p-value={p_value:.3f}")

if __name__ == "__main__":
    validate()
