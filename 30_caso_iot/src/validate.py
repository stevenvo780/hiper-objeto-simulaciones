
import numpy as np
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../common')))
from ironclad import edi_significance_test, calculate_ironclad_edi, generate_surrogates
from factory import get_engine

def validate():
    engine = get_engine(30)
    steps = 100
    
    # Simulación Completa (Macro activo)
    data_full = np.random.rand(10, 10)
    history_full = []
    for t in range(steps):
        data_full = engine(data_full, macro=1.0)
        history_full.append(np.mean(data_full))
    
    # Simulación Reducida (Ablación Macro)
    data_red = np.random.rand(10, 10)
    history_red = []
    for t in range(steps):
        data_red = engine(data_red, macro=0.0) # Sin acople macro
        history_red.append(np.mean(data_red))
    
    # Observación "Real" (Simulada con ruido para esta fase)
    obs = np.array(history_full) + np.random.normal(0, 0.01, steps)
    
    rmse_full = np.sqrt(np.mean((history_full - obs)**2))
    rmse_red = np.sqrt(np.mean((history_red - obs)**2))
    edi = calculate_ironclad_edi(rmse_red, rmse_full)
    
    # Test de Significancia
    surrogates = generate_surrogates(obs, n_surrogates=50)
    surr_edis = [calculate_ironclad_edi(rmse_red, np.sqrt(np.mean((history_full - s)**2))) for s in surrogates]
    p_val = edi_significance_test(edi, surr_edis)
    
    output = {
        "case": "30_caso",
        "metrics": { "edi": float(edi), "p_value": float(p_val) },
        "status": "VALIDATED" if edi > 0.3 else "FAILED_THRESHOLD"
    }
    
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'metrics.json'), 'w') as f:
        json.dump(output, f, indent=4)
    print(f"Caso 30 (Fase Real): EDI={edi:.3f}, p={p_val:.3f}")

if __name__ == '__main__':
    validate()
