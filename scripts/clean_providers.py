"""Clean NPPES results (dentists, pediatrics, OB-GYN) into a providers table.

Run from the repo root:  python scripts/clean_providers.py
Inputs:  data/raw/providers/nppes/*.json (from fetch_nppes.py)
         data/raw/providers/doc_clinics.zip (CMS Doctors & Clinicians, NJ) -> telehealth flag
Outputs: data/clean/providers.csv, data/clean/providers.json, data/reports/providers_report.md
Exit code 1 if any error-level validation check fails.

One row per provider x practice location in scope. The NPPES ZIP search also matches
mailing addresses and secondary locations, so every LOCATION address is checked:
it's geocoded with the Census batch geocoder and kept only if it falls in Middlesex
County and within 15 miles of New Brunswick.
"""
import json
import re
import sys
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

from geo import RADIUS_MI, geocode_batch, load_zips, miles
from report import Report

RAW = Path("data/raw/providers")
TODAY = date.today().isoformat()
NPPES_URL = "https://npiregistry.cms.hhs.gov/api/?version=2.1&number={}"
DAC_URL = "https://data.cms.gov/provider-data/dataset/mj5m-pzi6"
MIDDLESEX_FIPS = "34023"

# taxonomy description -> (specialty, general care?)
def classify(desc):
    d = (desc or "").strip()
    if d.startswith("Dentist") or d == "Clinic/Center, Dental":
        general = d in {"Dentist", "Dentist, General Practice", "Dentist, Pediatric Dentistry",
                        "Dentist, Dental Public Health", "Clinic/Center, Dental"}
        return "dentist", general
    if d.startswith("Pediatrics") or d in {"Nurse Practitioner, Pediatrics",
                                           "Nurse Practitioner, Neonatal"}:
        general = d in {"Pediatrics", "Pediatrics, Adolescent Medicine",
                        "Nurse Practitioner, Pediatrics"}
        return "pediatrics", general
    if d.startswith("Obstetrics & Gynecology") or d in {"Nurse Practitioner, Obstetrics & Gynecology",
                                                        "Nurse Practitioner, Women's Health",
                                                        "Advanced Practice Midwife"}:
        general = d in {"Obstetrics & Gynecology", "Obstetrics & Gynecology, Gynecology",
                        "Obstetrics & Gynecology, Obstetrics",
                        "Nurse Practitioner, Obstetrics & Gynecology",
                        "Nurse Practitioner, Women's Health", "Advanced Practice Midwife"}
        return "obgyn", general
    return None, False


ACRONYMS = {"DDS", "DMD", "MD", "DO", "PC", "LLC", "PA", "NP", "APN", "PLLC", "II", "III",
            "NJ", "USA", "RWJ", "UMDNJ", "CNM", "APRN", "FNP", "LLP", "DNP", "MPH", "MS",
            "PHD", "RN", "CPNP", "WHNP", "OB", "GYN", "OBGYN", "LP"}


def nice(v):
    if not v:
        return None
    out = []
    for w in str(v).strip().split():
        bare = re.sub(r"[^A-Za-z]", "", w).upper()
        out.append(w.upper() if bare in ACRONYMS else w.capitalize())
    return " ".join(out)


def phone(v):
    d = re.sub(r"\D", "", str(v or ""))
    return f"({d[:3]}) {d[3:6]}-{d[6:]}" if len(d) == 10 else None


def load_nppes(rep):
    recs = {}
    files = sorted((RAW / "nppes").glob("*.json"))
    n = 0
    for p in files:
        d = json.loads(p.read_text())
        for r in d["results"]:
            n += 1
            recs[r["number"]] = r
    rep.count(f"NPPES: {len(files)} files, {n} results, {len(recs)} unique NPIs")
    return recs


