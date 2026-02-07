
import os
import sys
import numpy as np
import pandas as pd

# Add common to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "common"))

from abm import simulate_abm
from ode import simulate_ode
from hybrid_validator import CaseConfig, run_full_validation
from validate import load_real_data

# Modified make_synthetic ISOLATING only measurement noise (Scale Effect)
def make_synthetic_isolated(start_date, end_date, seed=101):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start_date, end=end_date, freq="YS")
    steps = len(dates)
    
    # KEEP ORIGINAL DYNAMICS (as in original validate.py)
    forcing = [0.01 * t for t in range(steps)] 
    true_params = {
        "p0": 0.0, "ode_alpha": 0.08, "ode_beta": 0.03,
        "ode_noise": 0.02, # ORIGINAL
        "forcing_series": forcing, # ORIGINAL
        "p0_ode": 0.0,
    }
    sim = simulate_ode(true_params, steps, seed=seed + 1)
    ode_key = [k for k in sim if k not in ("forcing",)][0]
    
    # ONLY CHANGE MEASUREMENT NOISE to match real world std ~0.57
    # Original was rng.normal(0.0, 0.05, ...)
    obs = np.array(sim[ode_key]) + rng.normal(0.0, 0.57, size=steps)

    df = pd.DataFrame({"date": dates, "value": obs})
    meta = {"ode_true": {"alpha": 0.08, "beta": 0.03}, "measurement_noise": 0.57}
    return df, meta

def main():
    config = CaseConfig(
        case_name="Deforestación (Isolated Scale Test)",
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

    print("Running validation with ISOLATED High Variance Synthetic Data...")
    results = run_full_validation(
        config, load_real_data, make_synthetic_isolated,
        simulate_abm, simulate_ode,
    )
    
    syn = results['phases']['synthetic']
    print(f"RESULT: C1_PASS={syn['c1_convergence']}")
    print(f"RMSE={syn['errors']['rmse_abm']:.6f}")
    print(f"OBS_STD={syn['data']['obs_std_raw']:.6f}")
    
    # Logic of C1 in validator: rmse < threshold_factor * obs_std
    # Usually threshold_factor is around 1.0 (mean of raw)
    # We want to see if increasing OBS_STD (Scale) fixes C1.
    
    if not syn['c1_convergence']:
        print("FALSIFIED: Even isolating the scale, C1 fails. The problem is structural.")
    else:
        print("CONFIRMED: Scale effect was indeed the cause.")

if __name__ == "__main__":
    main()
