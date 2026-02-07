
import os
import sys
import numpy as np
import pandas as pd
import json

# Add common to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "common"))

from abm import simulate_abm
from ode import simulate_ode
from hybrid_validator import CaseConfig, run_full_validation
from validate import load_real_data

# Modified make_synthetic with higher variance
def make_synthetic_high_variance(start_date, end_date, seed=101):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start_date, end=end_date, freq="YS")
    steps = len(dates)
    
    # Increase forcing slope to create more trend variance
    forcing = [0.1 * t for t in range(steps)] 
    true_params = {
        "p0": 0.0, "ode_alpha": 0.08, "ode_beta": 0.03,
        "ode_noise": 0.1, # Increased ODE noise
        "forcing_series": forcing,
        "p0_ode": 0.0,
    }
    sim = simulate_ode(true_params, steps, seed=seed + 1)
    ode_key = [k for k in sim if k not in ("forcing",)][0]
    
    # Inject high measurement noise to match real world std ~0.57
    obs = np.array(sim[ode_key]) + rng.normal(0.0, 0.57, size=steps)

    df = pd.DataFrame({"date": dates, "value": obs})
    meta = {"ode_true": {"alpha": 0.08, "beta": 0.03}, "measurement_noise": 0.57}
    return df, meta

def main():
    config = CaseConfig(
        case_name="Deforestación Global (High Var Test)",
        value_col="value",
        series_key="d",
        grid_size=20,
        persistence_window=5,
        synthetic_start="1990-01-01",
        synthetic_end="2022-01-01",
        synthetic_split="2010-01-01",
        real_start="1990-01-01",
        real_end="2022-01-01",
        real_split="2010-01-01",
        corr_threshold=0.7,
        extra_base_params={},
    )

    # Only run synthetic phase check
    print("Running validation with High Variance Synthetic Data...")
    results = run_full_validation(
        config, load_real_data, make_synthetic_high_variance,
        simulate_abm, simulate_ode,
    )
    
    syn_c1 = results['phases']['synthetic']['c1_convergence']
    syn_rmse = results['phases']['synthetic']['errors']['rmse_abm']
    syn_std = results['phases']['synthetic']['data']['obs_std_raw']
    
    print(f"RESULT: C1={syn_c1}")
    print(f"RMSE={syn_rmse}")
    print(f"STD={syn_std}")
    
    if not syn_c1:
        print("FAIL: Even with high variance, C1 fails. Scale Effect hypothesis falsified.")
    else:
        print("PASS: Higher variance fixed C1. Scale Effect confirmed.")

if __name__ == "__main__":
    main()
