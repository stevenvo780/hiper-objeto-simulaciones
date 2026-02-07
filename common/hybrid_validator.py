"""
hybrid_validator.py — Validador unificado para todos los casos de simulación.

Este módulo implementa el pipeline completo de validación:
  1. Carga de datos (sintéticos + reales)
  2. Construcción de forcing
  3. Calibración ABM+ODE (grid search + refinamiento)
  4. Evaluación: modelo completo vs. reducido
  5. Cómputo de EDI con bootstrap CI
  6. Evaluación C1-C5 (todo computado, nada hardcodeado)
  7. Indicadores: Symploké, no-localidad, persistencia, emergencia
  8. Generación de outputs (metrics.json + report.md)

Cada caso solo necesita proveer:
  - simulate_abm(params, steps, seed) → dict con serie principal y grid
  - simulate_ode(params, steps, seed) → dict con serie principal
  - Configuración específica del caso (CaseConfig)
"""

import json
import math
import os
import random
import subprocess
from datetime import datetime

import numpy as np
import pandas as pd


# ─── Métricas básicas ────────────────────────────────────────────────────────

def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def variance(xs):
    if not xs:
        return 0.0
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def rmse(a, b):
    if len(a) != len(b) or not a:
        return float("inf")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def correlation(a, b):
    if len(a) != len(b) or len(a) < 2:
        return 0.0
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    if da < 1e-15 or db < 1e-15:
        return 0.0
    return max(-1.0, min(1.0, num / (da * db)))


def window_variance(xs, window):
    if len(xs) < window:
        return variance(xs)
    return variance(xs[-window:])


# ─── EDI & Emergencia ─────────────────────────────────────────────────────────

def compute_edi(rmse_abm, rmse_reduced):
    """EDI = (rmse_reduced - rmse_abm) / rmse_reduced"""
    if rmse_reduced < 1e-15:
        return 0.0
    return (rmse_reduced - rmse_abm) / rmse_reduced


def bootstrap_edi(obs_val, abm_val, reduced_val, n_boot=500, ci=0.95, seed=42):
    """Bootstrap CI para EDI."""
    rng = random.Random(seed)
    n = len(obs_val)
    if n < 4:
        edi = compute_edi(rmse(abm_val, obs_val), rmse(reduced_val, obs_val))
        return edi, edi, edi

    samples = []
    for _ in range(n_boot):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        obs_b = [obs_val[i] for i in idx]
        abm_b = [abm_val[i] for i in idx]
        red_b = [reduced_val[i] for i in idx]
        samples.append(compute_edi(rmse(abm_b, obs_b), rmse(red_b, obs_b)))

    samples.sort()
    alpha = (1.0 - ci) / 2.0
    lo = samples[max(0, int(alpha * n_boot))]
    hi = samples[min(n_boot - 1, int((1.0 - alpha) * n_boot))]
    return mean(samples), lo, hi


def _kde_entropy(series, n_eval=50):
    """Entropía via KDE."""
    n = len(series)
    if n < 2:
        return 0.0
    s = (sum((x - mean(series)) ** 2 for x in series) / n) ** 0.5
    if s < 1e-15:
        return 0.0
    h = 1.06 * s * (n ** (-0.2))
    if h < 1e-15:
        h = (max(series) - min(series)) / 10.0
    margin = 3 * h
    x_min = min(series) - margin
    x_max = max(series) + margin
    dx = (x_max - x_min) / n_eval
    entropy = 0.0
    for k in range(n_eval):
        x = x_min + (k + 0.5) * dx
        density = sum(math.exp(-0.5 * ((x - v) / h) ** 2) / (h * math.sqrt(2 * math.pi)) for v in series) / n
        if density > 1e-15:
            entropy -= density * math.log(density) * dx
    return max(0.0, entropy)


def effective_information(obs, full_pred, reduced_pred):
    """EI = H(residuos_reducido) - H(residuos_completo)"""
    res_full = [o - p for o, p in zip(obs, full_pred)]
    res_reduced = [o - p for o, p in zip(obs, reduced_pred)]
    return _kde_entropy(res_reduced) - _kde_entropy(res_full)


# ─── Cohesión y Symploké ─────────────────────────────────────────────────────

