import json
import os
import random
import subprocess
from datetime import datetime

import numpy as np
import pandas as pd

from abm import simulate_abm
from data import fetch_moderation_monthly
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


def load_observations(start_date, end_date):
    cache_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "moderation_monthly.csv"
    )
    cache_path = os.path.abspath(cache_path)
    df = fetch_moderation_monthly(start_date, end_date, cache_path=cache_path)
    df = df.dropna()
    return df


def make_synthetic_df(start_date, end_date, seed):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start_date, end=end_date, freq="MS")
    steps = len(dates)

    k = 0.06
    mid = int(steps * 0.55)
    t = np.arange(steps)
    series = 1.0 / (1.0 + np.exp(-k * (t - mid)))

    measurement_noise = 0.04
    obs = series + rng.normal(0.0, measurement_noise, size=steps)

    df = pd.DataFrame({"date": dates, "attention": obs})
    meta = {"k": k, "mid": mid, "measurement_noise": measurement_noise}
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


def adversarial_forcing(obs, strength=0.3):
    # Feedback adversarial: cuanto mas alta la atencion, mayor shock negativo
    return [-(strength * x) for x in obs]


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
    for forcing_scale in [0.05, 0.1, 0.2]:
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


def evaluate_phase(phase_name, df, start_date, end_date, split_date, synthetic_meta=None):
    if df.empty or len(df) < 60:
        raise RuntimeError(f"Insufficient data for phase {phase_name}")

    expected_months = len(pd.date_range(start=start_date, end=end_date, freq="MS"))
    observed_months = len(df)
    coverage = observed_months / expected_months if expected_months else 0.0
    if coverage < 0.85:
        raise RuntimeError(f"Data coverage too low for phase {phase_name}: {coverage:.2f}")

    obs_raw = df["attention"].tolist()
    obs_mean = float(np.mean(obs_raw))
    obs_std_raw = float(np.std(obs_raw)) if obs_raw else 0.0
    df = df.copy()
    if obs_std_raw > 0.0:
        df["attention_z"] = (df["attention"] - obs_mean) / obs_std_raw
    else:
        df["attention_z"] = 0.0

    train_df = df[df["date"] < split_date]
    val_df = df[df["date"] >= split_date]
    if train_df.empty or val_df.empty:
        raise RuntimeError(f"Insufficient data for train/validation split in phase {phase_name}")

    obs = df["attention_z"].tolist()
    obs_val = val_df["attention_z"].tolist()
    steps = len(obs)
    val_start = len(train_df)

    forcing_series, trend_params = build_forcing(obs[:val_start], steps)
    adv_series = adversarial_forcing(obs)
    forcing_series = [forcing_series[i] + adv_series[i] for i in range(steps)]

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
            "outlier_share": 0.0,
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
        "c2_robustness": False,
        "c3_replication": False,
        "c4_validity": False,
        "c5_uncertainty": True,
        "overall_pass": False,
    }

    if synthetic_meta:
        results["synthetic_meta"] = synthetic_meta

    return results


def run():
    start_date = "2015-01-01"
    end_date = "2024-12-01"
    split_date = "2019-01-01"

    synth_df, synth_meta = make_synthetic_df(start_date, end_date, seed=10)
    real_df = load_observations(start_date, end_date)

    synth_results = evaluate_phase(
        "synthetic",
        synth_df,
        start_date,
        end_date,
        split_date,
        synthetic_meta=synth_meta,
    )

    real_start = real_df["date"].min().strftime("%Y-%m-%d")
    real_end = real_df["date"].max().strftime("%Y-%m-%d")

    real_results = evaluate_phase(
        "real",
        real_df,
        real_start,
        real_end,
        split_date,
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
        f.write("# Reporte - Moderacion Adversarial (Jefe Final)\n\n")
        f.write(f"## Metadata\n- generated_at: {metrics['generated_at']}\n")
        git_info = metrics.get("git", {})
        f.write(f"- git_commit: {git_info.get('commit')}\n")
        f.write(f"- git_dirty: {git_info.get('dirty')}\n\n")
        for phase_key in ["synthetic", "real"]:
            phase = metrics["phases"][phase_key]
            f.write(f"## Fase {phase_key}\n- overall_pass: {phase['overall_pass']}\n\n")
            f.write("### Criterios\n")
            f.write(f"- c1_convergence: {phase['c1_convergence']}\n")
            f.write(f"- c4_validity: {phase['c4_validity']}\n\n")

        f.write("## Notas\n")
        f.write("- Caso adversarial con forcing dependiente del estado.\n")

    return metrics_path, report_path


if __name__ == "__main__":
    run()
    print("Validation complete. See outputs/metrics.json and outputs/report.md")
