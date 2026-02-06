import math


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def variance(xs):
    if not xs:
        return 0.0
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def rmse(a, b):
    if len(a) != len(b) or not a:
        return 0.0
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def correlation(a, b):
    if len(a) != len(b) or len(a) < 2:
        return 0.0
    ma = mean(a)
    mb = mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den_a = math.sqrt(sum((x - ma) ** 2 for x in a))
    den_b = math.sqrt(sum((y - mb) ** 2 for y in b))
    if den_a == 0.0 or den_b == 0.0:
        return 0.0
    return num / (den_a * den_b)


def window_variance(xs, window):
    if len(xs) < window:
        return variance(xs)
    tail = xs[-window:]
    return variance(tail)


def internal_vs_external_cohesion(grid_series, forcing_series):
    steps = len(grid_series)
    if steps == 0:
        return 0.0, 0.0
    n = len(grid_series[0])

    internal_corrs = []
    external_corrs = []
    for i in range(n):
        for j in range(n):
            cell_series = [grid_series[t][i][j] for t in range(steps)]
            neighbor_series = []
            for t in range(steps):
                neighbors = []
                if i > 0:
                    neighbors.append(grid_series[t][i - 1][j])
                if i < n - 1:
                    neighbors.append(grid_series[t][i + 1][j])
                if j > 0:
                    neighbors.append(grid_series[t][i][j - 1])
                if j < n - 1:
                    neighbors.append(grid_series[t][i][j + 1])
                neighbor_series.append(sum(neighbors) / len(neighbors))

            internal_corrs.append(correlation(cell_series, neighbor_series))
            external_corrs.append(correlation(cell_series, forcing_series))

    internal = mean(internal_corrs)
    external = mean(external_corrs)
    return internal, external


def dominance_share(grid_series):
    steps = len(grid_series)
    if steps == 0:
        return 1.0
    n = len(grid_series[0])
    regional = []
    for t in range(steps):
        total = 0.0
        for i in range(n):
            total += sum(grid_series[t][i])
        regional.append(total / (n * n))

    scores = []
    for i in range(n):
        for j in range(n):
            cell_series = [grid_series[t][i][j] for t in range(steps)]
            scores.append(abs(correlation(cell_series, regional)))

    total = sum(scores) if scores else 1.0
    max_share = max(scores) / total if scores else 1.0
    return max_share
