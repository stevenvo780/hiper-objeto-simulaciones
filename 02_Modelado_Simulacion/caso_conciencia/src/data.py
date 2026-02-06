import os
from datetime import datetime

import pandas as pd
import requests

DATA_URL = "https://ourworldindata.org/grapher/happiness-cantril-ladder.csv"
DEFAULT_UA = "SimulacionClimatica/0.1"


def _request(url):
    headers = {"User-Agent": os.getenv("OWID_USER_AGENT", DEFAULT_UA)}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def fetch_happiness_series(cache_path, entity="World", fallback_entity="United States", start_year=2011, end_year=2024, refresh=False):
    cache_path = os.path.abspath(cache_path)
    if os.path.exists(cache_path) and not refresh:
        df = pd.read_csv(cache_path)
        df["date"] = pd.to_datetime(df["date"])
        meta = {
            "source": "OWID",
            "entity": df.get("entity", pd.Series([entity])).iloc[0],
            "cached": True,
            "start_year": int(df["year"].min()),
            "end_year": int(df["year"].max()),
        }
        return df, meta

    raw_csv = _request(DATA_URL)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(raw_csv)

    df = pd.read_csv(cache_path)
    if "Entity" not in df.columns or "Year" not in df.columns:
        raise RuntimeError("Formato inesperado en CSV de OWID")

    value_col = None
    for col in df.columns:
        if col.lower() not in {"entity", "code", "year"}:
            value_col = col
            break
    if value_col is None:
        raise RuntimeError("No se encontro columna de valores")

    entity_df = df[df["Entity"] == entity]
    used_entity = entity
    if entity_df.empty:
        entity_df = df[df["Entity"] == fallback_entity]
        used_entity = fallback_entity
    if entity_df.empty:
        raise RuntimeError("No se encontro entidad World ni fallback en OWID")

    entity_df = entity_df[(entity_df["Year"] >= start_year) & (entity_df["Year"] <= end_year)]
    entity_df = entity_df.sort_values("Year")
    if entity_df.empty:
        raise RuntimeError("Rango sin datos en OWID")

    rows = []
    for _, row in entity_df.iterrows():
        year = int(row["Year"])
        value = float(row[value_col])
        rows.append({"year": year, "date": datetime(year, 1, 1), "value": value, "entity": used_entity})

    out_df = pd.DataFrame(rows)
    out_df.to_csv(cache_path, index=False)

    meta = {
        "source": "OWID",
        "entity": used_entity,
        "cached": False,
        "start_year": int(out_df["year"].min()),
        "end_year": int(out_df["year"].max()),
        "value_col": value_col,
    }
    return out_df, meta