def internal_vs_external_cohesion(grid_series, forcing_series):
    steps = len(grid_series)
    if steps == 0:
        return 0.0, 0.0
    n = len(grid_series[0])
    int_corrs = []
    ext_corrs = []
    for i in range(n):
        for j in range(n):
            cell = [grid_series[t][i][j] for t in range(steps)]
            nb = []
            for t in range(steps):
                neighbors = []
                if i > 0: neighbors.append(grid_series[t][i - 1][j])
                if i < n - 1: neighbors.append(grid_series[t][i + 1][j])
                if j > 0: neighbors.append(grid_series[t][i][j - 1])
                if j < n - 1: neighbors.append(grid_series[t][i][j + 1])
                nb.append(sum(neighbors) / len(neighbors))
            int_corrs.append(correlation(cell, nb))
            if len(forcing_series) == steps:
                ext_corrs.append(correlation(cell, forcing_series))
    internal = mean(int_corrs)
    external = mean(ext_corrs) if ext_corrs else 0.0
    return internal, external


def cohesion_ratio(internal, external):
    if abs(external) < 1e-10:
        return float("inf") if internal > 0 else 0.0
    return abs(internal / external)


def dominance_share(grid_series):
    steps = len(grid_series)
    if steps == 0:
        return 1.0
    n = len(grid_series[0])
    regional = []
    for t in range(steps):
        total = sum(sum(row) for row in grid_series[t])
        regional.append(total / (n * n))
    scores = []
    for i in range(n):
        for j in range(n):
            cell = [grid_series[t][i][j] for t in range(steps)]
            scores.append(abs(correlation(cell, regional)))
    total_s = sum(scores) if scores else 1.0
    if total_s < 1e-15:
        return 1.0 / (n * n)
    return max(scores) / total_s


# ─── Calibración ──────────────────────────────────────────────────────────────

def build_forcing_from_training(train_values, total_steps):
    """Construye forcing como tendencia lineal + forcing lagged."""
    n_train = len(train_values)
    t = np.arange(n_train)
    slope, intercept = np.polyfit(t, train_values, 1)
    t_full = np.arange(total_steps)
    trend = (intercept + slope * t_full).tolist()
    return trend, (slope, intercept)


def calibrate_ode(obs_train, forcing_train, regularization=0.01):
    """ODE: dX/dt = alpha*(F - beta*X) con regularización Tikhonov."""
    n = len(obs_train) - 1
    if n < 2:
        return 0.05, 0.02

    sf2, sx2, sfx, sfy, sxy = 0.0, 0.0, 0.0, 0.0, 0.0
    for t in range(n):
        y = obs_train[t + 1] - obs_train[t]
        f, x = forcing_train[t], obs_train[t]
        sf2 += f * f
        sx2 += x * x
        sfx += f * x
        sfy += f * y
        sxy += x * y

    reg = regularization * n
    det = (sf2 + reg) * (sx2 + reg) - sfx * sfx
    if abs(det) < 1e-15:
        return 0.05, 0.02

    a = (sfy * (sx2 + reg) - sxy * sfx) / det
    b = ((sf2 + reg) * sxy - sfy * sfx) / det

    alpha = max(0.001, min(a, 0.5))
    beta = max(0.001, min(-b / alpha if abs(alpha) > 1e-10 else 0.02, 1.0))
    return alpha, beta


