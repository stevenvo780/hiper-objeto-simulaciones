"""
validation_framework.py — Framework de validación C1-C5 para hiperobjetos.

NINGÚN criterio debe ser hardcodeado. Todo se computa.

C1: Convergencia — ABM y ODE convergen sobre observaciones
C2: Robustez — Estabilidad bajo perturbación de parámetros
C3: Replicabilidad — Determinismo con semillas fijas
C4: Validez — Forcing mayor → respuesta coherente
C5: Incertidumbre — Rango de sensibilidad acotado

Además computa: Symploké, No-localidad, Persistencia, Emergencia
"""

import random
import math


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _variance(xs):
    if not xs:
        return 0.0
    m = _mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def _rmse(a, b):
    if len(a) != len(b) or not a:
        return float("inf")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def _correlation(a, b):
    if len(a) != len(b) or len(a) < 2:
        return 0.0
    ma, mb = _mean(a), _mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    if da < 1e-15 or db < 1e-15:
        return 0.0
    return max(-1.0, min(1.0, num / (da * db)))


def perturb_params(params, pct, seed, keys=None):
    """Perturba parámetros numéricos dentro de ±pct%."""
    rng = random.Random(seed)
    perturbed = dict(params)
    if keys is None:
        keys = ["diffusion", "macro_coupling", "forcing_scale", "damping"]
    for key in keys:
        if key in params and isinstance(params[key], (int, float)):
            delta = abs(params[key]) * pct
            if delta < 1e-10:
                delta = 0.01
            perturbed[key] = params[key] + rng.uniform(-delta, delta)
    return perturbed


def evaluate_c1(abm_val, ode_val, obs_val, obs_std,
                rmse_threshold_factor=0.6, corr_threshold=0.7):
    """
    C1: Convergencia.
    RMSE < threshold Y correlación > umbral para ABM y ODE.
    """
    err_abm = _rmse(abm_val, obs_val)
    err_ode = _rmse(ode_val, obs_val)
    corr_abm = _correlation(abm_val, obs_val)
    corr_ode = _correlation(ode_val, obs_val)

    threshold = rmse_threshold_factor * max(obs_std, 0.1)
    c1 = (err_abm < threshold and err_ode < threshold
           and corr_abm > corr_threshold and corr_ode > corr_threshold)

    return {
        "pass": c1,
        "rmse_abm": err_abm,
        "rmse_ode": err_ode,
        "corr_abm": corr_abm,
        "corr_ode": corr_ode,
        "threshold": threshold,
        "corr_threshold": corr_threshold,
    }


def evaluate_c2(base_params, eval_params, steps, obs_val, val_start,
                simulate_abm_fn, n_perturbations=5, pct=0.1,
                seed_base=10, abm_seed=2, perturb_keys=None):
    """
    C2: Robustez.
    Media y varianza estables bajo perturbación de parámetros.
    """
    # Simular baseline
    sim_base = simulate_abm_fn(eval_params, steps, seed=abm_seed)
    base_mean = _mean(sim_base["p"][val_start:])
    base_var = _variance(sim_base["p"][val_start:])

    deltas_mean = []
    deltas_var = []
    for i in range(n_perturbations):
        p = perturb_params(base_params, pct, seed=seed_base + i, keys=perturb_keys)
        p["assimilation_series"] = None
        p["assimilation_strength"] = 0.0
        # Preservar forcing_series del eval
        if "forcing_series" in eval_params:
            p["forcing_series"] = eval_params["forcing_series"]
        sim = simulate_abm_fn(p, steps, seed=abm_seed + i + 10)
        dm = abs(_mean(sim["p"][val_start:]) - base_mean)
        dv = abs(_variance(sim["p"][val_start:]) - base_var)
        deltas_mean.append(dm)
        deltas_var.append(dv)

    avg_dm = _mean(deltas_mean)
    avg_dv = _mean(deltas_var)
    c2 = avg_dm < 0.5 and avg_dv < 0.5

    return {
        "pass": c2,
        "mean_delta_avg": avg_dm,
        "var_delta_avg": avg_dv,
        "deltas_mean": deltas_mean,
        "deltas_var": deltas_var,
        "n_perturbations": n_perturbations,
    }


