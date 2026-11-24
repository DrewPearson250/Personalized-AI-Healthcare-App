"""Build the services table (non-medical help) from the hand-built lists.

Run from the repo root:  python scripts/clean_services.py
Inputs:  data/manual/services.csv            hand-entered services (benefits, housing, legal, ...)
         data/manual/food_guide_extracted.csv food pantries / meals (from extract_food_guide.py)
Outputs: data/clean/services.csv, data/clean/services.json, data/reports/services_report.md

Local entries are geocoded (Census) and kept only in Middlesex County within 15 miles.
Entries with no street address (hotlines, statewide programs) are kept with scope = statewide.
embed_text is the text the service matcher embeds (name + category + description + eligibility).
Every row stays verified = false until a person checks it against its source_url.
"""
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from geo import RADIUS_MI, geocode_batch, miles
from report import Report

MANUAL = Path("data/manual/services.csv")
FOOD = Path("data/manual/food_guide_extracted.csv")
MIDDLESEX_FIPS = "34023"
CATEGORIES = {"food", "housing", "transportation", "prescriptions", "benefits", "legal",
              "domestic_violence", "immigrant", "utilities", "mental_health", "other"}
# municipalities and postal place names in Middlesex County (for entries that don't geocode)
MIDDLESEX_PLACES = {
    "carteret", "cranbury", "dunellen", "east brunswick", "edison", "helmetta", "highland park",
    "jamesburg", "metuchen", "middlesex", "milltown", "monroe", "monroe township", "new brunswick",
    "north brunswick", "old bridge", "perth amboy", "piscataway", "plainsboro", "sayreville",
    "south amboy", "south brunswick", "south plainfield", "south river", "spotswood", "woodbridge",
    "iselin", "avenel", "colonia", "fords", "hopelawn", "keasbey", "port reading", "sewaren",
    "parlin", "kendall park", "monmouth junction", "dayton", "kingston", "laurence harbor",
    "somerset", "matawan"}
FOOD_GUIDE_DATE = "2025-03-01"   # "Spring 2025" edition


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50]


def phone(v):
    d = re.sub(r"\D", "", str(v or ""))
    if len(d) == 10:
        return f"({d[:3]}) {d[3:6]}-{d[6:]}"
    return str(v).strip() if v and str(v) != "nan" else None


def food_rows(rep):
    f = pd.read_csv(FOOD, dtype=str).fillna("")
    rep.count(f"Food guide: {len(f)} entries extracted")
    rows = []
    for _, r in f.iterrows():
        addr, city = r["address"], r["city"]
        notes = []
        if r["review"]:
            # keep the first "street, City" of a merged address; the rest belonged to other entries
            m = re.match(r"(.+?),\s*([A-Za-z .]+?)\s+\d", addr + " " + city)
            if m:
                addr, city = m.group(1).strip(), m.group(2).strip()
            notes.append("address auto-split from a merged PDF entry, check")
        # city sometimes swallowed the start of the description ("South Amboy Free groceries.")
        cm = re.match(r"(.+?)\s+((?:Free|Prepared|Serving)\b.*)", city)
        desc = r["description"]
        if cm:
            city, desc = cm.group(1), (cm.group(2) + " " + desc).strip()
        city = re.sub(r"\s+Township$", "", city)
        desc = desc or "Free food."
        rows.append({
            "service_id": "food-" + slug(r["name"] + "-" + addr),
            "name": r["name"], "organization": r["name"], "category": "food",
            "description": desc,
            "eligibility": ("Rutgers students only" if "Rutgers Student" in r["name"] else
                            "Ages 59+ and/or homebound" if "Meals on Wheels" in r["name"] else ""),
            "address": addr, "city": city, "zip": "", "phone": r["phone"],
            "hours": r["hours"], "languages": "", "cost": "Free",
            "documents_needed": "; ".join(x for x in [
                "proof of address" if re.search(r"proof of (address|residence)", desc, re.I) else "",
                "proof of income" if re.search(r"proof of income", desc, re.I) else "",
                "photo ID" if re.search(r"photo id", desc, re.I) else "",
                "birth certificates for minors" if re.search(r"birth certificate", desc, re.I) else "",
                "student ID" if re.search(r"student id", desc, re.I) else ""] if x),
            "nearest_bus_stop": r["nearest_bus_stop"],
            "source_url": r["source_url"], "source_date": FOOD_GUIDE_DATE,
            "last_verified": date.today().isoformat(), "verified": False,
            "notes": "; ".join(notes) or None,
        })
    return rows