def calibrate_abm(obs_train, base_params, steps, simulate_abm_fn,
                   param_grid=None, seed=2, n_refine=200):
    """
    Grid search amplio + refinamiento local intensivo.
    Default: 2000+ combinaciones con 200 iteraciones de refinamiento.
    """
    if param_grid is None:
        param_grid = {
            "forcing_scale": [0.005, 0.01, 0.02, 0.04, 0.08, 0.12, 0.2, 0.3,
                              0.4, 0.5, 0.65, 0.8, 1.0, 1.3],
            "macro_coupling": [0.0, 0.1, 0.2, 0.4, 0.6, 0.75, 0.85, 0.95],
            "damping": [0.0, 0.01, 0.05, 0.1, 0.2, 0.35, 0.5, 0.65, 0.8],
        }

    candidates = []
    for fs in param_grid["forcing_scale"]:
        for mc in param_grid["macro_coupling"]:
            for dmp in param_grid["damping"]:
                params = dict(base_params)
                params["forcing_scale"] = fs
                params["macro_coupling"] = mc
                params["damping"] = dmp
                params["assimilation_strength"] = 0.0
                params["assimilation_series"] = None
                sim = simulate_abm_fn(params, steps, seed=seed)
                key = _get_series_key(sim)
                err = rmse(sim[key][:len(obs_train)], obs_train)
                candidates.append((err, fs, mc, dmp))

    candidates.sort(key=lambda x: x[0])
    best = candidates[0]

    # Refinamiento local intensivo alrededor del mejor
    best_params = {"forcing_scale": best[1], "macro_coupling": best[2], "damping": best[3]}
    best_err = best[0]
    rng = random.Random(seed + 100)
    for _ in range(n_refine):
        candidate = {
            "forcing_scale": max(0.0, best_params["forcing_scale"] + rng.uniform(-0.05, 0.05)),
            "macro_coupling": max(0.0, min(1.0, best_params["macro_coupling"] + rng.uniform(-0.1, 0.1))),
            "damping": max(0.0, best_params["damping"] + rng.uniform(-0.05, 0.05)),
        }
        params = dict(base_params)
        params.update(candidate)
        params["assimilation_strength"] = 0.0
        params["assimilation_series"] = None
        sim = simulate_abm_fn(params, steps, seed=seed)
        key = _get_series_key(sim)
        err = rmse(sim[key][:len(obs_train)], obs_train)
        if err < best_err:
            best_params = candidate
            best_err = err

    return best_params, best_err, candidates[:5]


def _get_series_key(sim_result):
    """Detecta la clave de la serie principal del resultado."""
    for k in ["p", "tbar", "x", "e", "m", "w", "incidence", "share"]:
        if k in sim_result:
            return k
    raise KeyError(f"No se encontró clave de serie en: {list(sim_result.keys())}")


# ─── Perturbación ─────────────────────────────────────────────────────────────

def perturb_params(params, pct, seed, keys=None):
    rng = random.Random(seed)
    p = dict(params)
    if keys is None:
        keys = ["diffusion", "macro_coupling", "forcing_scale", "damping"]
    for k in keys:
        if k in p and isinstance(p[k], (int, float)):
            delta = abs(p[k]) * pct
            if delta < 1e-10:
                delta = 0.01
            p[k] = p[k] + rng.uniform(-delta, delta)
    return p


# ─── Validación C1-C5 ────────────────────────────────────────────────────────

def evaluate_c1(abm_val, ode_val, obs_val, obs_std,
                threshold_factor=1.0, corr_threshold=0.7):
    err_abm = rmse(abm_val, obs_val)
    err_ode = rmse(ode_val, obs_val)
    corr_abm = correlation(abm_val, obs_val)
    corr_ode = correlation(ode_val, obs_val)
    threshold = threshold_factor * max(obs_std, 0.1)
    c1 = (err_abm < threshold and err_ode < threshold
           and corr_abm > corr_threshold and corr_ode > corr_threshold)
    return c1, {
        "rmse_abm": err_abm, "rmse_ode": err_ode,
        "corr_abm": corr_abm, "corr_ode": corr_ode,
        "threshold": threshold,
    }


def evaluate_c2(base_params, eval_params, steps, val_start,
                simulate_abm_fn, series_key, n_pert=5, pct=0.1, seed_base=10):
    sim_base = simulate_abm_fn(eval_params, steps, seed=2)
    base_mean = mean(sim_base[series_key][val_start:])
    base_var = variance(sim_base[series_key][val_start:])
    deltas_m, deltas_v = [], []
    for i in range(n_pert):
        p = perturb_params(base_params, pct, seed=seed_base + i)
        p["assimilation_series"] = None
        p["assimilation_strength"] = 0.0
        if "forcing_series" in eval_params:
            p["forcing_series"] = eval_params["forcing_series"]
        sim = simulate_abm_fn(p, steps, seed=2 + i + 10)
        deltas_m.append(abs(mean(sim[series_key][val_start:]) - base_mean))
        deltas_v.append(abs(variance(sim[series_key][val_start:]) - base_var))
    avg_dm = mean(deltas_m)
    avg_dv = mean(deltas_v)
    return avg_dm < 0.5 and avg_dv < 0.5, {"mean_delta": avg_dm, "var_delta": avg_dv}


