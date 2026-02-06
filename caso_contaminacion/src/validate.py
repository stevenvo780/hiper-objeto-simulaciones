"""
validate.py — Caso Contaminación (PM2.5 global)
Hiperobjeto: Contaminación atmosférica como entidad emergente.
Datos: World Bank PM2.5 (EN.ATM.PM25.MC.M3), resolución anual.
"""

import os
import sys

import numpy as np
import pandas as pd

# Agregar common/ al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "common"))

from abm import simulate_abm
from data import fetch_pm25_worldbank
from ode import simulate_ode
from hybrid_validator import CaseConfig, run_full_validation, write_outputs


def load_real_data(start_date, end_date):
    cache_path = os.path.join(os.path.dirname(__file__), "..", "data", "pm25_world.csv")
    cache_path = os.path.abspath(cache_path)
    df = fetch_pm25_worldbank(start_date, end_date, cache_path=cache_path)
    return df.dropna()


def make_synthetic(start_date, end_date, seed=101):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start_date, end=end_date, freq="YS")
    steps = len(dates)

    forcing = [0.01 * t for t in range(steps)]
    true_params = {
        "p0": 0.0, "ode_alpha": 0.08, "ode_beta": 0.03,
        "ode_noise": 0.02, "forcing_series": forcing,
    }
    sim = simulate_ode(true_params, steps, seed=seed + 1)
    obs = np.array(sim["p"]) + rng.normal(0.0, 0.05, size=steps)

    df = pd.DataFrame({"date": dates, "pm25": obs})
    meta = {
        "ode_true": {"alpha": 0.08, "beta": 0.03, "noise": 0.02},
        "measurement_noise": 0.05,
    }
    return df, meta


def main():
    config = CaseConfig(
        case_name="Contaminación PM2.5",
        value_col="pm25",
        series_key="p",
        grid_size=10,
        persistence_window=5,
        synthetic_start="1980-01-01",
        synthetic_end="2019-01-01",
        synthetic_split="2000-01-01",
        real_start="1990-01-01",
        real_end="2022-01-01",
        real_split="2006-01-01",
        extra_base_params={"pollution_scale": 0.01},
    )

    results = run_full_validation(
        config, load_real_data, make_synthetic,
        simulate_abm, simulate_ode,
    )

    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    write_outputs(results, os.path.abspath(out_dir))
    print("Validación completa. Ver outputs/metrics.json y outputs/report.md")


if __name__ == "__main__":
    main()
