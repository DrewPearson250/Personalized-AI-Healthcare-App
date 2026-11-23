"""Fetch raw NPPES NPI Registry results for the New Brunswick area.

Run from the repo root:  python scripts/fetch_nppes.py
Saves one JSON file per ZIP x specialty to data/raw/providers/.
No filtering here: clean_providers.py keeps LOCATION addresses in Middlesex.
"""
import json
import time
from pathlib import Path

import requests

API = "https://npiregistry.cms.hhs.gov/api/"
ZIPS = ["08901", "08902", "08903", "08904", "08906"]
SPECIALTIES = ["Dentist", "Pediatrics", "Obstetrics & Gynecology"]
PAGE = 200          # API max per request
MAX_SKIP = 1000     # API won't skip past this
OUT = Path("data/raw/providers")


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
    for z in ZIPS:
        for s in SPECIALTIES:
            rows = fetch(z, s)
            slug = s.lower().replace(" & ", "_").replace(" ", "_")
            path = OUT / f"nppes_{z}_{slug}.json"
            path.write_text(json.dumps({"zip": z, "specialty": s, "results": rows}, indent=1))
            print(f"{path.name}: {len(rows)} results")
            time.sleep(0.5)


if __name__ == "__main__":
    main()