def evaluate_c3(eval_params, steps, val_start, simulate_abm_fn,
                series_key, seed_1=2, seed_2=6, window=5):
    s1 = simulate_abm_fn(eval_params, steps, seed=seed_1)
    s2 = simulate_abm_fn(eval_params, steps, seed=seed_2)
    p1 = window_variance(s1[series_key][val_start:], window)
    p2 = window_variance(s2[series_key][val_start:], window)
    return abs(p1 - p2) < 0.3, {"persistence_1": p1, "persistence_2": p2}


def evaluate_c4(eval_params, base_params, steps, val_start,
                simulate_abm_fn, series_key, seed=7, factor=1.2):
    p_base = dict(eval_params)
    p_base["assimilation_strength"] = 0.0
    p_base["assimilation_series"] = None
    sim_b = simulate_abm_fn(p_base, steps, seed=seed)
    p_alt = dict(p_base)
    if "forcing_series" in base_params:
        p_alt["forcing_series"] = [x * factor for x in base_params["forcing_series"]]
    sim_a = simulate_abm_fn(p_alt, steps, seed=seed + 1)
    diff = abs(mean(sim_a[series_key][val_start:]) - mean(sim_b[series_key][val_start:]))
    return diff > 0.001, {"diff": diff}


def evaluate_c5(base_params, eval_params, steps, val_start,
                simulate_abm_fn, series_key, n_runs=5, pct=0.1):
    means = []
    for i in range(n_runs):
        p = perturb_params(base_params, pct, seed=20 + i)
        p["assimilation_series"] = None
        p["assimilation_strength"] = 0.0
        if "forcing_series" in eval_params:
            p["forcing_series"] = eval_params["forcing_series"]
        sim = simulate_abm_fn(p, steps, seed=30 + i)
        means.append(mean(sim[series_key][val_start:]))
    rng = max(means) - min(means) if means else 0.0
    return rng < 1.0, {"sensitivity_min": min(means), "sensitivity_max": max(means), "range": rng}


# ─── Pipeline Principal ──────────────────────────────────────────────────────

class CaseConfig:
    """Configuración de un caso de simulación."""
    def __init__(self, case_name, value_col, series_key,
                 grid_size=10, persistence_window=5,
                 synthetic_start="1980-01-01", synthetic_end="2019-01-01",
                 synthetic_split="2000-01-01",
                 real_start="1990-01-01", real_end="2022-01-01",
                 real_split="2006-01-01",
                 ode_noise=0.001, base_noise=0.001,
                 corr_threshold=0.7, threshold_factor=1.0,
                 extra_base_params=None):
        self.case_name = case_name
        self.value_col = value_col
        self.series_key = series_key
        self.grid_size = grid_size
        self.persistence_window = persistence_window
        self.synthetic_start = synthetic_start
        self.synthetic_end = synthetic_end
        self.synthetic_split = synthetic_split
        self.real_start = real_start
        self.real_end = real_end
        self.real_split = real_split
        self.ode_noise = ode_noise
        self.base_noise = base_noise
        self.corr_threshold = corr_threshold
        self.threshold_factor = threshold_factor
        self.extra_base_params = extra_base_params or {}


