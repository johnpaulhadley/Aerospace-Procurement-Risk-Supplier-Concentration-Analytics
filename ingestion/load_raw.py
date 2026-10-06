"""Load USAspending contract files into PostgreSQL, keeping only in-scope rows.

Reads every zip under the given paths, filters each CSV chunk to the project
scope, and copies the rows into raw.contract_transactions as text. Loading is
idempotent per source file: rows from a file are deleted before it is reloaded.
Each load is recorded in raw.load_log.

Usage:
    python ingestion/load_raw.py data/raw/bulk
    python ingestion/load_raw.py data/raw/archive/FY2024_097_Contracts_Full_20260906.zip
"""
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from config import COLUMNS, NAICS_PREFIX, PSC_GROUPS, database_url

TABLE = "raw.contract_transactions"
CHUNK = 100_000


def ensure_tables(engine):
    cols = ",\n  ".join(f'"{c}" text' for c in COLUMNS)
    with engine.begin() as con:
        con.execute(text("create schema if not exists raw"))
        con.execute(text(f"""
            create table if not exists {TABLE} (
              {cols},
              _source_file text not null,
              _loaded_at timestamptz not null default now()
            )"""))
        con.execute(text(f"create index if not exists ix_raw_ct_source on {TABLE} (_source_file)"))
        con.execute(text("""
            create table if not exists raw.load_log (
              source_file text, rows_read bigint, rows_loaded bigint,
              net_obligation_loaded numeric, loaded_at timestamptz default now()
            )"""))


def in_scope(df):
    psc = df["product_or_service_code"].str[:2].isin(PSC_GROUPS)
    naics = df["naics_code"].str.startswith(NAICS_PREFIX)
    return df[psc | naics]


def load_zip(engine, path):
    source = path.name
    rows_read = rows_loaded = 0
    net = 0.0
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute(f"delete from {TABLE} where _source_file = %s", (source,))
        with zipfile.ZipFile(path) as zf:
            for member in zf.namelist():
                if not member.lower().endswith(".csv"):
                    continue
                with zf.open(member) as fh:
                    header = pd.read_csv(fh, nrows=0).columns
                missing = [c for c in COLUMNS if c not in header]
                if missing:
                    raise ValueError(f"{source}/{member} is missing columns: {missing}")
                with zf.open(member) as fh:
                    for chunk in pd.read_csv(fh, usecols=COLUMNS, dtype=str,
                                             keep_default_na=False, chunksize=CHUNK):
                        rows_read += len(chunk)
                        keep = in_scope(chunk)[COLUMNS].copy()
                        if keep.empty:
                            continue
                        net += pd.to_numeric(keep["federal_action_obligation"], errors="coerce").sum()
                        keep["_source_file"] = source
                        buf = io.StringIO()
                        keep.to_csv(buf, index=False, header=False)
                        buf.seek(0)
                        col_list = ", ".join(f'"{c}"' for c in COLUMNS + ["_source_file"])
                        cur.copy_expert(
                            f"copy {TABLE} ({col_list}) from stdin with (format csv, null '')", buf)
                        rows_loaded += len(keep)
        cur.execute(
            "insert into raw.load_log (source_file, rows_read, rows_loaded, net_obligation_loaded) "
            "values (%s, %s, %s, %s)", (source, rows_read, rows_loaded, round(float(net), 2)))
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()
    print(f"{source}: read {rows_read:,}, loaded {rows_loaded:,}, net ${net:,.0f}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    paths = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        paths += sorted(p.glob("*.zip")) if p.is_dir() else [p]
    engine = create_engine(database_url())
    ensure_tables(engine)
    for p in paths:
        load_zip(engine, p)


if __name__ == "__main__":
    main()
