"""Clean the three CMS hospital files into one row per hospital.

Run from the repo root:  python scripts/clean_hospitals.py
Inputs:  data/raw/hospitals/CMS.csv (General Info), survey.csv (HCAHPS), timely.csv
Outputs: data/clean/hospitals.csv, data/clean/hospitals.json,
         data/reports/hospitals_report.md
Exit code 1 if any error-level validation check fails.
"""
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from geo import RADIUS_MI, geocode_batch, load_zips, miles

RAW = Path("data/raw/hospitals")
CLEAN = Path("data/clean")
REPORTS = Path("data/reports")
MANUAL_PEDS = Path("data/manual/hospital_pediatrics.csv")
SOURCES = {
    "general": "https://data.cms.gov/provider-data/dataset/xubh-q36u",
    "survey": "https://data.cms.gov/provider-data/dataset/dgck-syfz",
    "timely": "https://data.cms.gov/provider-data/dataset/yv7e-xc69",
}
SURVEY_MEASURES = {
    "H_STAR_RATING": ("survey_star", "Patient Survey Star Rating"),
    "H_COMP_1_STAR_RATING": ("nurse_comm_star", "Patient Survey Star Rating"),
    "H_COMP_2_STAR_RATING": ("doctor_comm_star", "Patient Survey Star Rating"),
    "H_RECMND_DY": ("recommend_pct", "HCAHPS Answer Percent"),
    "H_HSP_RATING_9_10": ("rating_9_10_pct", "HCAHPS Answer Percent"),
}
ER_MEASURES = {"OP_18b": "er_median_minutes", "OP_22": "er_left_unseen_pct", "EDV": "er_volume"}
MISSING = {"Not Available", "Not Applicable", ""}


ACRONYMS = {"JFK", "RWJ", "NJ", "UMC", "HMH"}


def nice(v):
    """CMS names are ALL CAPS: title-case them, keeping apostrophes and acronyms."""
    words = str(v).strip().split()
    return " ".join(w.upper() if w.upper() in ACRONYMS else w.capitalize() for w in words)


def num(v):
    """CMS uses text like 'Not Available' for missing; return int or None."""
    if pd.isna(v) or str(v).strip() in MISSING:
        return None
    return int(float(v))


def text(v):
    return None if pd.isna(v) or str(v).strip() in MISSING else str(v).strip()


def iso(v):
    return None if text(v) is None else pd.to_datetime(v, format="%m/%d/%Y").date().isoformat()


