import json
import os
import random
import subprocess
from datetime import datetime

import numpy as np
import pandas as pd

from abm import simulate_abm
from data import fetch_opsd_load_monthly
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
    for key in ["diffusion", "macro_coupling", "forcing_base", "forcing_trend"]:
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


def load_observations(start_date, end_date):
    cache_path = os.path.join(os.path.dirname(__file__), "..", "data", "opsd_load_monthly.csv")
    cache_path = os.path.abspath(cache_path)
    df = fetch_opsd_load_monthly(start_date, end_date, cache_path=cache_path)
    df = df.dropna()
    return df


def make_synthetic_df(start_date, end_date, seed):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start_date, end=end_date, freq="MS")
    steps = len(dates)

    forcing_base = 0.0
    forcing_trend = 0.002
    forcing_seasonal_amp = 0.3
    forcing_seasonal_period = 12

    forcing = []
    for t in range(steps):
        seasonal = forcing_seasonal_amp * np.sin(2.0 * np.pi * t / forcing_seasonal_period)
        forcing.append(forcing_base + forcing_trend * t + seasonal)

    true_params = {
        "e0": 0.0,
        "ode_alpha": 0.08,
        "ode_beta": 0.03,
        "ode_noise": 0.02,
        "forcing_series": forcing,
    }

    sim = simulate_ode(true_params, steps, seed=seed + 1)
    measurement_noise = 0.03
    obs = np.array(sim["e"]) + rng.normal(0.0, measurement_noise, size=steps)

    df = pd.DataFrame({"date": dates, "demand": obs})
    meta = {
        "forcing_base": forcing_base,
        "forcing_trend": forcing_trend,
        "forcing_seasonal_amp": forcing_seasonal_amp,
        "forcing_seasonal_period": forcing_seasonal_period,
        "ode_true": {"alpha": true_params["ode_alpha"], "beta": true_params["ode_beta"], "noise": true_params["ode_noise"]},
        "measurement_noise": measurement_noise,
    }
    return df, meta


def build_forcing(train_df, full_df, value_col):
    train_df = train_df.copy()
    train_df["month"] = train_df["date"].dt.month
    seasonal = train_df.groupby("month")[value_col].mean()
    seasonal_map = seasonal.to_dict()

    t = np.arange(len(train_df))
    y = train_df[value_col].values
    slope, intercept = np.polyfit(t, y, 1)

    full_df = full_df.copy()
    full_df["month"] = full_df["date"].dt.month
    t_full = np.arange(len(full_df))
    trend_full = intercept + slope * t_full
    forcing = np.array([seasonal_map[m] for m in full_df["month"]]) + trend_full
    return forcing.tolist(), (slope, intercept)


def calibrate_abm_params(obs, base_params, steps):
    candidates = []
    for forcing_scale in [0.01, 0.03, 0.05, 0.1, 0.2]:
        for macro_coupling in [0.0, 0.2, 0.4]:
            for damping in [0.0, 0.02, 0.05]:
                params = dict(base_params)
                params["forcing_scale"] = forcing_scale
                params["macro_coupling"] = macro_coupling
                params["damping"] = damping
                sim = simulate_abm(params, steps, seed=2)
                err = rmse(sim["e"], obs)
                candidates.append((err, forcing_scale, macro_coupling, damping))
    candidates.sort(key=lambda x: x[0])
    best = candidates[0]
    return best[1], best[2], best[3]


def calibrate_ode_params(obs, forcing):
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

    det = (sum_f2 * sum_x2) - (sum_fx * sum_fx)
    if det == 0.0:
        return 0.05, 0.02

    a = (sum_fy * sum_x2 - sum_xy * sum_fx) / det
    b = (sum_f2 * sum_xy - sum_fy * sum_fx) / det
    alpha = max(0.001, min(a, 0.5))
    beta = 0.02
    if alpha != 0.0:
        beta = max(0.001, min(-b / alpha, 1.0))
    return alpha, beta


