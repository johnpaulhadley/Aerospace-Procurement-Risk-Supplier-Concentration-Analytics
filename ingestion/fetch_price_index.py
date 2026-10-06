"""Download producer price index series from FRED and load them into PostgreSQL.

Uses FRED's public CSV download, which needs no API key. Each run replaces the
stored history for every series, because past index values are revised.

Usage:
    python ingestion/fetch_price_index.py
"""
import io

import pandas as pd
import requests
from sqlalchemy import create_engine, text

from config import database_url

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
SERIES = {
    "PCU33643364": "Aerospace product and parts manufacturing",
    "PCU336412336412": "Aircraft engine and engine parts manufacturing",
    "PCU336413336413": "Other aircraft parts and equipment manufacturing",
}
START = "2016-10-01"  # one year before the contract data, for year-over-year change


def fetch(series_id):
    resp = requests.get(URL, params={"id": series_id, "cosd": START}, timeout=60)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    if df.shape[1] != 2:
        raise ValueError(f"unexpected layout for {series_id}: {list(df.columns)}")
    df.columns = ["observation_date", "index_value"]
    df["observation_date"] = pd.to_datetime(df["observation_date"]).dt.date
    df["index_value"] = pd.to_numeric(df["index_value"], errors="coerce")  # FRED marks gaps with "."
    df = df.dropna(subset=["index_value"])
    df.insert(0, "series_id", series_id)
    df["series_name"] = SERIES[series_id]
    return df


def main():
    frames = [fetch(s) for s in SERIES]
    data = pd.concat(frames, ignore_index=True)
    engine = create_engine(database_url())
    with engine.begin() as con:
        con.execute(text("create schema if not exists raw"))
        con.execute(text("""
            create table if not exists raw.price_index (
              series_id text, observation_date date, index_value numeric,
              series_name text, _loaded_at timestamptz default now()
            )"""))
        con.execute(text("truncate raw.price_index"))
        data.to_sql("price_index", con, schema="raw", if_exists="append", index=False)
    for sid, grp in data.groupby("series_id"):
        print(f"{sid}: {len(grp)} months, {grp.observation_date.min()} to {grp.observation_date.max()}")


if __name__ == "__main__":
    main()
