"""Shared geography helpers: New Brunswick center, distance, Middlesex ZIP list."""
import csv
import math
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
