"""
validate.py — Falsación: Exogeneidad
Validación híbrida ABM+ODE con protocolo C1-C5.
Generado automáticamente por el framework de validación de hiperobjetos.
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "common"))

from abm import simulate_abm
from data import fetch_memetic_daily
from ode import simulate_ode
from hybrid_validator import CaseConfig, run_full_validation, write_outputs


def load_real_data(start_date, end_date):

    cache_path = os.path.join(os.path.dirname(__file__), "..", "data", "memetic.csv")
    df = fetch_memetic_daily(start_date, end_date, cache_path=os.path.abspath(cache_path))
    df = df.rename(columns={"attention": "value"})
    df["date"] = pd.to_datetime(df["date"])
    return df.dropna(subset=["date", "value"])


def make_synthetic(start_date, end_date, seed=101):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start_date, end=end_date, freq="MS")
    steps = len(dates)
    if steps < 5:
        dates = pd.date_range(start=start_date, end=end_date, freq="YS")
        steps = len(dates)

    forcing = [0.01 * t for t in range(steps)]
    true_params = {
        "p0": 0.0, "ode_alpha": 0.08, "ode_beta": 0.03,
        "ode_noise": 0.02, "forcing_series": forcing,
        "p0_ode": 0.0,
    }
    sim = simulate_ode(true_params, steps, seed=seed + 1)
    ode_key = [k for k in sim if k not in ("forcing",)][0]
    obs = np.array(sim[ode_key]) + rng.normal(0.0, 0.05, size=steps)

    df = pd.DataFrame({"date": dates, "value": obs})
    meta = {"ode_true": {"alpha": 0.08, "beta": 0.03}, "measurement_noise": 0.05}
    return df, meta


def main():
    config = CaseConfig(
        case_name="Falsación: Exogeneidad",
        value_col="value",
        series_key="incidence",
        grid_size=20,
        persistence_window=6,
        synthetic_start="2020-01-01",
        synthetic_end="2024-01-01",
        synthetic_split="2022-01-01",
        real_start="2020-01-01",
        real_end="2024-01-01",
        real_split="2022-01-01",
        corr_threshold=0.7,
        extra_base_params={},
    )

    results = run_full_validation(
        config, load_real_data, make_synthetic,
        simulate_abm, simulate_ode,
    )

    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    write_outputs(results, os.path.abspath(out_dir))

    # Resumen
    for phase_name, phase in results.get("phases", {}).items():
        edi = phase.get("edi", {})
        sym = phase.get("symploke", {})
        print(f"  {phase_name}: overall={phase.get('overall_pass')} "
              f"EDI={edi.get('value', 0):.3f} CR={sym.get('cr', 0):.3f} "
              f"C1={phase.get('c1_convergence')} C2={phase.get('c2_robustness')} "
              f"C3={phase.get('c3_replication')} C4={phase.get('c4_validity')} "
              f"C5={phase.get('c5_uncertainty')}")
    print("Validación completa. Ver outputs/metrics.json y outputs/report.md")


if __name__ == "__main__":
    main()