def evaluate_phase(config, df, start_date, end_date, split_date,
                   simulate_abm_fn, simulate_ode_fn,
                   synthetic_meta=None, param_grid=None):
    """Evalúa una fase completa (sintética o real)."""
    phase_name = "synthetic" if synthetic_meta else "real"

    if df.empty or len(df) < 10:
        return _empty_phase(phase_name, start_date, end_date, split_date, "Datos insuficientes")

    # Normalización
    obs_raw = df[config.value_col].tolist()
    obs_mean_raw = float(np.mean(obs_raw))
    obs_std_raw = float(np.std(obs_raw)) if obs_raw else 0.0

    df = df.copy()
    train_df_raw = df[df["date"] < split_date]
    val_df_raw = df[df["date"] >= split_date]

    if train_df_raw.empty or val_df_raw.empty:
        return _empty_phase(phase_name, start_date, end_date, split_date, "Split vacío")

    train_mean = float(np.mean(train_df_raw[config.value_col]))
    train_std = float(np.std(train_df_raw[config.value_col]))
    if train_std > 1e-10:
        df[config.value_col + "_z"] = (df[config.value_col] - train_mean) / train_std
    else:
        df[config.value_col + "_z"] = 0.0

    zcol = config.value_col + "_z"
    train_df = df[df["date"] < split_date]
    val_df = df[df["date"] >= split_date]
    obs = df[zcol].tolist()
    obs_val = val_df[zcol].tolist() if not val_df.empty else []
    if not obs_val:
        return _empty_phase(phase_name, start_date, end_date, split_date, "Validación vacía")

    steps = len(obs)
    val_start = len(train_df)
    obs_std = variance(obs_val) ** 0.5

    # Forcing
    forcing_trend, trend_params = build_forcing_from_training(obs[:val_start], steps)
    lag_forcing = [obs[0]] + obs[:-1]
    forcing_series = [forcing_trend[i] + 0.5 * lag_forcing[i] for i in range(steps)]

    # Parámetros base
    base_params = {
        "grid_size": config.grid_size,
        "diffusion": 0.2,
        "noise": config.base_noise,
        "macro_coupling": 0.2,
        "forcing_series": forcing_series,
        "forcing_scale": 0.05,
        "damping": 0.02,
        "p0": obs[0],
        "c0": obs[0],
        "p0_ode": obs[0],
        "t0": obs[0],
        "x0": obs[0],
        "e0": obs[0],
        "m0": obs[0],
        "w0": obs[0],
        "d0": obs[0],
        "f0": obs[0],
        "a0": obs[0],
        "h0": 0.5,
        "s0": 0.999, "i0": 0.0, "r0": 0.0,
        "ode_alpha": 0.05,
        "ode_beta": 0.02,
        "ode_noise": config.ode_noise,
        "assimilation_strength": 0.0,
        "assimilation_series": None,
    }
    base_params.update(config.extra_base_params)

    # Calibración ODE
    alpha, beta = calibrate_ode(obs[:val_start], forcing_series[:val_start])
    base_params["ode_alpha"] = alpha
    base_params["ode_beta"] = beta

    # Calibración ABM
    best_abm, best_err, top_5 = calibrate_abm(
        obs[:val_start], base_params, val_start, simulate_abm_fn,
        param_grid=param_grid, seed=2
    )
    base_params.update(best_abm)

    # Parámetros de evaluación (sin assimilación)
    eval_params = dict(base_params)
    eval_params["assimilation_strength"] = 0.0
    eval_params["assimilation_series"] = None

    # Simulaciones
    abm = simulate_abm_fn(eval_params, steps, seed=2)
    ode = simulate_ode_fn(eval_params, steps, seed=3)

    # Modelo reducido (sin acoplamiento macro)
    reduced_params = dict(eval_params)
    reduced_params["macro_coupling"] = 0.0
    reduced_params["forcing_scale"] = 0.0
    abm_reduced = simulate_abm_fn(reduced_params, steps, seed=4)

    sk = config.series_key
    ode_key = _get_ode_key(ode)
    abm_val = abm[sk][val_start:]
    ode_val = ode[ode_key][val_start:]
    reduced_val = abm_reduced[sk][val_start:]

    # Errores
    err_abm = rmse(abm_val, obs_val)
    err_ode = rmse(ode_val, obs_val)
    err_reduced = rmse(reduced_val, obs_val)

    # EDI con bootstrap
    edi_val = compute_edi(err_abm, err_reduced)
    edi_mean, edi_lo, edi_hi = bootstrap_edi(obs_val, abm_val, reduced_val)

    # Effective Information
    ei = effective_information(obs_val, abm_val, reduced_val)

    # C1-C5
    c1, c1_detail = evaluate_c1(abm_val, ode_val, obs_val, obs_std,
                                 config.threshold_factor, config.corr_threshold)
    c2, c2_detail = evaluate_c2(base_params, eval_params, steps, val_start,
                                 simulate_abm_fn, sk)
    c3, c3_detail = evaluate_c3(eval_params, steps, val_start, simulate_abm_fn,
                                 sk, window=config.persistence_window)
    c4, c4_detail = evaluate_c4(eval_params, base_params, steps, val_start,
                                 simulate_abm_fn, sk)
    c5, c5_detail = evaluate_c5(base_params, eval_params, steps, val_start,
                                 simulate_abm_fn, sk)

    # Symploké, non-locality, persistence
    internal, external = internal_vs_external_cohesion(abm.get("grid", []), abm.get("forcing", []))
    cr = cohesion_ratio(internal, external)
    sym_ok = internal > external
    dom = dominance_share(abm.get("grid", []))
    non_local_ok = dom < 0.05
    obs_persistence = window_variance(obs_val, config.persistence_window)
    model_persistence = window_variance(abm[sk][val_start:], config.persistence_window)
    persist_ok = model_persistence < 5.0 * max(obs_persistence, 0.001)

    # Emergencia
    emergence_threshold = 0.2 * max(obs_std, 0.01)
    emergence_ok = (err_reduced - err_abm) > emergence_threshold

    # Coupling check
    coupling_ok = base_params.get("macro_coupling", 0) >= 0.1
    # RMSE fraud check
    rmse_fraud = err_abm < 1e-10
    # EDI thresholds
    edi_valid = 0.30 <= edi_val <= 0.90
    cr_valid = cr > 2.0

    overall = all([c1, c2, c3, c4, c5, sym_ok, non_local_ok, persist_ok,
                   emergence_ok, coupling_ok, not rmse_fraud])

    results = {
        "phase": phase_name,
        "overall_pass": overall,
        "data": {
            "start": start_date,
            "end": end_date,
            "split": split_date,
            "obs_mean_raw": obs_mean_raw,
            "obs_std_raw": obs_std_raw,
            "steps": steps,
            "val_steps": len(obs_val),
            "coverage": len(df) / max(1, len(pd.date_range(start=start_date, end=end_date, freq="YS"))),
        },
        "calibration": {
            "forcing_scale": base_params["forcing_scale"],
            "macro_coupling": base_params["macro_coupling"],
            "damping": base_params.get("damping", 0.0),
            "ode_alpha": alpha,
            "ode_beta": beta,
            "assimilation_strength": 0.0,
            "calibration_rmse": best_err,
        },
        "errors": {
            "rmse_abm": err_abm,
            "rmse_ode": err_ode,
            "rmse_reduced": err_reduced,
            "threshold": config.threshold_factor * max(obs_std, 0.1),
        },
        "correlations": {
            "abm_obs": c1_detail["corr_abm"],
            "ode_obs": c1_detail["corr_ode"],
        },
        "edi": {
            "value": edi_val,
            "bootstrap_mean": edi_mean,
            "ci_lo": edi_lo,
            "ci_hi": edi_hi,
            "valid": edi_valid,
        },
        "effective_information": ei,
        "symploke": {
            "internal": internal,
            "external": external,
            "cr": cr,
            "pass": sym_ok,
            "cr_valid": cr_valid,
        },
        "non_locality": {
            "dominance_share": dom,
            "pass": non_local_ok,
        },
        "persistence": {
            "model": model_persistence,
            "obs": obs_persistence,
            "pass": persist_ok,
        },
        "emergence": {
            "err_reduced": err_reduced,
            "err_abm": err_abm,
            "threshold": emergence_threshold,
            "pass": emergence_ok,
            "significance": "computed",
        },
        "coupling_check": coupling_ok,
        "rmse_fraud_check": not rmse_fraud,
        "c1_convergence": c1,
        "c2_robustness": c2,
        "c3_replication": c3,
        "c4_validity": c4,
        "c5_uncertainty": c5,
        "c1_detail": c1_detail,
        "c2_detail": c2_detail,
        "c3_detail": c3_detail,
        "c4_detail": c4_detail,
        "c5_detail": c5_detail,
    }

    if synthetic_meta:
        results["synthetic_meta"] = synthetic_meta

    return results


