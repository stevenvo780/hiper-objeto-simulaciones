import numpy as np
import random


def simulate_abm(params, steps, seed):
    random.seed(seed)
    n = params.get("grid_size", 20)
    diffusion = params.get("diffusion", 0.2)
    noise = params.get("noise", 0.02)
    macro_coupling = params.get("macro_coupling", 0.3)
    forcing_scale = params.get("forcing_scale", 0.2)
    damping = params.get("damping", 0.05)
    assimilation_series = params.get("assimilation_series")
    assimilation_strength = params.get("assimilation_strength", 0.0)
    _store_grid = params.get("_store_grid", True)

    grid = [[random.uniform(-0.2, 0.2) for _ in range(n)] for _ in range(n)]

    forcing = params["forcing_series"]
    u_series = []
    grid_series = [] if _store_grid else None

    for t in range(steps):
        f = forcing[t]

        total = 0.0
        for i in range(n):
            total += sum(grid[i])
        macro = total / (n * n)

        new_grid = [[0.0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                neighbors = []
                if i > 0:
                    neighbors.append(grid[i - 1][j])
                if i < n - 1:
                    neighbors.append(grid[i + 1][j])
                if j > 0:
                    neighbors.append(grid[i][j - 1])
                if j < n - 1:
                    neighbors.append(grid[i][j + 1])
                neighbor_mean = sum(neighbors) / len(neighbors)

                x = grid[i][j]
                new_x = (
                    x
                    + diffusion * (neighbor_mean - x)
                    + macro_coupling * (macro - x)
                    + forcing_scale * f
                    - damping * x
                    + random.uniform(-noise, noise)
                )
                new_grid[i][j] = max(-50.0, min(50.0, new_x))

        total = 0.0
        for i in range(n):
            total += sum(new_grid[i])
        u = total / (n * n)

        if assimilation_series is not None and t < len(assimilation_series):
            target = assimilation_series[t]
            if target is not None:
                u = u + assimilation_strength * (target - u)

        grid = new_grid
        u_series.append(u)
        if _store_grid:
            grid_series.append([row[:] for row in grid])

    return {
        "u": u_series,
        "grid": grid_series,
        "forcing": forcing,
    }
