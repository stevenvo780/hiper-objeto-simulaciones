import numpy as np

def get_engine(case_num):
    """Retorna la función de simulación específica para cada caso."""
    
    if case_num == 22: # Salinización
        def engine(grid, macro):
            # Difusión + Evaporación (hacia arriba)
            diff = 0.1 * (np.roll(grid, 1) + np.roll(grid, -1) - 2*grid)
            return grid + diff + (macro * 0.05)
        return engine
        
    if case_num == 25: # Microplásticos
        def engine(levels, macro):
            # Acumulación por niveles tróficos (magnificación)
            # levels es un array de concentración por nivel [micro, meso, macro]
            accumulation = levels * 1.1 * macro
            return np.clip(accumulation, 0, 100)
        return engine

    if case_num == 30: # IoT Emergence
        def engine(bits, macro):
            # Sincronización de protocolos por ruido macro
            sync = bits ^ (np.roll(bits, 1) & macro.astype(int))
            return sync
        return engine

    # Default: Difusión simple
    def default_engine(grid, macro):
        return grid * 0.95 + macro * 0.05
    return default_engine