def _get_ode_key(ode_result):
    for k in ["p", "share", "price", "tbar", "x", "e", "m", "w", "incidence"]:
        if k in ode_result:
            return k
    return list(ode_result.keys())[0]


def _empty_phase(phase_name, start, end, split, reason):
    return {
        "phase": phase_name,
        "overall_pass": False,
        "error": reason,
        "data": {"start": start, "end": end, "split": split},
        "edi": {"value": 0.0, "bootstrap_mean": 0.0, "ci_lo": 0.0, "ci_hi": 0.0, "valid": False},
        "c1_convergence": False, "c2_robustness": False,
        "c3_replication": False, "c4_validity": False, "c5_uncertainty": False,
    }


# ─── Run Completo ─────────────────────────────────────────────────────────────

def run_full_validation(config, load_real_data_fn, make_synthetic_fn,
                        simulate_abm_fn, simulate_ode_fn,
                        param_grid=None):
    """
    Ejecuta validación completa: sintético → real (con gating).
    Retorna dict con ambas fases + metadata.
    """
    # Fase sintética
    synth_df, synth_meta = make_synthetic_fn(
        config.synthetic_start, config.synthetic_end, seed=101
    )
    synthetic = evaluate_phase(
        config, synth_df, config.synthetic_start, config.synthetic_end,
        config.synthetic_split, simulate_abm_fn, simulate_ode_fn,
        synthetic_meta=synth_meta, param_grid=param_grid
    )

    # Fase real
    real_df = load_real_data_fn(config.real_start, config.real_end)
    real = evaluate_phase(
        config, real_df, config.real_start, config.real_end,
        config.real_split, simulate_abm_fn, simulate_ode_fn,
        param_grid=param_grid
    )

    # Gating: si sintético falla, real falla
    if not synthetic.get("overall_pass", False):
        real["overall_pass"] = False
        real["gated_by_synthetic"] = True

    return {
        "case": config.case_name,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "git": _get_git_info(),
        "phases": {"synthetic": synthetic, "real": real},
    }


