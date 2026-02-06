import json
import os
import random
import subprocess
from datetime import datetime

import numpy as np
import pandas as pd

from abm import simulate_abm
from data import fetch_owid_world_weekly
from ode import simulate_seir
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
    for key in ["beta", "gamma", "sigma", "macro_coupling"]:
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
    cache_path = os.path.join(os.path.dirname(__file__), "..", "data", "owid_world_weekly_cases.csv")
    cache_path = os.path.abspath(cache_path)
    df = fetch_owid_world_weekly(start_date, end_date, cache_path=cache_path)
    df = df.dropna()
    return df


def make_synthetic_df(start_date, end_date, seed):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start_date, end=end_date, freq="W")
    steps = len(dates)

    forcing = [0.0 for _ in range(steps)]

    true_params = {
        "beta": 0.25,
        "sigma": 0.2,
        "gamma": 0.1,
        "noise": 0.01,
        "forcing_series": forcing,
    }

    sim = simulate_seir(true_params, steps, seed=seed + 1)
    measurement_noise = 0.02
    obs = np.array(sim["incidence"]) + rng.normal(0.0, measurement_noise, size=steps)

    df = pd.DataFrame({"date": dates, "cases": obs})
    meta = {
        "beta": true_params["beta"],
        "sigma": true_params["sigma"],
        "gamma": true_params["gamma"],
        "measurement_noise": measurement_noise,
    }
    return df, meta


def calibrate_seir(obs):
    # Simple heuristic: set beta proportional to peak, gamma to recovery speed
    if not obs:
        return 0.2, 0.2, 0.1
    peak = max(obs)
    beta = min(0.5, max(0.05, peak * 2))
    sigma = 0.2
    gamma = 0.1
    return beta, sigma, gamma


