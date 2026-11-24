"""Build config/middlesex_zips.csv from Census ZCTA files.

Inputs (data/raw/geo/, Middlesex rows extracted from the national Census files):
  zcta_county_middlesex.txt   2020 ZCTA-to-county relationship file
    https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt
  zcta_centroids_middlesex.txt  2024 Gazetteer ZCTA file (internal point lat/long)
    https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_zcta_national.zip

Output columns:
  zip, pct_land_in_middlesex, lat, lng, miles_to_nb,
  in_middlesex  (1 if >= 50% of the ZIP's land is in Middlesex),
  within_15mi   (1 if the ZIP's center is within 15 miles of New Brunswick),
  in_scope      (in_middlesex AND within_15mi: the ZIPs fetch scripts query)

Note: ZCTAs exclude PO-box-only ZIPs (e.g. 08903, 08906). Practice addresses use
street ZIPs, so this list is what address filtering needs.
"""
import csv
from pathlib import Path

from geo import RADIUS_MI, miles

RAW = Path("data/raw/geo")
OUT = Path("config/middlesex_zips.csv")


def main():
    share = {}
    with open(RAW / "zcta_county_middlesex.txt") as f:
        for r in csv.DictReader(f, delimiter="|"):
            share[r["GEOID_ZCTA5_20"]] = int(r["AREALAND_PART"]) / int(r["AREALAND_ZCTA5_20"])
    rows = []
    with open(RAW / "zcta_centroids_middlesex.txt") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            z = r["GEOID"].strip()
            lat, lng = float(r["INTPTLAT"]), float(r["INTPTLONG"].strip())
            d = miles(lat, lng)
            in_mx = share[z] >= 0.5
            within = d <= RADIUS_MI
            rows.append({"zip": z, "pct_land_in_middlesex": round(100 * share[z], 1),
                         "lat": lat, "lng": lng, "miles_to_nb": round(d, 1),
                         "in_middlesex": int(in_mx), "within_15mi": int(within),
                         "in_scope": int(in_mx and within)})
    missing = set(share) - {r["zip"] for r in rows}
    if missing:
        raise SystemExit(f"no centroid for {sorted(missing)}")
    rows.sort(key=lambda r: r["miles_to_nb"])
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n = sum(r["in_scope"] for r in rows)
    print(f"{len(rows)} ZIPs touch Middlesex; {n} in scope (>=50% in Middlesex, within {RADIUS_MI:g} mi) -> {OUT}")


if __name__ == "__main__":
    main()
