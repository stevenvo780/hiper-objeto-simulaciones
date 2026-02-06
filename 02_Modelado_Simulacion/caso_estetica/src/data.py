import os
import re
from datetime import datetime

import pandas as pd
import requests

DATA_URL = "https://raw.githubusercontent.com/MuseumofModernArt/collection/main/Artworks.csv"
MEDIA_URL = "https://media.githubusercontent.com/media/MuseumofModernArt/collection/main/Artworks.csv"
DEFAULT_UA = "SimulacionClimatica/0.1"


def _request(url):
    headers = {"User-Agent": os.getenv("MOMA_USER_AGENT", DEFAULT_UA)}
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.text


def _is_lfs_pointer(text):
    lines = text.splitlines()
    if not lines:
        return False
    return lines[0].startswith("version https://git-lfs.github.com/spec/v1")


def _extract_year(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if isinstance(value, (int, float)):
        year = int(value)
        if 1000 <= year <= 2100:
            return year
        return None
    text = str(value)
    match = re.search(r"(1[6-9]\d{2}|20\d{2})", text)
    if not match:
        return None
    year = int(match.group(0))
    if 1600 <= year <= 2100:
        return year
    return None


def fetch_moma_share(cache_path, start_year=1929, end_year=2023, refresh=False):
    cache_path = os.path.abspath(cache_path)
    raw_df = None
    if os.path.exists(cache_path) and not refresh:
        with open(cache_path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(256)
        if not _is_lfs_pointer(head):
            raw_df = pd.read_csv(cache_path)
            if "date" in raw_df.columns and "share" in raw_df.columns:
                raw_df["date"] = pd.to_datetime(raw_df["date"])
                meta = {
                    "source": "MoMA Collection",
                    "cached": True,
                    "start_year": int(raw_df["year"].min()),
                    "end_year": int(raw_df["year"].max()),
                }
                return raw_df, meta

    if raw_df is None:
        raw_csv = _request(DATA_URL)
        if _is_lfs_pointer(raw_csv):
            raw_csv = _request(MEDIA_URL)
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(raw_csv)
        df = pd.read_csv(cache_path)
    else:
        df = raw_df
    if "Date" not in df.columns or "Classification" not in df.columns:
        raise RuntimeError("Formato inesperado en Artworks.csv")

    df["year"] = df["Date"].apply(_extract_year)
    df = df.dropna(subset=["year", "Classification"]).copy()
    df["year"] = df["year"].astype(int)
    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()

    df["Classification"] = df["Classification"].astype(str).str.strip()
    df = df[df["Classification"].isin(["Painting", "Sculpture"])]

    counts = df.groupby(["year", "Classification"]).size().unstack(fill_value=0)
    rows = []
    for year in range(start_year, end_year + 1):
        if year in counts.index:
            painting = int(counts.loc[year].get("Painting", 0))
            sculpture = int(counts.loc[year].get("Sculpture", 0))
        else:
            painting = 0
            sculpture = 0
        total = painting + sculpture
        share = painting / total if total > 0 else 0.0
        rows.append(
            {
                "year": year,
                "date": datetime(year, 1, 1),
                "painting": painting,
                "sculpture": sculpture,
                "share": share,
            }
        )

    out_df = pd.DataFrame(rows)
    series_path = cache_path.replace(".csv", "_series.csv")
    out_df.to_csv(series_path, index=False)

    meta = {
        "source": "MoMA Collection",
        "cached": False,
        "start_year": start_year,
        "end_year": end_year,
        "series_path": series_path,
    }
    return out_df, meta
