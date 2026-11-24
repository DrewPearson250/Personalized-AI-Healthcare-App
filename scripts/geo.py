"""Shared geography helpers: New Brunswick center, distance, Middlesex ZIP list."""
import csv
import math
import re
from pathlib import Path

NB_LAT, NB_LNG = 40.4862, -74.4518   # New Brunswick center (same point as the SAMHSA query)
RADIUS_MI = 15.0
ZIPS_CSV = Path("config/middlesex_zips.csv")


def miles(lat1, lng1, lat2=NB_LAT, lng2=NB_LNG):
    """Great-circle distance in miles (haversine)."""
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_zips(path=ZIPS_CSV):
    """{zip: row} for every Middlesex ZIP, values as strings from the CSV."""
    with open(path, newline="") as f:
        return {r["zip"]: r for r in csv.DictReader(f)}


def query_zips(path=ZIPS_CSV):
    """ZIPs to query APIs with: mostly in Middlesex and center within 15 miles."""
    return sorted(z for z, r in load_zips(path).items() if r["in_scope"] == "1")


# ---------------------------------------------------------------------------
# Census geocoder (free, no key). Results are cached in data/raw/geo/ so
# re-running a cleaning script doesn't hit the API again.
CENSUS = "https://geocoding.geo.census.gov/geocoder"
CACHE = Path("data/raw/geo/census_cache.json")
_cache = None


def _load_cache():
    global _cache
    if _cache is None:
        import json
        _cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    return _cache


def _save_cache():
    import json
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(_cache, indent=0, sort_keys=True))


def county_at(lat, lng):
    """County name (e.g. 'Middlesex') for a point, or None if the lookup fails."""
    import requests
    cache = _load_cache()
    key = f"pt:{lat:.5f},{lng:.5f}"
    if key not in cache:
        try:
            r = requests.get(f"{CENSUS}/geographies/coordinates", timeout=30, params={
                "x": lng, "y": lat, "benchmark": "Public_AR_Current",
                "vintage": "Current_Current", "layers": "Counties", "format": "json"})
            c = r.json()["result"]["geographies"]["Counties"]
            cache[key] = c[0]["BASENAME"] if c else None
        except Exception:
            return None
        _save_cache()
    return cache[key]


def geocode_batch(addresses):
    """{id: [lat, lng, county_fips, zip] or None} for {id: (street, city, state, zip)}.

    Uses the Census batch geocoder (up to 10,000 rows per call); cached by address.
    """
    import csv
    import io
    import requests
    cache = _load_cache()
    out, todo = {}, {}
    for i, a in addresses.items():
        k = "addr:" + "|".join(str(x).upper().strip() for x in a)
        if k in cache:
            out[i] = cache[k]
        else:
            todo[i] = (k, a)
    items = list(todo.items())
    for start in range(0, len(items), 5000):
        chunk = items[start:start + 5000]
        buf = io.StringIO()
        w = csv.writer(buf)
        for n, (i, (k, a)) in enumerate(chunk):
            w.writerow([n, *a])
        r = requests.post(f"{CENSUS}/geographies/addressbatch", timeout=600,
                          files={"addressFile": ("a.csv", buf.getvalue())},
                          data={"benchmark": "Public_AR_Current", "vintage": "Current_Current"})
        r.raise_for_status()
        got = {}
        for row in csv.reader(io.StringIO(r.text)):
            if len(row) >= 6 and row[2] == "Match":
                lng, lat = map(float, row[5].split(","))
                # row[8] = state FIPS, row[9] = county FIPS
                fips = (row[8] + row[9]) if len(row) > 9 else ""
                mz = re.search(r"(\d{5})\s*$", row[4])   # matched address ends in the ZIP
                got[int(row[0])] = [lat, lng, fips, mz.group(1) if mz else None]
        for n, (i, (k, a)) in enumerate(chunk):
            cache[k] = got.get(n)
            out[i] = cache[k]
        _save_cache()
    return out