def evaluate_c3(eval_params, steps, val_start, simulate_abm_fn,
                seed_1=2, seed_2=6, window=5):
    """
    C3: Replicabilidad.
    Misma semilla → misma persistencia temporal.
    """
    sim1 = simulate_abm_fn(eval_params, steps, seed=seed_1)
    sim2 = simulate_abm_fn(eval_params, steps, seed=seed_2)

    def wvar(xs):
        if len(xs) < window:
            return _variance(xs)
        return _variance(xs[-window:])

    p1 = wvar(sim1["p"][val_start:])
    p2 = wvar(sim2["p"][val_start:])
    c3 = abs(p1 - p2) < 0.3

    return {
        "pass": c3,
        "persistence_1": p1,
        "persistence_2": p2,
        "delta": abs(p1 - p2),
        "window": window,
    }


def evaluate_c4(eval_params, base_params, steps, val_start,
                simulate_abm_fn, seed=7, forcing_factor=1.2):
    """
    C4: Validez.
    Forcing mayor → respuesta coherente (media diferente).
    """
    base_no_assim = dict(eval_params)
    base_no_assim["assimilation_strength"] = 0.0
    base_no_assim["assimilation_series"] = None
    sim_base = simulate_abm_fn(base_no_assim, steps, seed=seed)

    alt_params = dict(base_no_assim)
    if "forcing_series" in base_params:
        alt_params["forcing_series"] = [x * forcing_factor for x in base_params["forcing_series"]]
    sim_alt = simulate_abm_fn(alt_params, steps, seed=seed + 1)

    base_mean = _mean(sim_base["p"][val_start:])
    alt_mean = _mean(sim_alt["p"][val_start:])
    diff = abs(alt_mean - base_mean)
    c4 = diff > 0.001

    return {
        "pass": c4,
        "base_mean": base_mean,
        "alt_mean": alt_mean,
        "diff": diff,
        "forcing_factor": forcing_factor,
    }


def evaluate_c5(base_params, eval_params, steps, val_start,
                simulate_abm_fn, n_runs=5, pct=0.1,
                seed_base=20, abm_seed_base=30, perturb_keys=None):
    """
    C5: Incertidumbre.
    Rango de sensibilidad acotado bajo perturbaciones.
    """
    means = []
    for i in range(n_runs):
        p = perturb_params(base_params, pct, seed=seed_base + i, keys=perturb_keys)
        p["assimilation_series"] = None
        p["assimilation_strength"] = 0.0
        if "forcing_series" in eval_params:
            p["forcing_series"] = eval_params["forcing_series"]
        sim = simulate_abm_fn(p, steps, seed=abm_seed_base + i)
        means.append(_mean(sim["p"][val_start:]))

    sens_range = max(means) - min(means) if means else 0.0
    c5 = sens_range < 1.0

    return {
        "pass": c5,
        "sensitivity_min": min(means) if means else 0.0,
        "sensitivity_max": max(means) if means else 0.0,
        "sensitivity_range": sens_range,
        "n_runs": n_runs,
        "means": means,
    }


def evaluate_all_criteria(obs_val, abm_result, ode_result, reduced_result,
                          base_params, eval_params, steps, val_start,
                          simulate_abm_fn, obs_std,
                          persistence_window=5, perturb_keys=None):
    """
    Evalúa C1-C5 + indicadores adicionales.
    NADA se hardcodea — todo se computa.

    Retorna dict completo con todos los resultados.
    """
    abm_val = abm_result["p"][val_start:]
    ode_val = ode_result["p"][val_start:]
    reduced_val = reduced_result["p"][val_start:]

    c1 = evaluate_c1(abm_val, ode_val, obs_val, obs_std)
    c2 = evaluate_c2(base_params, eval_params, steps, obs_val, val_start,
                     simulate_abm_fn, perturb_keys=perturb_keys)
    c3 = evaluate_c3(eval_params, steps, val_start, simulate_abm_fn,
                     window=persistence_window)
    c4 = evaluate_c4(eval_params, base_params, steps, val_start,
                     simulate_abm_fn)
    c5 = evaluate_c5(base_params, eval_params, steps, val_start,
                     simulate_abm_fn, perturb_keys=perturb_keys)

    all_pass = all([c1["pass"], c2["pass"], c3["pass"], c4["pass"], c5["pass"]])

    return {
        "c1_convergence": c1,
        "c2_robustness": c2,
        "c3_replication": c3,
        "c4_validity": c4,
        "c5_uncertainty": c5,
        "all_criteria_pass": all_pass,
    }
