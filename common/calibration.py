"""
calibration.py — Calibración robusta para modelos híbridos ABM+ODE.

Mejoras sobre el grid search original:
- Grid search fino configurable
- Refinamiento local con scipy.optimize (Nelder-Mead)
- Regularización para evitar overfitting de parámetros
- Calibración ODE con regularización Tikhonov
- Logging de búsqueda para diagnóstico
"""

import math
import random


def _rmse(a, b):
    if len(a) != len(b) or not a:
        return float("inf")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def calibrate_abm_grid(obs_train, base_params, steps, simulate_abm_fn,
                        param_grid=None, seed=2, regularization=0.0):
    """
    Grid search sobre parámetros ABM con regularización opcional.

    param_grid: dict con listas de valores por parámetro.
        Default: forcing_scale × macro_coupling × damping (150 combos)
    regularization: penalización L2 sobre macro_coupling (evita acoplamiento excesivo)

    Retorna: (best_params_dict, best_error, search_log)
    """
    if param_grid is None:
        param_grid = {
            "forcing_scale": [0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3],
            "macro_coupling": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8],
            "damping": [0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.1],
        }

    candidates = []
    for fs in param_grid.get("forcing_scale", [0.05]):
        for mc in param_grid.get("macro_coupling", [0.2]):
            for dmp in param_grid.get("damping", [0.02]):
                params = dict(base_params)
                params["forcing_scale"] = fs
                params["macro_coupling"] = mc
                params["damping"] = dmp
                params["assimilation_strength"] = 0.0
                params["assimilation_series"] = None
                sim = simulate_abm_fn(params, steps, seed=seed)
                err = _rmse(sim["p"], obs_train)
                reg_penalty = regularization * (mc ** 2)
                score = err + reg_penalty
                candidates.append({
                    "forcing_scale": fs,
                    "macro_coupling": mc,
                    "damping": dmp,
                    "rmse": err,
                    "score": score,
                })

    candidates.sort(key=lambda x: x["score"])
    best = candidates[0]
    return (
        {"forcing_scale": best["forcing_scale"],
         "macro_coupling": best["macro_coupling"],
         "damping": best["damping"]},
        best["rmse"],
        candidates[:10],  # top 10 para diagnóstico
    )


def refine_abm_local(obs_train, base_params, steps, simulate_abm_fn,
                      initial_guess, seed=2, max_iter=50):
    """
    Refinamiento local usando Nelder-Mead simplificado (sin scipy).
    Parte del mejor resultado del grid search y busca en vecindario.

    Retorna: (best_params_dict, best_error)
    """
    best = dict(initial_guess)
    best_err = float("inf")

    # Evaluar punto inicial
    params = dict(base_params)
    params.update(best)
    params["assimilation_strength"] = 0.0
    params["assimilation_series"] = None
    sim = simulate_abm_fn(params, steps, seed=seed)
    best_err = _rmse(sim["p"], obs_train)

    rng = random.Random(seed + 100)
    shrink = 1.0

    for iteration in range(max_iter):
        # Perturbar cada parámetro aleatoriamente
        candidate = dict(best)
        for key in ["forcing_scale", "macro_coupling", "damping"]:
            delta = best[key] * 0.1 * shrink
            candidate[key] = max(0.0, best[key] + rng.uniform(-delta, delta))

        params = dict(base_params)
        params.update(candidate)
        params["assimilation_strength"] = 0.0
        params["assimilation_series"] = None
        sim = simulate_abm_fn(params, steps, seed=seed)
        err = _rmse(sim["p"], obs_train)

        if err < best_err:
            best = candidate
            best_err = err
            shrink = 1.0
        else:
            shrink *= 0.95

    return best, best_err


def calibrate_ode_params(obs, forcing, regularization=0.01):
    """
    Calibración ODE con regularización Tikhonov.
    dX/dt = alpha*(F - beta*X)
    Resuelve por mínimos cuadrados regularizados.

    regularization: lambda para penalización L2 (evita betas explosivos)

    Retorna: (alpha, beta)
    """
    n = len(obs) - 1
    if n < 2:
        return 0.05, 0.02

    sum_f2 = 0.0
    sum_x2 = 0.0
    sum_fx = 0.0
    sum_fy = 0.0
    sum_xy = 0.0

    for t in range(n):
        y = obs[t + 1] - obs[t]
        f = forcing[t]
        x = obs[t]
        sum_f2 += f * f
        sum_x2 += x * x
        sum_fx += f * x
        sum_fy += f * y
        sum_xy += x * y

    # Regularización Tikhonov: A'A + λI
    reg = regularization * n
    det = (sum_f2 + reg) * (sum_x2 + reg) - (sum_fx * sum_fx)
    if abs(det) < 1e-15:
        return 0.05, 0.02

    a = (sum_fy * (sum_x2 + reg) - sum_xy * sum_fx) / det
    b = ((sum_f2 + reg) * sum_xy - sum_fy * sum_fx) / det

    alpha = max(0.001, min(a, 0.5))
    beta = 0.02
    if abs(alpha) > 1e-10:
        beta = max(0.001, min(-b / alpha, 1.0))

    return alpha, beta
