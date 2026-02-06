"""
metrics_enhanced.py — Métricas robustas para validación de hiperobjetos.

Mejoras sobre metrics.py original:
- EDI con bootstrap CI (intervalos de confianza)
- Effective Information (EI) con KDE en lugar de bins duros
- Tests estadísticos de significancia
- Cohesion Ratio (CR) como métrica unificada
- Window variance con soporte multi-escala
"""

import math
import random


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def variance(xs):
    if not xs:
        return 0.0
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def std(xs):
    return math.sqrt(variance(xs))


def rmse(a, b):
    if len(a) != len(b) or not a:
        return float("inf")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def correlation(a, b):
    if len(a) != len(b) or len(a) < 2:
        return 0.0
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den_a = math.sqrt(sum((x - ma) ** 2 for x in a))
    den_b = math.sqrt(sum((y - mb) ** 2 for y in b))
    if den_a < 1e-15 or den_b < 1e-15:
        return 0.0
    return max(-1.0, min(1.0, num / (den_a * den_b)))


def window_variance(xs, window):
    if len(xs) < window:
        return variance(xs)
    return variance(xs[-window:])


def multi_scale_window_variance(xs, windows):
    """Varianza en múltiples escalas temporales."""
    return {w: window_variance(xs, w) for w in windows}


# --- EDI (Effective Dependence Index) ---

def compute_edi(rmse_abm, rmse_reduced):
    """
    EDI = (rmse_reduced - rmse_abm) / rmse_reduced
    Mide cuánto mejora el modelo completo vs. el reducido (sin acoplamiento macro).
    EDI > 0.30 → emergencia detectada
    EDI > 0.90 → sospecha de tautología
    """
    if rmse_reduced < 1e-15:
        return 0.0
    edi = (rmse_reduced - rmse_abm) / rmse_reduced
    return edi


def bootstrap_edi(obs_val, abm_val, reduced_val, n_boot=500, ci=0.95, seed=42):
    """
    Bootstrap CI para EDI. Remuestrea los residuos y recalcula EDI n_boot veces.
    Retorna: (edi_mean, edi_lo, edi_hi, edi_samples)
    """
    rng = random.Random(seed)
    n = len(obs_val)
    if n < 4:
        edi = compute_edi(rmse(abm_val, obs_val), rmse(reduced_val, obs_val))
        return edi, edi, edi, [edi]

    edi_samples = []
    for _ in range(n_boot):
        indices = [rng.randint(0, n - 1) for _ in range(n)]
        obs_b = [obs_val[i] for i in indices]
        abm_b = [abm_val[i] for i in indices]
        red_b = [reduced_val[i] for i in indices]
        r_abm = rmse(abm_b, obs_b)
        r_red = rmse(red_b, obs_b)
        edi_samples.append(compute_edi(r_abm, r_red))

    edi_samples.sort()
    alpha = (1.0 - ci) / 2.0
    lo_idx = max(0, int(alpha * n_boot))
    hi_idx = min(n_boot - 1, int((1.0 - alpha) * n_boot))
    return mean(edi_samples), edi_samples[lo_idx], edi_samples[hi_idx], edi_samples


# --- Effective Information (EI) via KDE-like approach ---

def _gaussian_kernel(x, mu, h):
    """Kernel gaussiano para estimación de densidad."""
    z = (x - mu) / h
    return math.exp(-0.5 * z * z) / (h * math.sqrt(2 * math.pi))


def _kde_entropy(series, n_eval=50, bandwidth=None):
    """
    Entropía Shannon estimada via KDE (Kernel Density Estimation).
    Más robusta que bins duros para series cortas.
    """
    n = len(series)
    if n < 2:
        return 0.0

    s_min, s_max = min(series), max(series)
    s_range = s_max - s_min
    if s_range < 1e-15:
        return 0.0

    if bandwidth is None:
        bandwidth = 1.06 * std(series) * (n ** (-0.2))
    if bandwidth < 1e-15:
        bandwidth = s_range / 10.0

    margin = 3 * bandwidth
    eval_min = s_min - margin
    eval_max = s_max + margin
    dx = (eval_max - eval_min) / n_eval

    entropy = 0.0
    for k in range(n_eval):
        x = eval_min + (k + 0.5) * dx
        density = sum(_gaussian_kernel(x, s, bandwidth) for s in series) / n
        if density > 1e-15:
            entropy -= density * math.log(density) * dx

    return max(0.0, entropy)