def evaluate_phase(phase_name, df, start_date, end_date, split_date, synthetic_meta=None):
    if df.empty or len(df) < 24:
        raise RuntimeError(f"Insufficient data for phase {phase_name}")

    expected_months = len(pd.date_range(start=start_date, end=end_date, freq="MS"))
    observed_months = len(df)
    coverage = observed_months / expected_months if expected_months else 0.0
    if coverage < 0.85:
        raise RuntimeError(f"Data coverage too low for phase {phase_name}: {coverage:.2f}")

    obs_raw = df["demand"].tolist()
    obs_mean = float(np.mean(obs_raw))
    obs_std_raw = float(np.std(obs_raw)) if obs_raw else 0.0
    df = df.copy()
    if obs_std_raw > 0.0:
        df["demand_z"] = (df["demand"] - obs_mean) / obs_std_raw
    else:
        df["demand_z"] = 0.0

    train_df = df[df["date"] < split_date]
    val_df = df[df["date"] >= split_date]
    if train_df.empty or val_df.empty:
        raise RuntimeError(f"Insufficient data for train/validation split in phase {phase_name}")

    obs = df["demand_z"].tolist()
    obs_val = val_df["demand_z"].tolist()
    steps = len(obs)
    val_start = len(train_df)

    obs_std_all = float(np.std(obs)) if obs else 0.0
    outlier_share = 0.0
    if obs_std_all > 0.0:
        outlier_share = sum(1 for x in obs if abs((x - mean(obs)) / obs_std_all) > 3.0) / len(obs)

    seasonal_trend, trend_params = build_forcing(train_df, df, "demand_z")
    lag_forcing = [obs[0]] + obs[:-1]
    forcing_series = [seasonal_trend[i] + 0.5 * lag_forcing[i] for i in range(steps)]

    base_params = {
        "grid_size": 10,
        "diffusion": 0.2,
        "noise": 0.02,
        "macro_coupling": 0.4,
        "d0": obs[0],
        "e0": obs[0],
        "forcing_series": forcing_series,
        "forcing_scale": 0.02,
        "damping": 0.05,
        "demand_scale": 0.05,
        "forcing_base": 1.0,
        "forcing_trend": 0.005,
        "ode_alpha": 0.05,
        "ode_beta": 0.02,
        "ode_noise": 0.02,
    }

    forcing_train = base_params["forcing_series"][:val_start]
    alpha, beta = calibrate_ode_params(obs[:val_start], forcing_train)
    base_params["ode_alpha"] = alpha
    base_params["ode_beta"] = beta
    best_scale, best_coupling, best_damping = calibrate_abm_params(obs[:val_start], base_params, val_start)
    base_params["forcing_scale"] = best_scale
    base_params["macro_coupling"] = best_coupling
    base_params["damping"] = best_damping

    assimilation_series = obs
    eval_params = dict(base_params)
    eval_params["assimilation_series"] = None
    eval_params["assimilation_strength"] = 0.0

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
    err_abm = rmse(abm["e"][val_start:], obs_val)
    err_ode = rmse(ode["e"][val_start:], obs_val)
    err_reduced = rmse(abm_reduced["e"][val_start:], obs_val)
    err_reduced_full = rmse(abm_reduced["e"][val_start:], abm["e"][val_start:])

    err_threshold = 0.6 * obs_std
    corr_abm = correlation(abm["e"][val_start:], obs_val)
    corr_ode = correlation(ode["e"][val_start:], obs_val)
    c1 = err_abm < err_threshold and err_ode < err_threshold and corr_abm > 0.7 and corr_ode > 0.7

    perturbed = perturb_params(base_params, 0.1, seed=10)
    perturbed["assimilation_series"] = None
    perturbed["assimilation_strength"] = 0.0
    abm_pert = simulate_abm(perturbed, steps, seed=seeds["perturbed"])
    mean_delta = abs(mean(abm_pert["e"][val_start:]) - mean(abm["e"][val_start:]))
    var_delta = abs(variance(abm_pert["e"][val_start:]) - variance(abm["e"][val_start:]))
    c2 = mean_delta < 0.5 and var_delta < 0.5

    abm_rep = simulate_abm(eval_params, steps, seed=seeds["replication"])
    persistence_base = window_variance(abm["e"][val_start:], 12)
    persistence_rep = window_variance(abm_rep["e"][val_start:], 12)
    c3 = abs(persistence_base - persistence_rep) < 0.3

    base_no_assim = dict(eval_params)
    base_no_assim["assimilation_strength"] = 0.0
    abm_base_no_assim = simulate_abm(base_no_assim, steps, seed=seeds["alt"])

    alt_params = dict(base_no_assim)
    alt_forcing = [x * 1.2 for x in base_params["forcing_series"]]
    alt_params["forcing_series"] = alt_forcing
    abm_alt = simulate_abm(alt_params, steps, seed=seeds["alt"] + 1)

    base_mean = mean(abm_base_no_assim["e"][val_start:])
    alt_mean = mean(abm_alt["e"][val_start:])
    c4 = abs(alt_mean - base_mean) > 0.001

    sensitivities = []
    for i in range(5):
        p = perturb_params(base_params, 0.1, seed=20 + i)
        p["assimilation_series"] = None
        p["assimilation_strength"] = 0.0
        s = simulate_abm(p, steps, seed=seeds["sensitivity"][i])
        sensitivities.append(mean(s["e"][val_start:]))
    sens_min = min(sensitivities)
    sens_max = max(sensitivities)
    c5 = (sens_max - sens_min) < 1.0

    internal, external = internal_vs_external_cohesion(abm["grid"], abm["forcing"])
    symploke_ok = internal > external
    dominance = dominance_share(abm["grid"])
    non_local_ok = dominance < 0.05
    obs_persistence = window_variance(obs_val, 12)
    persistence_ok = window_variance(abm["e"][val_start:], 12) < 1.5 * obs_persistence
    emergence_threshold = 0.2 * obs_std
    emergence_ok = (err_reduced - err_abm) > emergence_threshold

    results = {
        "phase": phase_name,
        "data": {
            "start": start_date,
            "end": end_date,
            "split": split_date,
            "obs_mean": obs_mean,
            "obs_std_raw": obs_std_raw,
            "steps": steps,
            "val_steps": len(obs_val),
            "expected_months": expected_months,
            "observed_months": observed_months,
            "coverage": coverage,
            "outlier_share": outlier_share,
        },
        "calibration": {
            "forcing_scale": base_params["forcing_scale"],
            "macro_coupling": base_params["macro_coupling"],
            "damping": base_params.get("damping", 0.0),
            "assimilation_strength": eval_params["assimilation_strength"],
            "ode_alpha": base_params["ode_alpha"],
            "ode_beta": base_params["ode_beta"],
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
            "window_variance": window_variance(abm["e"][val_start:], 12),
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
            "eval": {
                "assimilation_strength": eval_params["assimilation_strength"],
            },
        },
        "seeds": seeds,
        "overall_pass": all([c1, c2, c3, c4, c5, symploke_ok, non_local_ok, persistence_ok, emergence_ok]),
    }

    if synthetic_meta:
        results["synthetic_meta"] = synthetic_meta

    return results


