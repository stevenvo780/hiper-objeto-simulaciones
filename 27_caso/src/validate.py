
import numpy as np
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../common')))
from ironclad import edi_significance_test, calculate_ironclad_edi
from factory import get_engine

def validate():
    engine = get_engine(27)
    steps = 50
    # Simulación simple para validar estructura
    data = np.random.rand(10, 10)
    macro = 1.0
    for _ in range(steps):
        data = engine(data, macro)
    
    # Generar metrics.json placeholder
    output = {
        "case": "27_caso",
        "metrics": { "edi": 0.45, "p_value": 0.01 },
        "status": "PROTOTYPE"
    }
    with open('../outputs/metrics.json', 'w') as f:
        json.dump(output, f, indent=4)
    print(f"Caso 27 inicializado.")

if __name__ == '__main__':
    validate()
