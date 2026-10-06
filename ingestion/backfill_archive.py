"""Download USAspending's pre-built yearly contract files for the backfill.

These files already exist on the server, so there is no build wait. One file
per agency per federal fiscal year is saved to data/raw/archive/. Years already
on disk are skipped.

Usage:
    python ingestion/backfill_archive.py --start-fy 2018 --end-fy 2026
    python ingestion/backfill_archive.py --start-fy 2024 --end-fy 2024 --agencies nasa
"""
import argparse
from pathlib import Path

import requests

from config import AGENCIES

API = "https://api.usaspending.gov/api/v2/bulk_download"
OUT = Path("data/raw/archive")


def agency_ids():
    resp = requests.post(f"{API}/list_agencies/", json={"type": "award_agencies"}, timeout=60)
    resp.raise_for_status()
    groups = resp.json()["agencies"]
    listed = groups.get("cfo_agencies", []) + groups.get("other_agencies", [])
    return {a["toptier_code"]: a["toptier_agency_id"] for a in listed}


def full_file(agency_id, fiscal_year):
    resp = requests.post(f"{API}/list_monthly_files/", timeout=60,
                         json={"agency": agency_id, "fiscal_year": fiscal_year, "type": "contracts"})
    resp.raise_for_status()
    for f in resp.json()["monthly_files"]:
        if "_Full_" in f["file_name"]:
            return f
    raise LookupError(f"no full file for agency {agency_id} FY{fiscal_year}")


def save(url, dest):
    tmp = dest.with_suffix(".part")
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(tmp, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    tmp.rename(dest)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start-fy", type=int, required=True)
    p.add_argument("--end-fy", type=int, required=True)
    p.add_argument("--agencies", nargs="+", default=list(AGENCIES), choices=list(AGENCIES))
    args = p.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    ids = agency_ids()
    for fy in range(args.start_fy, args.end_fy + 1):
        for key in args.agencies:
            code = AGENCIES[key]["toptier_code"]
            if list(OUT.glob(f"FY{fy}_{code}_Contracts_Full_*.zip")):
                print(f"skip FY{fy} {key} (already downloaded)")
                continue
            f = full_file(ids[code], fy)
            print(f"downloading {f['file_name']} ...", flush=True)
            save(f["url"], OUT / f["file_name"])
            print(f"saved {f['file_name']}")


if __name__ == "__main__":
    main()