def write_outputs(results, output_dir):
    """Escribe metrics.json y report.md."""
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "metrics.json"), "w") as f:
        json.dump(results, f, indent=2, default=_default)

    with open(os.path.join(output_dir, "report.md"), "w") as f:
        f.write(f"# Reporte de Validación — {results.get('case', 'N/A')}\n\n")
        f.write(f"- generated_at: {results['generated_at']}\n\n")

        for label, phase in results.get("phases", {}).items():
            f.write(f"## Fase {label}\n")
            f.write(f"- **overall_pass**: {phase.get('overall_pass', 'N/A')}\n\n")

            if "edi" in phase:
                edi = phase["edi"]
                f.write(f"### EDI\n")
                f.write(f"- valor: {edi.get('value', 0):.4f}\n")
                f.write(f"- bootstrap_mean: {edi.get('bootstrap_mean', 0):.4f}\n")
                f.write(f"- CI 95%: [{edi.get('ci_lo', 0):.4f}, {edi.get('ci_hi', 0):.4f}]\n")
                f.write(f"- válido (0.30-0.90): {edi.get('valid', False)}\n\n")

            if "symploke" in phase:
                s = phase["symploke"]
                f.write(f"### Symploké y CR\n")
                f.write(f"- internal: {s.get('internal', 0):.4f}\n")
                f.write(f"- external: {s.get('external', 0):.4f}\n")
                f.write(f"- CR: {s.get('cr', 0):.4f}\n")
                f.write(f"- CR válido (>2.0): {s.get('cr_valid', False)}\n\n")

            f.write(f"### Criterios C1-C5\n")
            for c in ["c1_convergence", "c2_robustness", "c3_replication",
                       "c4_validity", "c5_uncertainty"]:
                f.write(f"- {c}: {phase.get(c, 'N/A')}\n")
            f.write("\n")

            if "errors" in phase:
                f.write(f"### Errores\n")
                for k, v in phase["errors"].items():
                    f.write(f"- {k}: {v:.4f}\n" if isinstance(v, float) else f"- {k}: {v}\n")
                f.write("\n")

            if "calibration" in phase:
                f.write(f"### Calibración\n")
                for k, v in phase["calibration"].items():
                    f.write(f"- {k}: {v:.4f}\n" if isinstance(v, float) else f"- {k}: {v}\n")
                f.write("\n")


def _get_git_info():
    try:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        commit = subprocess.check_output(
            ["git", "-C", repo_root, "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        status = subprocess.check_output(
            ["git", "-C", repo_root, "status", "--porcelain"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        return {"commit": commit, "dirty": bool(status)}
    except Exception:
        return {"commit": None, "dirty": None}


def _default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if hasattr(obj, "tolist"):
        return obj.tolist()
    return str(obj)