def evaluate():
    synthetic_start = "2000-01-01"
    synthetic_end = "2019-12-01"
    synthetic_split = "2010-01-01"
    synth_df, synth_meta = make_synthetic_df(synthetic_start, synthetic_end, seed=101)
    synthetic = evaluate_phase(
        "synthetic",
        synth_df,
        synthetic_start,
        synthetic_end,
        synthetic_split,
        synthetic_meta=synth_meta,
    )

    real_start = "2015-01-01"
    real_end = "2020-06-30"
    real_split = "2019-01-01"
    real_df = load_observations(real_start, real_end)
    real = evaluate_phase("real", real_df, real_start, real_end, real_split)
    if not synthetic.get("overall_pass", False):
        real["overall_pass"] = False
        real["gated_by_synthetic"] = True

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "git": get_git_info(),
        "phases": {
            "synthetic": synthetic,
            "real": real,
        },
    }


def write_phase_report(f, label, results):
    f.write(f"## Fase {label}\n")
    f.write(f"- overall_pass: {results['overall_pass']}\n\n")

    f.write("### Datos\n")
    f.write(f"- start: {results['data']['start']}\n")
    f.write(f"- end: {results['data']['end']}\n")
    f.write(f"- split: {results['data']['split']}\n")
    f.write(f"- steps: {results['data']['steps']}\n")
    f.write(f"- val_steps: {results['data']['val_steps']}\n")
    f.write(f"- obs_mean: {results['data']['obs_mean']:.3f}\n")
    f.write(f"- obs_std_raw: {results['data']['obs_std_raw']:.3f}\n\n")

    f.write("### Auditoria de datos\n")
    f.write(f"- expected_months: {results['data']['expected_months']}\n")
    f.write(f"- observed_months: {results['data']['observed_months']}\n")
    f.write(f"- coverage: {results['data']['coverage']:.3f}\n")
    f.write(f"- outlier_share: {results['data']['outlier_share']:.3f}\n\n")

    if "synthetic_meta" in results:
        f.write("### Meta sintetica\n")
        f.write(f"- forcing_base: {results['synthetic_meta']['forcing_base']:.3f}\n")
        f.write(f"- forcing_trend: {results['synthetic_meta']['forcing_trend']:.4f}\n")
        f.write(f"- forcing_seasonal_amp: {results['synthetic_meta']['forcing_seasonal_amp']:.3f}\n")
        f.write(f"- forcing_seasonal_period: {results['synthetic_meta']['forcing_seasonal_period']}\n")
        f.write(f"- ode_true_alpha: {results['synthetic_meta']['ode_true']['alpha']:.3f}\n")
        f.write(f"- ode_true_beta: {results['synthetic_meta']['ode_true']['beta']:.3f}\n")
        f.write(f"- ode_true_noise: {results['synthetic_meta']['ode_true']['noise']:.3f}\n")
        f.write(f"- measurement_noise: {results['synthetic_meta']['measurement_noise']:.3f}\n\n")

    f.write("### Calibracion\n")
    f.write(f"- forcing_scale: {results['calibration']['forcing_scale']:.3f}\n")
    f.write(f"- macro_coupling: {results['calibration']['macro_coupling']:.3f}\n")
    f.write(f"- damping: {results['calibration']['damping']:.3f}\n")
    f.write(f"- assimilation_strength: {results['calibration']['assimilation_strength']:.3f}\n")
    f.write(f"- ode_alpha: {results['calibration']['ode_alpha']:.4f}\n")
    f.write(f"- ode_beta: {results['calibration']['ode_beta']:.4f}\n\n")

    f.write("### Criterios C1-C5\n")
    for key in ["c1_convergence", "c2_robustness", "c3_replication", "c4_validity", "c5_uncertainty"]:
        f.write(f"- {key}: {results[key]}\n")
    f.write("\n")

    f.write("### Indicadores\n")
    f.write(f"- symploke_pass: {results['symploke']['pass']}\n")
    f.write(f"- non_locality_pass: {results['non_locality']['pass']}\n")
    f.write(f"- persistence_pass: {results['persistence']['pass']}\n")
    f.write(f"- persistence_window_variance: {results['persistence']['window_variance']:.3f}\n")
    f.write(f"- obs_window_variance: {results['persistence']['obs_window_variance']:.3f}\n")
    f.write(f"- emergence_pass: {results['emergence']['pass']}\n\n")

    f.write("### Errores\n")
    f.write(f"- rmse_abm: {results['errors']['rmse_abm']:.3f}\n")
    f.write(f"- rmse_ode: {results['errors']['rmse_ode']:.3f}\n")
    f.write(f"- rmse_reduced: {results['errors']['rmse_reduced']:.3f}\n")
    f.write(f"- rmse_reduced_full: {results['emergence']['err_reduced_full']:.3f}\n")
    f.write(f"- threshold: {results['errors']['threshold']:.3f}\n\n")


def write_outputs(results):
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    metrics_path = os.path.join(out_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    report_path = os.path.join(out_dir, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Reporte de Validacion - Caso Energia Electrica\n\n")
        f.write("## Metadata\n")
        f.write(f"- generated_at: {results['generated_at']}\n")
        f.write(f"- git_commit: {results['git']['commit']}\n")
        f.write(f"- git_dirty: {results['git']['dirty']}\n\n")

        for label, phase in results["phases"].items():
            write_phase_report(f, label, phase)

        f.write("## Notas\n")
        f.write("- Fase sintetica: verificacion interna con serie controlada.\n")
        f.write("- Fase real: evaluacion final con datos OPSD (GB load).\n")
        f.write("- Sensibilidad reportada en metrics.json.\n")


def main():
    results = evaluate()
    write_outputs(results)
    print("Validation complete. See outputs/metrics.json and outputs/report.md")


if __name__ == "__main__":
    main()