def evaluate_phase(phase_name, df, start_date, end_date, split_date, synthetic_meta=None):
    if df.empty or len(df) < 52:
        raise RuntimeError(f"Insufficient data for phase {phase_name}")

    expected_weeks = len(pd.date_range(start=start_date, end=end_date, freq="W"))
    observed_weeks = len(df)
    coverage = observed_weeks / expected_weeks if expected_weeks else 0.0
    if coverage < 0.85:
        raise RuntimeError(f"Data coverage too low for phase {phase_name}: {coverage:.2f}")

    obs_raw = df["cases"].tolist()
    obs_mean = float(np.mean(obs_raw))
    obs_std_raw = float(np.std(obs_raw)) if obs_raw else 0.0
    df = df.copy()
    if obs_std_raw > 0.0:
        df["cases_z"] = (df["cases"] - obs_mean) / obs_std_raw
    else:
        df["cases_z"] = 0.0

    train_df = df[df["date"] < split_date]
    val_df = df[df["date"] >= split_date]
    if train_df.empty or val_df.empty:
        raise RuntimeError(f"Insufficient data for train/validation split in phase {phase_name}")

    obs = df["cases_z"].tolist()
    obs_val = val_df["cases_z"].tolist()
    steps = len(obs)
    val_start = len(train_df)

    obs_std_all = float(np.std(obs)) if obs else 0.0
    outlier_share = 0.0
    if obs_std_all > 0.0:
        outlier_share = sum(1 for x in obs if abs((x - mean(obs)) / obs_std_all) > 3.0) / len(obs)

    forcing_series = [0.0 for _ in range(steps)]

    beta, sigma, gamma = calibrate_seir(obs[:val_start])
    base_params = {
        "grid_size": 20,
        "beta": beta,
        "sigma": sigma,
        "gamma": gamma,
        "noise": 0.01,
        "macro_coupling": 0.2,
        "forcing_series": forcing_series,
    }

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
    ode = simulate_seir(eval_params, steps, seed=seeds["ode"])

    reduced_params = dict(eval_params)
    reduced_params["macro_coupling"] = 0.0
    reduced_params["forcing_scale"] = 0.0
    reduced_params["assimilation_strength"] = 0.0
    abm_reduced = simulate_abm(reduced_params, steps, seed=seeds["reduced"])

    obs_std = variance(obs_val) ** 0.5
    err_abm = rmse(abm["incidence"][val_start:], obs_val)
    err_ode = rmse(ode["incidence"][val_start:], obs_val)
    err_reduced = rmse(abm_reduced["incidence"][val_start:], obs_val)
    err_reduced_full = rmse(abm_reduced["incidence"][val_start:], abm["incidence"][val_start:])

    err_threshold = 0.6 * obs_std
    corr_abm = correlation(abm["incidence"][val_start:], obs_val)
    corr_ode = correlation(ode["incidence"][val_start:], obs_val)
    c1 = err_abm < err_threshold and err_ode < err_threshold and corr_abm > 0.7 and corr_ode > 0.7

    perturbed = perturb_params(base_params, 0.1, seed=10)
    perturbed["assimilation_series"] = None
    perturbed["assimilation_strength"] = 0.0
    abm_pert = simulate_abm(perturbed, steps, seed=seeds["perturbed"])
    mean_delta = abs(mean(abm_pert["incidence"][val_start:]) - mean(abm["incidence"][val_start:]))
    var_delta = abs(variance(abm_pert["incidence"][val_start:]) - variance(abm["incidence"][val_start:]))
    c2 = mean_delta < 0.5 and var_delta < 0.5

    abm_rep = simulate_abm(eval_params, steps, seed=seeds["replication"])
    persistence_base = window_variance(abm["incidence"][val_start:], 8)
    persistence_rep = window_variance(abm_rep["incidence"][val_start:], 8)
    c3 = abs(persistence_base - persistence_rep) < 0.3

    base_no_assim = dict(eval_params)
    base_no_assim["assimilation_strength"] = 0.0
    abm_base_no_assim = simulate_abm(base_no_assim, steps, seed=seeds["alt"])

    alt_params = dict(base_no_assim)
    alt_params["beta"] = min(0.6, base_params["beta"] * 1.2)
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
        p["assimilation_series"] = None
        p["assimilation_strength"] = 0.0
        s = simulate_abm(p, steps, seed=seeds["sensitivity"][i])
        sensitivities.append(mean(s["incidence"][val_start:]))
    sens_min = min(sensitivities)
    sens_max = max(sensitivities)
    c5 = (sens_max - sens_min) < 1.0

    internal, external = internal_vs_external_cohesion(abm["grid"], forcing_series)
    symploke_ok = internal > external
    dominance = dominance_share(abm["grid"])
    non_local_ok = dominance < 0.05
    obs_persistence = window_variance(obs_val, 8)
    persistence_ok = window_variance(abm["incidence"][val_start:], 8) < 1.5 * obs_persistence
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
            "expected_weeks": expected_weeks,
            "observed_weeks": observed_weeks,
            "coverage": coverage,
            "outlier_share": outlier_share,
        },
        "calibration": {
            "beta": base_params["beta"],
            "sigma": base_params["sigma"],
            "gamma": base_params["gamma"],
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
            "window_variance": window_variance(abm["incidence"][val_start:], 8),
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
    synthetic_start = "2010-01-03"
    synthetic_end = "2020-12-27"
    synthetic_split = "2017-01-01"
    synth_df, synth_meta = make_synthetic_df(synthetic_start, synthetic_end, seed=101)
    synthetic = evaluate_phase(
        "synthetic",
        synth_df,
        synthetic_start,
        synthetic_end,
        synthetic_split,
        synthetic_meta=synth_meta,
    )

    real_start = "2020-03-01"
    real_end = "2023-12-31"
    real_split = "2022-01-01"
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
    f.write(f"- expected_weeks: {results['data']['expected_weeks']}\n")
    f.write(f"- observed_weeks: {results['data']['observed_weeks']}\n")
    f.write(f"- coverage: {results['data']['coverage']:.3f}\n")
    f.write(f"- outlier_share: {results['data']['outlier_share']:.3f}\n\n")

    if "synthetic_meta" in results:
        f.write("### Meta sintetica\n")
        f.write(f"- beta: {results['synthetic_meta']['beta']:.3f}\n")
        f.write(f"- sigma: {results['synthetic_meta']['sigma']:.3f}\n")
        f.write(f"- gamma: {results['synthetic_meta']['gamma']:.3f}\n")
        f.write(f"- measurement_noise: {results['synthetic_meta']['measurement_noise']:.3f}\n\n")

    f.write("### Calibracion\n")
    f.write(f"- beta: {results['calibration']['beta']:.3f}\n")
    f.write(f"- sigma: {results['calibration']['sigma']:.3f}\n")
    f.write(f"- gamma: {results['calibration']['gamma']:.3f}\n")
    f.write(f"- macro_coupling: {results['calibration']['macro_coupling']:.3f}\n")
    f.write(f"- assimilation_strength: {results['calibration']['assimilation_strength']:.3f}\n\n")

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
        f.write("# Reporte de Validacion - Caso Epidemiologia\n\n")
        f.write("## Metadata\n")
        f.write(f"- generated_at: {results['generated_at']}\n")
        f.write(f"- git_commit: {results['git']['commit']}\n")
        f.write(f"- git_dirty: {results['git']['dirty']}\n\n")

        for label, phase in results["phases"].items():
            write_phase_report(f, label, phase)

        f.write("## Notas\n")
        f.write("- Fase sintetica: verificacion interna con serie controlada.\n")
        f.write("- Fase real: evaluacion final con datos OWID (World).\n")
        f.write("- Sensibilidad reportada en metrics.json.\n")


def main():
    results = evaluate()
    write_outputs(results)
    print("Validation complete. See outputs/metrics.json and outputs/report.md")


if __name__ == "__main__":
    main()