def manual_rows(rep):
    m = pd.read_csv(MANUAL, dtype=str).fillna("")
    rep.count(f"Hand-built services: {len(m)} rows")
    rows = []
    for _, r in m.iterrows():
        d = r.to_dict()
        d["verified"] = d.get("verified", "").lower() == "true"
        d["nearest_bus_stop"] = ""
        d["source_date"] = None
        d["notes"] = None
        rows.append(d)
    return rows


def main():
    rep = Report("services")
    rows = manual_rows(rep) + food_rows(rep)
    s = pd.DataFrame(rows)

    # --- geocode local entries -------------------------------------------------
    local = s[s["address"].str.strip() != ""]
    geo = geocode_batch({i: (r["address"], r["city"], "NJ", r["zip"]) for i, r in local.iterrows()})
    keep, out_county, out_radius, nogeo = [], [], 0, []
    for i, r in s.iterrows():
        r = r.to_dict()
        if not r["address"].strip():
            r.update(scope="statewide" if not r["city"] else "local", lat=None, lng=None, miles_to_nb=None)
            keep.append(r)
            continue
        g = geo.get(i)
        if not g:
            if r["city"].strip().lower() not in MIDDLESEX_PLACES:
                out_county.append(f"{r['name']} ({r['city']}, not geocoded, not a Middlesex place)")
                continue
            nogeo.append(f"{r['name']} ({r['address']}, {r['city']})")
            r.update(scope="local", lat=None, lng=None, miles_to_nb=None)
            keep.append(r)
            continue
        lat, lng, fips = g[:3]
        if fips != MIDDLESEX_FIPS:
            out_county.append(f"{r['name']} ({r['city']})")
            continue
        dist = round(miles(lat, lng), 1)
        if dist > RADIUS_MI:
            out_radius += 1
            continue
        if not r["zip"] and len(g) > 3 and g[3]:
            r["zip"] = g[3]
        r.update(scope="local", lat=round(lat, 6), lng=round(lng, 6), miles_to_nb=dist)
        keep.append(r)
    rep.count(f"Dropped {len(out_county)} outside Middlesex County: " + "; ".join(out_county))
    rep.count(f"Dropped {out_radius} over {RADIUS_MI:g} miles")
    for n in nogeo:
        rep.warn(f"address didn't geocode, kept without distance: {n}")

    s = pd.DataFrame(keep)
    s["phone"] = s["phone"].map(phone)
    s["languages"] = s["languages"].map(lambda v: [x.strip() for x in str(v).split(";") if x.strip()])
    s["embed_text"] = s.apply(lambda r: ". ".join(x for x in [
        r["name"], r["category"].replace("_", " "), r["description"],
        f"Who can use it: {r['eligibility']}" if r["eligibility"] else "",
        f"In {r['city']}" if r["city"] else "Statewide"] if x), axis=1)
    for c in ("eligibility", "address", "city", "zip", "hours", "cost", "documents_needed",
              "nearest_bus_stop"):
        s[c] = s[c].replace("", None)
    cols = ["service_id", "name", "organization", "category", "description", "eligibility",
            "address", "city", "zip", "phone", "hours", "languages", "cost", "documents_needed",
            "nearest_bus_stop", "lat", "lng", "miles_to_nb", "scope", "embed_text", "verified",
            "notes", "source_url", "source_date", "last_verified"]
    s = s[cols].sort_values(["category", "miles_to_nb"], na_position="last").reset_index(drop=True)

    # --- validation -----------------------------------------------------------
    rep.check_required(s, ["service_id", "name", "category", "description", "source_url",
                           "last_verified"], "service_id")
    rep.check_unique(s, "service_id")
    for _, r in s.iterrows():
        if r["category"] not in CATEGORIES:
            rep.error(f"{r.service_id}: unknown category {r.category}")
        if r["phone"] is None and r["scope"] == "local":
            rep.warn(f"{r.service_id}: no phone number")
        if r["notes"]:
            rep.warn(f"{r.service_id}: {r.notes}")
    old = s[s.source_date.notna()]
    if len(old):
        rep.warn(f"{len(old)} food entries come from the Spring 2025 Rutgers guide: hours change "
                 "often, re-check before launch")
    rep.warn(f"verified = false for all {int((~s.verified).sum())} rows: a person must check each "
             "against its source_url (catalog rule: hand-built lists get a human check)")
    rep.warn("Set aside (sites blocked automated reading, add by hand later; see current_stage.md): "
             "Middlesex County Board of Social Services, Woman Aware (local DV program), Coming Home "
             "of Middlesex, Central Jersey Legal Services")
    summary = [f"- {k}: {v}" for k, v in s.category.value_counts().items()]
    summary.append(f"- statewide (no address): {int((s.scope == 'statewide').sum())}")
    return rep.write(s, extra_sections={"Summary": summary})


if __name__ == "__main__":
    sys.exit(main())
