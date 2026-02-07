import numpy as np

def simulate_kessler_step(grid, macro_density, collision_prob, fragmentation_rate):
    """
    Simulación vectorizada de la densidad de basura espacial.
    grid: matriz de densidad local (micro).
    macro_density: densidad total en la órbita (macro).
    """
    # 1. Probabilidad de colisión aumenta con la densidad local y macro
    # P = micro * macro * collision_prob
    collisions = grid * macro_density * collision_prob
    
    # 2. Generación de fragmentos (Emergencia de nuevos agentes)
    new_fragments = collisions * fragmentation_rate
    
    # 3. Difusión orbital (La basura se mueve a otras celdas)
    diffusion = 0.1 * (np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0) +
                       np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1) - 4*grid)
    
    next_grid = grid + new_fragments + diffusion - (collisions * 0.1) # Algunos se queman en la atmósfera
    return np.clip(next_grid, 0, 1)

def run_simulation(steps, initial_density, macro_coupling):
    grid = np.full((50, 50), initial_density)
    history = []
    macro_state = initial_density
    
    for _ in range(steps):
        # La ODE macro describe la acumulación total
        macro_state = macro_state * 1.01 # Crecimiento exógeno (nuevos lanzamientos)
        grid = simulate_kessler_step(grid, macro_state, 0.02 * macro_coupling, 5.0)
        history.append(np.mean(grid))
        
    return history
