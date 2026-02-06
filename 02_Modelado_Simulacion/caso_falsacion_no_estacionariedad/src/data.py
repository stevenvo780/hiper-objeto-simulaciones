import os
import time
from datetime import datetime

import numpy as np
import pandas as pd
import requests

API_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"

DEFAULT_ARTICLES = [
    "Bitcoin",
    "Cryptocurrency",
    "Non-fungible_token",
]


def _fetch_article_daily(article, start, end, user_agent):
    url = f"{API_BASE}/en.wikipedia.org/all-access/user/{article}/daily/{start}/{end}"
    headers = {"User-Agent": user_agent}
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 429:
        time.sleep(1)
        resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])
    rows = []
    for item in items:
        ts = item.get("timestamp")
        views = item.get("views")
        if not ts or views is None:
            continue
        date = datetime.strptime(ts[:8], "%Y%m%d")
        rows.append({"date": date, "views": int(views)})
    return rows


def fetch_crypto_daily(start_date, end_date, articles=None, cache_path=None):
    if cache_path and os.path.exists(cache_path):
        df = pd.read_csv(cache_path, parse_dates=["date"])
        return df

    articles = articles or DEFAULT_ARTICLES
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    start_ts = start.strftime("%Y%m%d00")
    end_ts = end.strftime("%Y%m%d00")

    user_agent = os.environ.get(
        "WIKIMEDIA_USER_AGENT",
        "SimulacionClimatica/1.0 (contact: local@example.com)",
    )

    all_rows = []
    for article in articles:
        all_rows.extend(_fetch_article_daily(article, start_ts, end_ts, user_agent))
        time.sleep(0.2)

    df = pd.DataFrame(all_rows)
    if df.empty:
        raise RuntimeError("No pageviews data returned")

    daily = df.groupby("date", as_index=False)["views"].sum().sort_values("date")
    daily["log_views"] = daily["views"].apply(lambda x: float(np.log(max(x, 1.0))))
    out = daily[["date", "log_views"]].rename(columns={"log_views": "attention"})

    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        out.to_csv(cache_path, index=False)

    return out
