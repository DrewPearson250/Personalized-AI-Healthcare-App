"""Download the price transparency (standard charges) files for the in-scope hospitals.

Run from the repo root:  python scripts/fetch_price_transparency.py
Each hospital publishes /cms-hpt.txt listing its machine-readable file (MRF) URL
(CMS spec: https://github.com/CMSgov/hospital-price-transparency). This script reads
that index, finds the hospital's entry by location-name, and streams the file to
data/raw/price_transparency/<facility_id>.<ext>. Files are large (100 MB - 2.5 GB);
existing files are skipped (delete to refresh). A manifest records URL, size, date.

Penn Medicine Princeton (310010): princetonhcs.org blocks scripted requests. Download
its file in a browser from the price transparency page and save it as
data/raw/price_transparency/310010.csv (or .json); clean_price_transparency.py will pick it up.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests

OUT = Path("data/raw/price_transparency")
UA = {"User-Agent": "Mozilla/5.0 (CareBridge NB data pipeline)"}
HOSPITALS = {
    # facility_id: (cms-hpt.txt URL, location-name in that file)
    "310038": ("https://www.rwjbh.org/cms-hpt.txt", "Robert Wood Johnson University Hospital"),
    "313300": ("https://www.rwjbh.org/cms-hpt.txt", "Childrens Specialized Hospital"),
    "310070": ("https://www.saintpetershcs.com/cms-hpt.txt", "Saint Peters University Hospital"),
    "310108": ("https://www.hackensackmeridianhealth.org/cms-hpt.txt", "JFK University Medical Center"),
    "310039": ("https://www.hackensackmeridianhealth.org/cms-hpt.txt", "Raritan Bay Medical Center"),
    "310010": ("https://www.princetonhcs.org/cms-hpt.txt", "Princeton"),
}


def parse_hpt(text):
    """cms-hpt.txt -> list of {location-name, mrf-url, source-page-url, ...} blocks."""
    entries, cur = [], {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            if cur:
                entries.append(cur)
                cur = {}
            continue
        m = re.match(r"([a-z-]+):\s*(.*)", line)
        if m:
            if m.group(1) == "location-name" and "location-name" in cur:
                entries.append(cur)
                cur = {}
            cur[m.group(1)] = m.group(2).strip()
    if cur:
        entries.append(cur)
    return entries


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    cache = {}
    for fid, (hpt, loc) in HOSPITALS.items():
        if fid in manifest and (OUT / manifest[fid]["file"]).exists():
            print(f"{fid}: already downloaded, skipping")
            continue
        try:
            if hpt not in cache:
                r = requests.get(hpt, headers=UA, timeout=60)
                r.raise_for_status()
                cache[hpt] = parse_hpt(r.text)
            entries = [e for e in cache[hpt] if e.get("location-name", "").strip() == loc]
            if not entries:
                print(f"{fid}: no '{loc}' entry in {hpt} (blocked or renamed); download by hand")
                continue
            url = entries[0]["mrf-url"]
        except Exception as e:  # noqa: BLE001
            print(f"{fid}: couldn't read {hpt}: {e}; download by hand")
            continue
        ext = "json" if url.lower().endswith(".json") else "csv"
        dest = OUT / f"{fid}.{ext}"
        tmp = dest.with_suffix(dest.suffix + ".part")
        print(f"{fid}: downloading {url}")
        with requests.get(url, headers=UA, stream=True, timeout=120) as r:
            r.raise_for_status()
            size = 0
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
                    size += len(chunk)
        tmp.rename(dest)
        manifest[fid] = {"file": dest.name, "location_name": loc, "mrf_url": url, "hpt_url": hpt,
                         "source_page_url": entries[0].get("source-page-url"),
                         "bytes": size, "downloaded": date.today().isoformat()}
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"{fid}: {size / 1e6:,.0f} MB -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
