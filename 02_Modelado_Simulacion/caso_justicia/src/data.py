import os
from datetime import datetime

import pandas as pd
import requests

API_BASE = "https://api.worldbank.org/v2"
DEFAULT_UA = "SimulacionClimatica/0.1"


def _request(url, params=None):
    headers = {"User-Agent": os.getenv("WORLDBANK_USER_AGENT", DEFAULT_UA)}
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_rule_of_law(cache_path, country="USA", indicator="RL.EST", start_year=1996, end_year=2023, refresh=False):
    cache_path = os.path.abspath(cache_path)
    if os.path.exists(cache_path) and not refresh:
        df = pd.read_csv(cache_path)
        df["date"] = pd.to_datetime(df["date"])
        meta = {
            "source": "World Bank WGI",
            "country": country,
            "indicator": indicator,
            "cached": True,
            "start_year": int(df["year"].min()),
            "end_year": int(df["year"].max()),
        }
        return df, meta

    url = f"{API_BASE}/country/{country}/indicator/{indicator}"
    data = _request(url, params={"format": "json", "per_page": 1000})
    if not isinstance(data, list) or len(data) < 2:
        raise RuntimeError("Respuesta inesperada del API World Bank")

    entries = data[1]
    rows = []
    for entry in entries:
        year = entry.get("date")
        value = entry.get("value")
        if year is None:
            continue
        year = int(year)
        if year < start_year or year > end_year:
            continue
        if value is None:
            continue
        rows.append(
            {
                "year": year,
                "date": datetime(year, 1, 1),
                "value": float(value),
            }
        )

    df = pd.DataFrame(rows).sort_values("year")
    if df.empty:
        raise RuntimeError("No se encontraron datos para el rango solicitado")

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    df.to_csv(cache_path, index=False)

    meta = {
        "source": "World Bank WGI",
        "country": country,
        "indicator": indicator,
        "cached": False,
        "start_year": int(df["year"].min()),
        "end_year": int(df["year"].max()),
    }
    return df, meta
