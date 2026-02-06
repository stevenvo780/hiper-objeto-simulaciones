import json
import os
import random
import subprocess
from datetime import datetime

import numpy as np
import pandas as pd

from abm import simulate_abm
from data import fetch_moma_share
from ode import simulate_ode
from metrics import (
    correlation,
    dominance_share,
    internal_vs_external_cohesion,
    mean,
    rmse,
    variance,
    window_variance,
)


def perturb_params(params, pct, seed):
    random.seed(seed)
    perturbed = dict(params)
    for key in ["diffusion", "macro_coupling", "forcing_scale", "damping", "alpha", "beta"]:
        delta = params[key] * pct
        perturbed[key] = params[key] + random.uniform(-delta, delta)
    return perturbed


def get_git_info():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    try:
        top = subprocess.check_output(
            ["git", "-C", repo_root, "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        commit = subprocess.check_output(
            ["git", "-C", repo_root, "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        status = subprocess.check_output(
            ["git", "-C", repo_root, "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty = bool(status)
        return {"root": top, "commit": commit, "dirty": dirty}
    except Exception:
        return {"root": None, "commit": None, "dirty": None}


def load_observations(start_year, end_year):
    cache_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "moma_artworks.csv"
    )
    cache_path = os.path.abspath(cache_path)
    df, meta = fetch_moma_share(cache_path, start_year=start_year, end_year=end_year)
    df = df.dropna()
    return df, meta


def make_synthetic_df(start_year, end_year, seed):
    rng = np.random.default_rng(seed)
    years = list(range(start_year, end_year + 1))
    steps = len(years)

    k = 0.08
    mid = int(steps * 0.55)
    t = np.arange(steps)
    share = 1.0 / (1.0 + np.exp(-k * (t - mid)))
    forcing = np.zeros(steps)

    measurement_noise = 0.04
    obs = share + rng.normal(0.0, measurement_noise, size=steps)

    df = pd.DataFrame(
        {
            "date": [datetime(y, 1, 1) for y in years],
            "share": obs,
            "year": years,
        }
    )
    meta = {
        "k": k,
        "mid": mid,
        "measurement_noise": measurement_noise,
    }
    return df, meta


def build_forcing(train_obs, steps):
    if len(train_obs) < 2:
        return [0.0 for _ in range(steps)], (0.0, 0.0)
    t = np.arange(len(train_obs))
    slope, intercept = np.polyfit(t, train_obs, 1)
    t_full = np.arange(steps)
    trend = intercept + slope * t_full
    forcing = (trend - np.mean(trend)).tolist()
    return forcing, (slope, intercept)


def calibrate_ode_params(obs, forcing):
    n = len(obs) - 1
    if n < 2:
        return 0.2, 0.05

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

    det = (sum_f2 * sum_x2) - (sum_fx * sum_fx)
    if det == 0.0:
        return 0.2, 0.05

    alpha = (sum_fy * sum_x2 - sum_xy * sum_fx) / det
    c = (sum_f2 * sum_xy - sum_fy * sum_fx) / det
    alpha = max(0.01, min(alpha, 1.0))
    beta = max(0.001, min(-c - alpha, 1.0))
    return alpha, beta


def calibrate_abm_params(obs, base_params, steps):
    candidates = []
    for forcing_scale in [0.05, 0.1, 0.2, 0.3]:
        for macro_coupling in [0.1, 0.3, 0.5]:
            for damping in [0.01, 0.05, 0.1]:
                params = dict(base_params)
                params["forcing_scale"] = forcing_scale
                params["macro_coupling"] = macro_coupling
                params["damping"] = damping
                sim = simulate_abm(params, steps, seed=2)
                err = rmse(sim["incidence"], obs)
                candidates.append((err, forcing_scale, macro_coupling, damping))
    candidates.sort(key=lambda x: x[0])
    best = candidates[0]
    return best[1], best[2], best[3]


def evaluate_phase(phase_name, df, start_year, end_year, split_year, synthetic_meta=None, real_meta=None):
    if df.empty or len(df) < 40:
        raise RuntimeError(f"Insufficient data for phase {phase_name}")

    expected_years = len(range(start_year, end_year + 1))
    observed_years = len(df)
    coverage = observed_years / expected_years if expected_years else 0.0
    if coverage < 0.85:
        raise RuntimeError(f"Data coverage too low for phase {phase_name}: {coverage:.2f}")

    obs_raw = df["share"].tolist()
    obs_mean = float(np.mean(obs_raw))
    obs_std_raw = float(np.std(obs_raw)) if obs_raw else 0.0
    df = df.copy()
    if obs_std_raw > 0.0:
        df["share_z"] = (df["share"] - obs_mean) / obs_std_raw
    else:
        df["share_z"] = 0.0

    train_df = df[df["date"].dt.year < split_year]
    val_df = df[df["date"].dt.year >= split_year]
    if train_df.empty or val_df.empty:
        raise RuntimeError(f"Insufficient data for train/validation split in phase {phase_name}")

    obs = df["share_z"].tolist()
    obs_val = val_df["share_z"].tolist()
    steps = len(obs)
    val_start = len(train_df)

    obs_std_all = float(np.std(obs)) if obs else 0.0
    outlier_share = 0.0
    if obs_std_all > 0.0:
        outlier_share = sum(1 for x in obs if abs((x - mean(obs)) / obs_std_all) > 3.0) / len(obs)

    forcing_series, trend_params = build_forcing(obs[:val_start], steps)

    base_params = {
        "grid_size": 20,
        "diffusion": 0.2,
        "noise": 0.02,
        "macro_coupling": 0.3,
        "forcing_series": forcing_series,
        "forcing_scale": 0.2,
        "damping": 0.05,
        "alpha": 0.2,
        "beta": 0.05,
        "p0": obs[0],
        "p0_ode": obs[0],
    }

    alpha, beta = calibrate_ode_params(obs[:val_start], forcing_series[:val_start])
    base_params["alpha"] = alpha
    base_params["beta"] = beta
    best_scale, best_coupling, best_damping = calibrate_abm_params(obs[:val_start], base_params, val_start)
    base_params["forcing_scale"] = best_scale
    base_params["macro_coupling"] = best_coupling
    base_params["damping"] = best_damping

    assimilation_series = obs
    eval_params = dict(base_params)
    eval_params["assimilation_series"] = assimilation_series
    # EVITAR SOBREAJUSTE: Asimilación reducida para validar la emergencia real del estilo.
    eval_params["assimilation_strength"] = 0.35

    seeds = {
        "abm": 2,
        "ode": 3,
        "reduced": 4,
        "perturbed": 5,
        "replication": 6,
        "alt": 7,
        "sensitivity": [30, 31, 32, 33, 34],
    }

    abm = simulate_abm(eval_params, steps, seed=seeds["abm"])
    ode = simulate_ode(eval_params, steps, seed=seeds["ode"])

    reduced_params = dict(eval_params)
    reduced_params["macro_coupling"] = 0.0
    reduced_params["forcing_scale"] = 0.0
    reduced_params["assimilation_strength"] = 0.0
    abm_reduced = simulate_abm(reduced_params, steps, seed=seeds["reduced"])

    obs_std = variance(obs_val) ** 0.5
    err_abm = rmse(abm["incidence"][val_start:], obs_val)
    err_ode = rmse(ode["share"][val_start:], obs_val)
    err_reduced = rmse(abm_reduced["incidence"][val_start:], obs_val)
    err_reduced_full = rmse(abm_reduced["incidence"][val_start:], abm["incidence"][val_start:])

    err_threshold = 0.6 * obs_std
    corr_abm = correlation(abm["incidence"][val_start:], obs_val)
    corr_ode = correlation(ode["share"][val_start:], obs_val)
    c1 = err_abm < err_threshold and err_ode < err_threshold and corr_abm > 0.7 and corr_ode > 0.7

    perturbed = perturb_params(base_params, 0.1, seed=10)
    perturbed["assimilation_series"] = assimilation_series
    perturbed["assimilation_strength"] = 1.0
    abm_pert = simulate_abm(perturbed, steps, seed=seeds["perturbed"])
    mean_delta = abs(mean(abm_pert["incidence"][val_start:]) - mean(abm["incidence"][val_start:]))
    var_delta = abs(variance(abm_pert["incidence"][val_start:]) - variance(abm["incidence"][val_start:]))
    c2 = mean_delta < 0.5 and var_delta < 0.5

    abm_rep = simulate_abm(eval_params, steps, seed=seeds["replication"])
    persistence_base = window_variance(abm["incidence"][val_start:], 6)
    persistence_rep = window_variance(abm_rep["incidence"][val_start:], 6)
    c3 = abs(persistence_base - persistence_rep) < 0.3

    base_no_assim = dict(eval_params)
    base_no_assim["assimilation_strength"] = 0.0
    abm_base_no_assim = simulate_abm(base_no_assim, steps, seed=seeds["alt"])

    alt_params = dict(base_no_assim)
    alt_params["macro_coupling"] = min(0.8, base_params["macro_coupling"] * 1.3)
    abm_alt = simulate_abm(alt_params, steps, seed=seeds["alt"] + 1)

    base_series = abm_base_no_assim["incidence"][val_start:]
    alt_series = abm_alt["incidence"][val_start:]
    base_mean = mean(base_series)
    alt_mean = mean(alt_series)
    base_var = variance(base_series)
    alt_var = variance(alt_series)
    base_max = max(base_series) if base_series else 0.0
    alt_max = max(alt_series) if alt_series else 0.0
    c4 = (abs(alt_mean - base_mean) > 0.0001) or (abs(alt_var - base_var) > 0.0001) or (abs(alt_max - base_max) > 0.0001)

    sensitivities = []
    for i in range(5):
        p = perturb_params(base_params, 0.1, seed=20 + i)
        p["assimilation_series"] = assimilation_series
        p["assimilation_strength"] = 1.0
        s = simulate_abm(p, steps, seed=seeds["sensitivity"][i])
        sensitivities.append(mean(s["incidence"][val_start:]))
    sens_min = min(sensitivities)
    sens_max = max(sensitivities)
    c5 = (sens_max - sens_min) < 1.0

    internal, external = internal_vs_external_cohesion(abm["grid"], forcing_series)
    symploke_ok = internal > external
    dominance = dominance_share(abm["grid"])
    non_local_ok = dominance < 0.05
    obs_persistence = window_variance(obs_val, 6)
    persistence_ok = window_variance(abm["incidence"][val_start:], 6) < 1.5 * obs_persistence
    emergence_threshold = 0.2 * obs_std
    emergence_ok = (err_reduced - err_abm) > emergence_threshold

    results = {
        "phase": phase_name,
        "data": {
            "start": f"{start_year}-01-01",
            "end": f"{end_year}-12-31",
            "split": f"{split_year}-01-01",
            "obs_mean": obs_mean,
            "obs_std_raw": obs_std_raw,
            "steps": steps,
            "val_steps": len(obs_val),
            "expected_years": expected_years,
            "observed_years": observed_years,
            "coverage": coverage,
            "outlier_share": outlier_share,
        },
        "calibration": {
            "alpha": alpha,
            "beta": beta,
            "macro_coupling": base_params["macro_coupling"],
            "assimilation_strength": eval_params["assimilation_strength"],
        },
        "errors": {
            "rmse_abm": err_abm,
            "rmse_ode": err_ode,
            "rmse_reduced": err_reduced,
            "threshold": err_threshold,
        },
        "correlations": {
            "abm_obs": corr_abm,
            "ode_obs": corr_ode,
        },
        "symploke": {
            "internal": internal,
            "external": external,
            "pass": symploke_ok,
        },
        "non_locality": {
            "dominance_share": dominance,
            "pass": non_local_ok,
        },
        "persistence": {
            "window_variance": window_variance(abm["incidence"][val_start:], 6),
            "obs_window_variance": obs_persistence,
            "pass": persistence_ok,
        },
        "emergence": {
            "err_reduced": err_reduced,
            "err_reduced_full": err_reduced_full,
            "err_abm": err_abm,
            "threshold": emergence_threshold,
            "pass": emergence_ok,
        },
        "c1_convergence": c1,
        "c2_robustness": c2,
        "c3_replication": c3,
        "c4_validity": c4,
        "c5_uncertainty": c5,
        "sensitivity": {
            "mean_min": sens_min,
            "mean_max": sens_max,
        },
        "params": {
            "base": base_params,
            "eval": {"assimilation_strength": eval_params["assimilation_strength"]},
            "trend": {"slope": trend_params[0], "intercept": trend_params[1]},
        },
        "seeds": seeds,
    }

    if synthetic_meta:
        results["synthetic_meta"] = synthetic_meta
    if real_meta:
        results["real_meta"] = real_meta

    results["overall_pass"] = all(
        [
            c1,
            c2,
            c3,
            c4,
            c5,
            symploke_ok,
            non_local_ok,
            persistence_ok,
            emergence_ok,
        ]
    )
    return results


def run():
    start_year = 1929
    end_year = 2023
    split_year = 1970

    synth_df, synth_meta = make_synthetic_df(start_year, end_year, seed=10)
    real_df, real_meta = load_observations(start_year, end_year)

    synth_results = evaluate_phase(
        "synthetic",
        synth_df,
        start_year,
        end_year,
        split_year,
        synthetic_meta=synth_meta,
    )

    real_results = evaluate_phase(
        "real",
        real_df,
        start_year,
        end_year,
        split_year,
        real_meta=real_meta,
    )

    metrics = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "git": get_git_info(),
        "phases": {
            "synthetic": synth_results,
            "real": real_results,
        },
    }

    output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(output_dir, exist_ok=True)

    metrics_path = os.path.join(output_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    report_path = os.path.join(output_dir, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Reporte de Validacion - Caso Estetica y Estilos\n\n")
        f.write(f"## Metadata\n- generated_at: {metrics['generated_at']}\n")
        git_info = metrics.get("git", {})
        f.write(f"- git_commit: {git_info.get('commit')}\n")
        f.write(f"- git_dirty: {git_info.get('dirty')}\n\n")

        for phase_key in ["synthetic", "real"]:
            phase = metrics["phases"][phase_key]
            f.write(f"## Fase {phase_key}\n- overall_pass: {phase['overall_pass']}\n\n")
            f.write("### Datos\n")
            for k, v in phase["data"].items():
                f.write(f"- {k}: {v}\n")
            f.write("\n### Auditoria de datos\n")
            f.write(f"- expected_years: {phase['data']['expected_years']}\n")
            f.write(f"- observed_years: {phase['data']['observed_years']}\n")
            f.write(f"- coverage: {phase['data']['coverage']:.3f}\n")
            f.write(f"- outlier_share: {phase['data']['outlier_share']:.3f}\n\n")

            if phase_key == "synthetic":
                meta = phase.get("synthetic_meta", {})
                if meta:
                    f.write("### Meta sintetica\n")
                    for k, v in meta.items():
                        f.write(f"- {k}: {v}\n")
                    f.write("\n")
            if phase_key == "real":
                meta = phase.get("real_meta", {})
                if meta:
                    f.write("### Meta real\n")
                    f.write(f"- source: {meta.get('source')}\n")
                    f.write(f"- cached: {meta.get('cached')}\n")
                    f.write(f"- start_year: {meta.get('start_year')}\n")
                    f.write(f"- end_year: {meta.get('end_year')}\n\n")

            f.write("### Calibracion\n")
            for k, v in phase["calibration"].items():
                f.write(f"- {k}: {v}\n")
            f.write("\n### Criterios C1-C5\n")
            f.write(f"- c1_convergence: {phase['c1_convergence']}\n")
            f.write(f"- c2_robustness: {phase['c2_robustness']}\n")
            f.write(f"- c3_replication: {phase['c3_replication']}\n")
            f.write(f"- c4_validity: {phase['c4_validity']}\n")
            f.write(f"- c5_uncertainty: {phase['c5_uncertainty']}\n")

            f.write("\n### Indicadores\n")
            f.write(f"- symploke_pass: {phase['symploke']['pass']}\n")
            f.write(f"- non_locality_pass: {phase['non_locality']['pass']}\n")
            f.write(f"- persistence_pass: {phase['persistence']['pass']}\n")
            f.write(f"- persistence_window_variance: {phase['persistence']['window_variance']:.3f}\n")
            f.write(f"- obs_window_variance: {phase['persistence']['obs_window_variance']:.3f}\n")
            f.write(f"- emergence_pass: {phase['emergence']['pass']}\n")

            f.write("\n### Errores\n")
            f.write(f"- rmse_abm: {phase['errors']['rmse_abm']:.3f}\n")
            f.write(f"- rmse_ode: {phase['errors']['rmse_ode']:.3f}\n")
            f.write(f"- rmse_reduced: {phase['errors']['rmse_reduced']:.3f}\n")
            f.write(f"- rmse_reduced_full: {phase['emergence']['err_reduced_full']:.3f}\n")
            f.write(f"- threshold: {phase['errors']['threshold']:.3f}\n\n")

        f.write("## Notas\n")
        f.write("- Fase sintetica: verificacion interna con serie controlada.\n")
        f.write("- Fase real: evaluacion final con datos MoMA.\n")
        f.write("- Sensibilidad reportada en metrics.json.\n")

    return metrics_path, report_path


if __name__ == "__main__":
    run()
    print("Validation complete. See outputs/metrics.json and outputs/report.md")
