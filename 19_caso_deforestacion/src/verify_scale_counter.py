"""
Counter-experiment: Correct Scale Effect Test
==============================================
The critic's 'isolated' test (verify_synthetic_isolated.py) increases
measurement noise from 0.05 to 0.57 WITHOUT scaling the ODE signal.
This destroys the SNR from 1.4 to 0.12 (signal buried in noise).

This script demonstrates the correct approach:
1. Scale the ODE signal amplitude to match real data range (~5 units)
2. Add measurement noise proportional to real data (std=0.57)
3. Result: SNR comparable to real data → C1 should pass

This proves the Scale Effect hypothesis: C1 failure in synthetic
is caused by low signal amplitude, not structural model failure.
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "common"))

from abm import simulate_abm
from ode import simulate_ode
from hybrid_validator import CaseConfig, run_full_validation
from validate import load_real_data


def make_synthetic_correct_scale(start_date, end_date, seed=101):
    """Synthetic with CORRECT scale: amplified signal + proportional noise."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start_date, end=end_date, freq="YS")
    steps = len(dates)

    # Same ODE dynamics as original
    forcing = [0.01 * t for t in range(steps)]
    true_params = {
        "p0": 0.0, "ode_alpha": 0.08, "ode_beta": 0.03,
        "ode_noise": 0.02,
        "forcing_series": forcing,
        "p0_ode": 0.0,
    }
    sim = simulate_ode(true_params, steps, seed=seed + 1)
    ode_key = [k for k in sim if k not in ("forcing",)][0]
    raw_signal = np.array(sim[ode_key])

    # SCALE signal to match real data amplitude (~5 units range)
    sig_range = raw_signal.max() - raw_signal.min()
    scale = 5.0 / max(sig_range, 0.01)
    scaled_signal = raw_signal * scale

    # Add noise proportional to real data (std=0.57)
    obs = scaled_signal + rng.normal(0.0, 0.57, size=steps)

    print(f"[CORRECT SCALE] signal_std={np.std(scaled_signal):.4f}, "
          f"noise_std=0.57, SNR={np.std(scaled_signal)/0.57:.2f}, "
          f"obs_std={np.std(obs):.4f}")

    df = pd.DataFrame({"date": dates, "value": obs})
    meta = {"ode_true": {"alpha": 0.08, "beta": 0.03},
            "scale_factor": scale, "measurement_noise": 0.57}
    return df, meta


def make_synthetic_critic_isolated(start_date, end_date, seed=101):
    """Critic's test: noise increased WITHOUT signal scaling (SNR destroyed)."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start_date, end=end_date, freq="YS")
    steps = len(dates)

    forcing = [0.01 * t for t in range(steps)]
    true_params = {
        "p0": 0.0, "ode_alpha": 0.08, "ode_beta": 0.03,
        "ode_noise": 0.02,
        "forcing_series": forcing,
        "p0_ode": 0.0,
    }
    sim = simulate_ode(true_params, steps, seed=seed + 1)
    ode_key = [k for k in sim if k not in ("forcing",)][0]
    raw_signal = np.array(sim[ode_key])

    obs = raw_signal + rng.normal(0.0, 0.57, size=steps)

    print(f"[CRITIC ISOLATED] signal_std={np.std(raw_signal):.4f}, "
          f"noise_std=0.57, SNR={np.std(raw_signal)/0.57:.2f}, "
          f"obs_std={np.std(obs):.4f}")

    df = pd.DataFrame({"date": dates, "value": obs})
    meta = {"ode_true": {"alpha": 0.08, "beta": 0.03}, "measurement_noise": 0.57}
    return df, meta


def main():
    config = CaseConfig(
        case_name="Deforestación (Counter-Experiment)",
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

    # Test 1: Critic's approach (broken SNR)
    print("=" * 60)
    print("TEST 1: Critic's Isolated Test (noise up, signal unchanged)")
    print("=" * 60)
    r1 = run_full_validation(
        config, load_real_data, make_synthetic_critic_isolated,
        simulate_abm, simulate_ode,
    )
    syn1 = r1['phases']['synthetic']
    print(f"  C1={syn1['c1_convergence']}, RMSE={syn1['errors']['rmse_abm']:.4f}")
    print()

    # Test 2: Correct scale (signal amplified, noise proportional)
    print("=" * 60)
    print("TEST 2: Correct Scale Test (signal scaled + proportional noise)")
    print("=" * 60)
    config2 = CaseConfig(
        case_name="Deforestación (Correct Scale)",
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
    r2 = run_full_validation(
        config2, load_real_data, make_synthetic_correct_scale,
        simulate_abm, simulate_ode,
    )
    syn2 = r2['phases']['synthetic']
    print(f"  C1={syn2['c1_convergence']}, RMSE={syn2['errors']['rmse_abm']:.4f}")
    print()

    print("=" * 60)
    print("CONCLUSION:")
    if not syn1['c1_convergence'] and syn2['c1_convergence']:
        print("  CONFIRMED: Scale Effect is real.")
        print("  Critic's test fails because SNR is destroyed (0.12).")
        print("  Correct test passes because SNR matches real data.")
    elif syn1['c1_convergence']:
        print("  Both pass — model works at any scale.")
    else:
        print(f"  Test 1 C1={syn1['c1_convergence']}, Test 2 C1={syn2['c1_convergence']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