def main():
    report = {"counts": [], "errors": [], "warnings": [], "coverage": {}}

    # --- General Information: the base list ---------------------------------
    g = pd.read_csv(RAW / "CMS.csv", dtype=str)
    report["counts"].append(f"General Information: {len(g)} rows read (NJ)")
    county = g["County/Parish"].fillna("").str.strip().str.upper()
    blank = g[county == ""]
    for _, r in blank.iterrows():
        report["warnings"].append(f"{r['Facility ID']} {r['Facility Name']}: blank county, dropped")
    g = g[(g["State"] == "NJ") & (county == "MIDDLESEX")].copy()
    report["counts"].append(f"In Middlesex: {len(g)} hospitals")

    zips = load_zips()
    # street address -> lat/lng (Census geocoder); ZIP centroid if that fails
    geo = geocode_batch({r["Facility ID"]: (r["Address"], r["City/Town"], "NJ", str(r["ZIP Code"]).zfill(5)[:5])
                         for _, r in g.iterrows()})
    rows = []
    for _, r in g.iterrows():
        z = str(r["ZIP Code"]).zfill(5)[:5]
        zr = zips.get(z)
        lat = lng = dist = None
        gc = geo.get(r["Facility ID"])
        if gc:
            lat, lng = round(gc[0], 6), round(gc[1], 6)
            dist = round(miles(lat, lng), 1)
        elif zr and zr["lat"]:
            lat, lng, dist = float(zr["lat"]), float(zr["lng"]), float(zr["miles_to_nb"])
            report["warnings"].append(f"{r['Facility ID']} {r['Facility Name']}: address didn't "
                                      "geocode, using the ZIP centroid")
        else:
            report["warnings"].append(
                f"{r['Facility ID']} {r['Facility Name']}: address didn't geocode and ZIP {z} has "
                f"no Census centroid (PO-box ZIP); distance unknown, kept because it's in Middlesex")
        if dist is not None and dist > RADIUS_MI:
            report["counts"].append(f"Dropped {r['Facility Name']}: {dist} mi from New Brunswick")
            continue
        rows.append({
            "facility_id": r["Facility ID"].strip(),
            "name": nice(r["Facility Name"]),
            "address": nice(r["Address"]),
            "city": nice(r["City/Town"]),
            "state": r["State"],
            "zip": z,
            "county": nice(r["County/Parish"]),
            "phone": text(r["Telephone Number"]),
            "hospital_type": r["Hospital Type"].strip(),
            "ownership": text(r["Hospital Ownership"]),
            "has_emergency": r["Emergency Services"].strip() == "Yes",
            "birthing_friendly": text(r["Meets criteria for birthing friendly designation"]) == "Y",
            "overall_rating": num(r["Hospital overall rating"]),
            "lat": lat, "lng": lng, "miles_to_nb": dist,
        })
    h = pd.DataFrame(rows).set_index("facility_id")
    h["overall_rating"] = h["overall_rating"].astype("Int64")
    ids = set(h.index)

    # --- HCAHPS: pivot the chosen measures to one row per hospital -----------
    s = pd.read_csv(RAW / "survey.csv", dtype=str)
    s = s[s["Facility ID"].isin(ids) & s["HCAHPS Measure ID"].isin(SURVEY_MEASURES)]
    report["counts"].append(f"HCAHPS: {len(s)} rows kept ({len(SURVEY_MEASURES)} measures x hospitals)")
    for mid, (col, src) in SURVEY_MEASURES.items():
        vals = s[s["HCAHPS Measure ID"] == mid].set_index("Facility ID")[src].map(num)
        h[col] = vals.reindex(h.index).astype("Int64")
    star = s[s["HCAHPS Measure ID"] == "H_STAR_RATING"].set_index("Facility ID")
    h["survey_count"] = star["Number of Completed Surveys"].map(num).reindex(h.index).astype("Int64")
    h["survey_period_end"] = star["End Date"].map(iso).reindex(h.index)

    # --- Timely & Effective Care: ER rows only --------------------------------
    t = pd.read_csv(RAW / "timely.csv", dtype=str)
    t = t[t["Facility ID"].isin(ids) & t["Measure ID"].isin(ER_MEASURES)]
    report["counts"].append(f"Timely & Effective Care: {len(t)} ER rows kept")
    for mid, col in ER_MEASURES.items():
        m = t[t["Measure ID"] == mid].set_index("Facility ID")
        conv = text if mid == "EDV" else num
        vals = m["Score"].map(conv).reindex(h.index)
        h[col] = vals if mid == "EDV" else vals.astype("Int64")
    op18 = t[t["Measure ID"] == "OP_18b"].set_index("Facility ID")
    h["er_period_end"] = op18["End Date"].map(iso).reindex(h.index)

    # --- manual columns from data/manual/hospital_pediatrics.csv + provenance ---
    h["source_url"] = SOURCES["general"]
    peds = pd.read_csv(MANUAL_PEDS, dtype=str).fillna("") if MANUAL_PEDS.exists() else pd.DataFrame()
    peds = peds.set_index("facility_id") if len(peds) else peds
    tf = {"true": True, "false": False}
    h["has_pediatric_er"] = [tf.get(peds.at[i, "has_pediatric_er"]) if i in peds.index else None for i in h.index]
    h["has_childrens_hospital"] = [tf.get(peds.at[i, "has_childrens_hospital"]) if i in peds.index else None for i in h.index]
    h["pediatric_specialties"] = [
        [x.strip() for x in peds.at[i, "pediatric_specialties"].split(";") if x.strip()] or None
        if i in peds.index else None for i in h.index]
    h["pediatric_source_url"] = [peds.at[i, "source_url"] or None if i in peds.index else None for i in h.index]
    h["last_verified"] = date.today().isoformat()
    h = h.reset_index()

    # --- validation -----------------------------------------------------------
    required = ["facility_id", "name", "address", "city", "zip", "hospital_type"]
    for c in required:
        for fid in h.loc[h[c].isna(), "facility_id"]:
            report["errors"].append(f"{fid}: missing required field {c}")
    if h["facility_id"].duplicated().any():
        report["errors"].append(f"duplicate facility_id: {sorted(h.loc[h.facility_id.duplicated(), 'facility_id'])}")
    for _, r in h.iterrows():
        if r["has_emergency"] and pd.isna(r["er_median_minutes"]):
            report["warnings"].append(f"{r.facility_id} {r['name']}: has an ER but no median ER time")
        if pd.isna(r["survey_star"]):
            report["warnings"].append(f"{r.facility_id} {r['name']}: no patient survey star rating")
        if pd.notna(r["er_median_minutes"]) and not 30 <= r["er_median_minutes"] <= 600:
            report["warnings"].append(f"{r.facility_id}: unusual ER time {r['er_median_minutes']} min")
        for p in ("survey_period_end", "er_period_end"):
            if pd.notna(r[p]) and (date.today() - date.fromisoformat(r[p])).days > 3 * 365:
                report["warnings"].append(f"{r.facility_id}: {p} {r[p]} is over 3 years old")
    for _, r in h.iterrows():
        if r["has_pediatric_er"] is None:
            report["warnings"].append(f"{r.facility_id} {r['name']}: pediatric columns not filled "
                                      f"(data/manual/hospital_pediatrics.csv); check the hospital website")
    for c in h.columns:
        report["coverage"][c] = round(100 * h[c].map(lambda v: v is not None and not (isinstance(v, float) and pd.isna(v))).mean())

    # --- write outputs --------------------------------------------------------
    CLEAN.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    h.assign(pediatric_specialties=h["pediatric_specialties"].map(
        lambda v: "; ".join(v) if isinstance(v, list) else v)).to_csv(CLEAN / "hospitals.csv", index=False)
    recs = json.loads(h.to_json(orient="records"))
    (CLEAN / "hospitals.json").write_text(json.dumps(recs, indent=2))
    write_report(report, h)
    print(f"{len(h)} hospitals -> {CLEAN/'hospitals.csv'}  "
          f"({len(report['errors'])} errors, {len(report['warnings'])} warnings)")
    return 1 if report["errors"] else 0


def write_report(rep, h):
    lines = [f"# Validation report: hospitals", f"*Run {date.today().isoformat()}*", "",
             f"**Result:** {'FAILED' if rep['errors'] else 'PASSED'} — "
             f"{len(h)} rows, {len(rep['errors'])} errors, {len(rep['warnings'])} warnings", "",
             "## Counts", *[f"- {c}" for c in rep["counts"]], "",
             "## Errors (block loading)", *([f"- {e}" for e in rep["errors"]] or ["- none"]), "",
             "## Warnings (review)", *([f"- {w}" for w in rep["warnings"]] or ["- none"]), "",
             "## Coverage (% of rows filled)", "| column | % |", "| --- | --- |",
             *[f"| {c} | {v} |" for c, v in rep["coverage"].items()], ""]
    (REPORTS / "hospitals_report.md").write_text("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
