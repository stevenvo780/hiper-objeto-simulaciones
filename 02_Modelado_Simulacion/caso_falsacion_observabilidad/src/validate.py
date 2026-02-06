import json
import os
import random
import subprocess
from datetime import datetime

import numpy as np
import pandas as pd

from abm import simulate_abm
from data import fetch_sparse_happiness
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
        os.path.dirname(__file__), "..", "data", "owid_happiness_sparse.csv"
    )
    cache_path = os.path.abspath(cache_path)
    df, meta = fetch_sparse_happiness(
        cache_path,
        entity="World",
        fallback_entity="United States",
        start_year=start_year,
        end_year=end_year,
        drop_rate=0.4,
        seed=7,
    )
    df = df.dropna()
    return df, meta


def make_synthetic_df(start_year, end_year, seed):
    rng = np.random.default_rng(seed)
    years = list(range(start_year, end_year + 1))
    steps = len(years)

    k = 0.15
    mid = int(steps * 0.5)
    t = np.arange(steps)
    level = 0.4 * np.tanh(k * (t - mid))

    measurement_noise = 0.04
    obs = level + rng.normal(0.0, measurement_noise, size=steps)

    df = pd.DataFrame(
        {
            "date": [datetime(y, 1, 1) for y in years],
            "value": obs,
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


def evaluate_phase(phase_name, df, start_year, end_year, split_year, synthetic_meta=None, real_meta=None):
    expected_years = len(range(start_year, end_year + 1))
    observed_years = len(df)
    coverage = observed_years / expected_years if expected_years else 0.0

    if df.empty or observed_years < 6:
        return {
            "phase": phase_name,
            "data": {
                "start": f"{start_year}-01-01",
                "end": f"{end_year}-12-31",
                "split": f"{split_year}-01-01",
                "obs_mean": 0.0,
                "obs_std_raw": 0.0,
                "steps": observed_years,
                "val_steps": 0,
                "expected_years": expected_years,
                "observed_years": observed_years,
                "coverage": coverage,
                "outlier_share": 0.0,
            },
            "c1_convergence": False,
            "c2_robustness": False,
            "c3_replication": False,
            "c4_validity": False,
            "c5_uncertainty": False,
            "overall_pass": False,
        }

    obs_raw = df["value"].tolist()
    obs_mean = float(np.mean(obs_raw))
    obs_std_raw = float(np.std(obs_raw)) if obs_raw else 0.0
    df = df.copy()
    if obs_std_raw > 0.0:
        df["value_z"] = (df["value"] - obs_mean) / obs_std_raw
    else:
        df["value_z"] = 0.0

    train_df = df[df["date"].dt.year < split_year]
    val_df = df[df["date"].dt.year >= split_year]
    if train_df.empty or val_df.empty:
        c1 = False
        obs = df["value_z"].tolist()
        obs_val = val_df["value_z"].tolist()
    else:
        obs = df["value_z"].tolist()
        obs_val = val_df["value_z"].tolist()
        steps = len(obs)
        val_start = len(train_df)

        forcing_series, trend_params = build_forcing(obs[:val_start], steps)

        base_params = {
            "grid_size": 20,
            "diffusion": 0.2,
            "noise": 0.02,
            "macro_coupling": 0.1,
            "forcing_series": forcing_series,
            "forcing_scale": 0.1,
            "damping": 0.05,
            "alpha": 0.2,
            "beta": 0.05,
            "p0": obs[0],
            "p0_ode": obs[0],
        }

        eval_params = dict(base_params)
        eval_params["assimilation_series"] = None
        eval_params["assimilation_strength"] = 0.0

        abm = simulate_abm(eval_params, steps, seed=2)
        ode = simulate_ode(eval_params, steps, seed=3)

        obs_std = variance(obs_val) ** 0.5
        err_abm = rmse(abm["incidence"][val_start:], obs_val)
        err_ode = rmse(ode["share"][val_start:], obs_val)
        err_threshold = 0.6 * obs_std
        corr_abm = correlation(abm["incidence"][val_start:], obs_val)
        corr_ode = correlation(ode["share"][val_start:], obs_val)
        c1 = err_abm < err_threshold and err_ode < err_threshold and corr_abm > 0.7 and corr_ode > 0.7

    results = {
        "phase": phase_name,
        "data": {
            "start": f"{start_year}-01-01",
            "end": f"{end_year}-12-31",
            "split": f"{split_year}-01-01",
            "obs_mean": obs_mean,
            "obs_std_raw": obs_std_raw,
            "steps": observed_years,
            "val_steps": len(obs_val),
            "expected_years": expected_years,
            "observed_years": observed_years,
            "coverage": coverage,
            "outlier_share": 0.0,
        },
        "c1_convergence": c1,
        "c2_robustness": False,
        "c3_replication": False,
        "c4_validity": False,
        "c5_uncertainty": coverage >= 0.85,
        "overall_pass": False,
    }

    if synthetic_meta:
        results["synthetic_meta"] = synthetic_meta
    if real_meta:
        results["real_meta"] = real_meta

    return results


def run():
    start_year = 2011
    end_year = 2023
    split_year = 2018

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
        f.write("# Reporte de Falsacion - Observabilidad Insuficiente\n\n")
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
            f.write("\n### Criterios\n")
            f.write(f"- c1_convergence: {phase['c1_convergence']}\n")
            f.write(f"- c5_uncertainty: {phase['c5_uncertainty']}\n\n")

        f.write("## Notas\n")
        f.write("- Cobertura deliberadamente insuficiente para falsacion.\n")

    return metrics_path, report_path


if __name__ == "__main__":
    run()
    print("Validation complete. See outputs/metrics.json and outputs/report.md")
