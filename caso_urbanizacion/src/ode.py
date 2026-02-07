import random


def simulate_ode(params, steps, seed):
    random.seed(seed)
    alpha = params.get("alpha", 0.2)
    beta = params.get("beta", 0.05)
    noise = params.get("noise", 0.01)
    p = params.get("p0", 0.0)

    forcing = params["forcing_series"]
    assimilation_series = params.get("assimilation_series")
    assimilation_strength = params.get("assimilation_strength", 0.0)

    series = []
    for t in range(steps):
        f = forcing[t]
        dp = alpha * (f - p) - beta * p
        p = p + dp + random.uniform(-noise, noise)

        if assimilation_series is not None and t < len(assimilation_series):
            target = assimilation_series[t]
            if target is not None:
                p = p + assimilation_strength * (target - p)

        series.append(p)

    return {
        "u": series,
        "forcing": forcing,
    }