def telehealth_npis(rep):
    z = zipfile.ZipFile(RAW / "doc_clinics.zip")
    name = next(n for n in z.namelist() if n.endswith(".csv") and not n.startswith("__"))
    df = pd.read_csv(z.open(name), dtype=str, usecols=["NPI", "Telehlth"])
    rep.count(f"Doctors & Clinicians: {len(df)} NJ rows read, "
              f"{df['NPI'].nunique()} NPIs, {int((df['Telehlth'] == 'Y').sum())} rows with Telehlth = Y")
    return set(df.loc[df["Telehlth"] == "Y", "NPI"]), set(df["NPI"])


def main():
    rep = Report("providers")
    zips = load_zips()
    recs = load_nppes(rep)
    tele, dac = telehealth_npis(rep)

    # --- one candidate row per NPI x LOCATION address in a Middlesex ZIP ------
    cands, wrong_tax, inactive = [], 0, 0
    for npi, r in recs.items():
        if r["basic"].get("status") != "A":
            inactive += 1
            continue
        taxes = [(t, *classify(t["desc"])) for t in r["taxonomies"]]
        taxes = [x for x in taxes if x[1]]
        if not taxes:
            wrong_tax += 1
            continue
        taxes.sort(key=lambda x: (not x[0]["primary"], not x[2]))  # primary first, then general
        tax, spec, general = taxes[0]
        locs = [a for a in r["addresses"] if a["address_purpose"] == "LOCATION"]
        locs += r.get("practiceLocations") or []
        seen = set()
        for a in locs:
            z = str(a.get("postal_code", ""))[:5]
            key = (a.get("address_1", "").upper(), z)
            if a.get("state") != "NJ" or z not in zips or key in seen:
                continue
            seen.add(key)
            b = r["basic"]
            if r["enumeration_type"] == "NPI-1":
                name = " ".join(x for x in [nice(b.get("first_name")), nice(b.get("last_name"))] if x)
                cred = (b.get("credential") or "").replace(".", "").strip().upper() or None
                kind = "individual"
            else:
                name = nice(b.get("organization_name"))
                cred = None
                kind = "organization"
            cands.append({
                "npi": npi, "name": name, "credential": cred, "provider_kind": kind,
                "sex": b.get("sex") if kind == "individual" else None,
                "specialty": spec, "taxonomy": tax["desc"], "taxonomy_code": tax["code"],
                "general_care": general,
                "other_specialties": sorted({t["desc"] for t in r["taxonomies"] if t.get("desc")} - {tax["desc"]}),
                "address": nice(" ".join(x for x in [a.get("address_1"), a.get("address_2")] if x)),
                "street_raw": a.get("address_1", ""),
                "city": nice(a.get("city")), "state": "NJ", "zip": z,
                "phone": phone(a.get("telephone_number")),
                "is_primary_location": a in r["addresses"],
                "nppes_last_updated": b.get("last_updated"),
            })
    rep.count(f"NPPES: {inactive} inactive NPIs dropped")
    rep.count(f"NPPES: {wrong_tax} NPIs dropped whose taxonomies aren't dental / pediatric / OB-GYN "
              "(the API's taxonomy search is loose, e.g. medical-equipment suppliers)")
    rep.count(f"Candidate locations (NJ, ZIP touches Middlesex): {len(cands)}")

    # --- geocode, then keep Middlesex + 15 miles --------------------------------
    geo = geocode_batch({i: (c["street_raw"], c["city"], "NJ", c["zip"]) for i, c in enumerate(cands)})
    rows, out_county, out_radius, fallback = [], 0, 0, 0
    for i, c in enumerate(cands):
        g = geo.get(i)
        zr = zips[c["zip"]]
        if g:
            lat, lng, fips = g[:3]
            if fips != MIDDLESEX_FIPS:
                out_county += 1
                continue
            c["geo_precision"] = "address"
        else:
            # not geocoded: keep only if the ZIP is mostly Middlesex, use its centroid
            if zr["in_scope"] != "1" or not zr["lat"]:
                out_county += 1
                continue
            lat, lng = float(zr["lat"]), float(zr["lng"])
            c["geo_precision"] = "zip"
            fallback += 1
        c["lat"], c["lng"] = round(lat, 6), round(lng, 6)
        c["miles_to_nb"] = round(miles(lat, lng), 1)
        if c["miles_to_nb"] > RADIUS_MI:
            out_radius += 1
            continue
        rows.append(c)
    rep.count(f"Dropped {out_county} locations outside Middlesex County (Census geocoder) "
              "or in an unmatched address in a mostly-outside ZIP")
    rep.count(f"Dropped {out_radius} locations over {RADIUS_MI:g} miles from New Brunswick")
    if fallback:
        rep.warn(f"{fallback} addresses didn't geocode; used the ZIP centroid (geo_precision = zip)")

    p = pd.DataFrame(rows)
    p["county"] = "Middlesex"
    p["telehealth"] = p["npi"].map(lambda n: True if n in tele else (False if n in dac else None))
    p["accepts_medicaid"] = None      # hand-filled; NPPES doesn't say
    p["sliding_fee"] = None
    p["accepting_new_patients"] = None
    p["languages"] = [[] for _ in range(len(p))]
    p = p.sort_values(["specialty", "miles_to_nb", "name"]).reset_index(drop=True)
    p["location_seq"] = p.groupby("npi").cumcount() + 1
    p["provider_id"] = p["npi"] + "-" + p["location_seq"].astype(str)
    p["source_url"] = p["npi"].map(NPPES_URL.format)
    p["last_verified"] = TODAY
    cols = ["provider_id", "npi", "name", "credential", "provider_kind", "sex", "specialty",
            "taxonomy", "taxonomy_code", "general_care", "other_specialties", "address", "city",
            "state", "zip", "county", "phone", "lat", "lng", "geo_precision", "miles_to_nb",
            "is_primary_location", "telehealth", "accepts_medicaid", "sliding_fee",
            "accepting_new_patients", "languages", "nppes_last_updated", "source_url",
            "last_verified"]
    p = p[cols]

    # --- validation -----------------------------------------------------------
    rep.check_required(p, ["provider_id", "npi", "name", "specialty", "address", "city", "zip",
                           "lat", "lng", "source_url", "last_verified"], "provider_id")
    rep.check_unique(p, "provider_id")
    bad_npi = p.loc[~p["npi"].str.fullmatch(r"\d{10}"), "npi"]
    for n in bad_npi:
        rep.error(f"{n}: NPI is not 10 digits")
    nophone = int(p["phone"].isna().sum())
    if nophone:
        rep.warn(f"{nophone} locations have no phone number")
    stale = p[pd.to_datetime(p["nppes_last_updated"]) < pd.Timestamp(date.today()) - pd.Timedelta(days=3 * 365)]
    if len(stale):
        rep.warn(f"{len(stale)} locations from NPIs not updated in NPPES for over 3 years "
                 "(addresses may be out of date; prefer recently updated rows)")
    multi = p.groupby(["address", "zip"]).size()
    rep.warn(f"{int((multi > 1).sum())} addresses host several providers (group practices); fine, "
             "but the app should group them when listing")
    rep.warn("accepts_medicaid, sliding_fee, accepting_new_patients, languages: not in NPPES; "
             "fill by hand for the providers the app shows first")
    rep.warn("telehealth is only known for Medicare-enrolled clinicians (NULL = not in Doctors & Clinicians)")

    summary = [f"- {s}: {n} locations ({g} general care)" for s, n, g in
               p.groupby("specialty").agg(n=("npi", "size"), g=("general_care", "sum")).itertuples()]
    summary += [f"- unique NPIs: {p['npi'].nunique()}",
                f"- organizations: {int((p.provider_kind == 'organization').sum())}",
                f"- telehealth = true: {int(p.telehealth.eq(True).sum())}",
                f"- geocoded to the address: {int((p.geo_precision == 'address').sum())}"]
    return rep.write(p, extra_sections={"Summary": summary})


if __name__ == "__main__":
    sys.exit(main())
