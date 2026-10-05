"""Pull a small sample of USAspending contract transactions.

Purpose: confirm field names, pagination behaviour and row volumes before the
schema is finalised. Writes raw JSON pages to data/raw/sample/.

Usage:
    python ingestion/pull_sample.py --start 2025-06-01 --end 2025-06-07 --psc 1510 --max-pages 3
"""
import argparse
import json
import time
from pathlib import Path

import requests

URL = "https://api.usaspending.gov/api/v2/search/spending_by_transaction/"
FIELDS = [
    "Award ID", "Mod", "Recipient Name", "Recipient UEI", "Action Date",
    "Action Type", "Transaction Amount", "Awarding Agency",
    "Awarding Sub Agency", "Award Type", "PSC", "NAICS",
    "Primary Place of Performance", "Transaction Description",
    "internal_id", "generated_internal_id",
]
CONTRACT_TYPES = ["A", "B", "C", "D"]  # BPA call, purchase order, delivery order, definitive contract


def fetch_page(start, end, psc, page, limit):
    body = {
        "filters": {
            "time_period": [{"start_date": start, "end_date": end}],
            "award_type_codes": CONTRACT_TYPES,
            "psc_codes": [psc],
        },
        "fields": FIELDS,
        "page": page,
        "limit": limit,
        "sort": "Action Date",
        "order": "asc",
    }
    for attempt in range(4):
        resp = requests.post(URL, json=body, timeout=60)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()
    resp.raise_for_status()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--psc", default="1510")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--max-pages", type=int, default=3)
    args = p.parse_args()

    out = Path("data/raw/sample")
    out.mkdir(parents=True, exist_ok=True)
    total = 0
    for page in range(1, args.max_pages + 1):
        data = fetch_page(args.start, args.end, args.psc, page, args.limit)
        rows = data.get("results", [])
        total += len(rows)
        (out / f"psc{args.psc}_{args.start}_{args.end}_p{page}.json").write_text(json.dumps(data, indent=2))
        meta = data.get("page_metadata", {})
        print(f"page {page}: {len(rows)} rows, metadata={meta}")
        if not meta.get("hasNext"):
            break
    print(f"saved {total} rows to {out}")
    if rows:
        print("fields returned:", sorted(rows[0].keys()))


if __name__ == "__main__":
    main()
