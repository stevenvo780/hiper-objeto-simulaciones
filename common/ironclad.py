import numpy as np
from sklearn.metrics import mean_squared_error

def generate_surrogates(data, n_surrogates=100):
    """Genera series de tiempo barajadas manteniendo la distribución."""
    surrogates = []
    for _ in range(n_surrogates):
        s = data.copy()
        np.random.shuffle(s)
        surrogates.append(s)
    return surrogates

def edi_significance_test(real_edi, surrogate_edis):
    """
    Calcula el p-valor de la eficacia causal.
    Si p < 0.05, el hiperobjeto es estadísticamente significativo.
    """
    count = sum(1 for s_edi in surrogate_edis if s_edi >= real_edi)
    p_value = count / len(surrogate_edis)
    return p_value

def calculate_ironclad_edi(rmse_reduced, rmse_full):
    """EDI ajustado para evitar sobreajuste."""
    if rmse_reduced == 0: return 0.0
    raw_edi = (rmse_reduced - rmse_full) / rmse_reduced
    return max(0.0, raw_edi)