def effective_information(full_series, reduced_series):
    """
    EI = H(reduced) - H(full)
    Mide la reducción de entropía que el modelo macro aporta.
    Si EI > 0, el modelo macro reduce incertidumbre.
    """
    h_full = _kde_entropy(full_series)
    h_reduced = _kde_entropy(reduced_series)
    return h_reduced - h_full


def effective_information_residuals(obs, full_pred, reduced_pred):
    """
    EI basado en residuos: H(residuos_reducido) - H(residuos_completo).
    Más informativo que comparar series directamente.
    """
    res_full = [o - p for o, p in zip(obs, full_pred)]
    res_reduced = [o - p for o, p in zip(obs, reduced_pred)]
    return effective_information(res_full, res_reduced)


# --- Cohesion Ratio (CR) ---

def internal_vs_external_cohesion(grid_series, forcing_series):
    """
    Cohesión interna (correlación entre celdas vecinas) vs.
    cohesión externa (correlación celdas-forcing).
    """
    steps = len(grid_series)
    if steps == 0:
        return 0.0, 0.0
    n = len(grid_series[0])

    internal_corrs = []
    external_corrs = []
    for i in range(n):
        for j in range(n):
            cell_series = [grid_series[t][i][j] for t in range(steps)]
            neighbors = []
            for t in range(steps):
                nb = []
                if i > 0:
                    nb.append(grid_series[t][i - 1][j])
                if i < n - 1:
                    nb.append(grid_series[t][i + 1][j])
                if j > 0:
                    nb.append(grid_series[t][i][j - 1])
                if j < n - 1:
                    nb.append(grid_series[t][i][j + 1])
                neighbors.append(sum(nb) / len(nb))

            internal_corrs.append(correlation(cell_series, neighbors))
            if len(forcing_series) == steps:
                external_corrs.append(correlation(cell_series, forcing_series))

    internal = mean(internal_corrs)
    external = mean(external_corrs) if external_corrs else 0.0
    return internal, external


def cohesion_ratio(internal, external):
    """CR = internal / external. CR > 2.0 indica frontera sistémica."""
    if abs(external) < 1e-10:
        return float("inf") if internal > 0 else 0.0
    return abs(internal / external)


def dominance_share(grid_series):
    """Proporción del agente más dominante. Non-locality si < 0.05."""
    steps = len(grid_series)
    if steps == 0:
        return 1.0
    n = len(grid_series[0])
    regional = []
    for t in range(steps):
        total = sum(sum(row) for row in grid_series[t])
        regional.append(total / (n * n))

    scores = []
    for i in range(n):
        for j in range(n):
            cell_series = [grid_series[t][i][j] for t in range(steps)]
            scores.append(abs(correlation(cell_series, regional)))

    total_score = sum(scores) if scores else 1.0
    if total_score < 1e-15:
        return 1.0 / (n * n)
    return max(scores) / total_score


# --- Tests estadísticos ---

def diebold_mariano_like(errors_1, errors_2):
    """
    Test simplificado estilo Diebold-Mariano.
    Compara dos series de errores cuadrados.
    Retorna: (stat, significant_at_05)
    stat > 1.96 indica que model_1 es significativamente mejor.
    """
    n = len(errors_1)
    if n < 10:
        return 0.0, False
    d = [e2 ** 2 - e1 ** 2 for e1, e2 in zip(errors_1, errors_2)]
    d_mean = mean(d)
    d_var = variance(d)
    if d_var < 1e-15:
        return 0.0, False
    stat = d_mean / math.sqrt(d_var / n)
    return stat, abs(stat) > 1.96


def emergence_significance(obs, abm_pred, reduced_pred, n_perm=200, seed=42):
    """
    Test de permutación para significancia de emergencia.
    Compara RMSE del modelo completo vs. reducido bajo permutaciones aleatorias.
    Retorna: (p_value, significant)
    """
    rng = random.Random(seed)
    observed_diff = rmse(reduced_pred, obs) - rmse(abm_pred, obs)

    count = 0
    combined = list(zip(abm_pred, reduced_pred))
    for _ in range(n_perm):
        perm_abm = []
        perm_red = []
        for a, r in combined:
            if rng.random() < 0.5:
                perm_abm.append(a)
                perm_red.append(r)
            else:
                perm_abm.append(r)
                perm_red.append(a)
        perm_diff = rmse(perm_red, obs) - rmse(perm_abm, obs)
        if perm_diff >= observed_diff:
            count += 1

    p_value = (count + 1) / (n_perm + 1)
    return p_value, p_value < 0.05
