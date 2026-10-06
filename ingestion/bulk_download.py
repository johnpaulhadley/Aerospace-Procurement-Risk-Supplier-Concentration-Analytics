"""Download full-column contract transactions from the USAspending bulk download API.

One request per agency per calendar month of action date. Each request starts a
server-side job; the script polls the status endpoint, then saves the zip to
data/raw/bulk/. Months already on disk are skipped, so a backfill can be re-run
safely.

Usage:
    python ingestion/bulk_download.py --start 2024-06 --end 2024-06
    python ingestion/bulk_download.py --start 2017-10 --end 2026-09      # full backfill
"""
import argparse
import calendar
import time
from datetime import date
from pathlib import Path

import requests

API = "https://api.usaspending.gov/api/v2/bulk_download/awards/"
AGENCIES = {
    "dod": "Department of Defense",
    "nasa": "National Aeronautics and Space Administration",
}
CONTRACT_TYPES = ["A", "B", "C", "D"]
OUT = Path("data/raw/bulk")


def months(start, end):
    y, m = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    while (y, m) <= (ey, em):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def request_job(agency_name, first, last):
    body = {
        "filters": {
            "prime_award_types": CONTRACT_TYPES,
            "date_type": "action_date",
            "date_range": {"start_date": first.isoformat(), "end_date": last.isoformat()},
            "agencies": [{"type": "awarding", "tier": "toptier", "name": agency_name}],
        },
        "file_format": "csv",
    }
    resp = requests.post(API, json=body, timeout=120)
    resp.raise_for_status()
    return resp.json()


def wait_for(status_url, poll=15, timeout=3600):
    waited = 0
    while waited < timeout:
        st = requests.get(status_url, timeout=60).json()
        if st["status"] == "finished":
            return st
        if st["status"] == "failed":
            raise RuntimeError(f"download job failed: {st.get('message')}")
        time.sleep(poll)
        waited += poll
    raise TimeoutError(status_url)


def save(file_url, dest):
    tmp = dest.with_suffix(".part")
    with requests.get(file_url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    tmp.rename(dest)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, help="first month, YYYY-MM")
    p.add_argument("--end", required=True, help="last month, YYYY-MM")
    p.add_argument("--agencies", nargs="+", default=list(AGENCIES), choices=list(AGENCIES))
    args = p.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    for y, m in months(args.start, args.end):
        first = date(y, m, 1)
        last = date(y, m, calendar.monthrange(y, m)[1])
        for key in args.agencies:
            dest = OUT / f"{key}_{y}-{m:02d}.zip"
            if dest.exists():
                print(f"skip {dest.name} (already downloaded)")
                continue
            job = request_job(AGENCIES[key], first, last)
            st = wait_for(job["status_url"])
            save(job["file_url"], dest)
            print(f"saved {dest.name}: {st.get('total_rows')} rows, {st.get('total_columns')} columns")


if __name__ == "__main__":
    main()
