"""Fetch raw NPPES NPI Registry results for the New Brunswick area.

Run from the repo root:  python scripts/fetch_nppes.py
Queries every in-scope Middlesex ZIP (config/middlesex_zips.csv: >=50% in
Middlesex, within 15 miles of New Brunswick) for each specialty and saves one
JSON file per ZIP x specialty to data/raw/providers/nppes/.
No filtering here: clean_providers.py keeps LOCATION addresses in Middlesex.
Re-running skips files that already exist (delete them to refresh).
"""
import json
import time
from pathlib import Path

import requests

from geo import query_zips

API = "https://npiregistry.cms.hhs.gov/api/"
SPECIALTIES = ["Dentist", "Pediatrics", "Obstetrics & Gynecology"]
PAGE = 200          # API max per request
MAX_SKIP = 1000     # API won't skip past this
OUT = Path("data/raw/providers/nppes")


def fetch(zip_code: str, specialty: str) -> list[dict]:
    results, skip = [], 0
    while skip <= MAX_SKIP:
        params = {
            "version": "2.1",
            "postal_code": zip_code,
            "taxonomy_description": specialty,
            "limit": PAGE,
            "skip": skip,
        }
        r = requests.get(API, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "Errors" in data:
            raise RuntimeError(f"{zip_code}/{specialty}: {data['Errors']}")
        batch = data.get("results", [])
        results.extend(batch)
        if len(batch) < PAGE:
            break
        skip += PAGE
        time.sleep(0.5)
    return results


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    zips = query_zips()
    print(f"{len(zips)} ZIPs x {len(SPECIALTIES)} specialties")
    for z in zips:
        for s in SPECIALTIES:
            slug = s.lower().replace(" & ", "_").replace(" ", "_")
            path = OUT / f"nppes_{z}_{slug}.json"
            if path.exists():
                continue
            rows = fetch(z, s)
            path.write_text(json.dumps({"zip": z, "specialty": s, "results": rows}, indent=1))
            print(f"{path.name}: {len(rows)} results")
            time.sleep(0.5)


if __name__ == "__main__":
    main()
