"""Clean HRSA health center sites + SAMHSA treatment facilities into one clinics table.

Run from the repo root:  python scripts/clean_clinics.py
Inputs:  data/raw/clinics/Health_Center_Service_Delivery_and_LookAlike_Sites.csv (HRSA)
         data/raw/clinics/samhsa.json (FindTreatment.gov, 15 mi around New Brunswick)
         data/manual/free_clinics.csv (hand-built free/student-run clinics, optional)
Outputs: data/clean/clinics.csv, data/clean/clinics.json, data/reports/clinics_report.md
Exit code 1 if any error-level validation check fails.

Scope: Middlesex County and within 15 miles of New Brunswick.
- HRSA has a county column -> State = NJ, county = Middlesex, Active sites.
- SAMHSA has no county -> keep facilities whose ZIP is an in-scope Middlesex ZIP
  (config/middlesex_zips.csv), then keep only those that take Medicaid or offer a
  sliding fee / payment assistance / free (government-funded) care.
"""
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from geo import RADIUS_MI, county_at, geocode_batch, load_zips, miles
from report import Report

RAW = Path("data/raw/clinics")
MANUAL = Path("data/manual/free_clinics.csv")
TODAY = date.today().isoformat()
HRSA_URL = "https://data.hrsa.gov/data/download"
SAMHSA_URL = ("https://findtreatment.gov/locator/exportsAsJson/v2?sAddr=%2240.4862,-74.4518%22"
              "&limitType=2&limitValue=24140&pageSize=2000&page=1")
# FQHCs must offer a sliding fee scale and serve everyone regardless of ability to pay
FQHC_RULE_URL = "https://bphc.hrsa.gov/compliance/compliance-manual/chapter9"

# SAMHSA payment values that count as "help for people without money or insurance"
FREE_FUNDS = {
    "SAMHSA funding/block grants", "Community Mental Health Block Grants",
    "Community Service Block Grants", "County or local government funds",
    "Federal, or any government funding for substance use treatment programs",
    "State mental health agency (or equivalent) funds", "Other State funds",
    "Private or Community foundation",
}
CARE_TYPES = {  # SAMHSA TC values -> short tags
    "Mental health treatment": "mental_health",
    "Substance use treatment": "substance_use",
    "Detoxification": "detox",
    "Transitional housing, halfway house, or sober home": "sober_housing",
    "Treatment for co-occurring disorders plus serious mental illness (SMI) in adults": "co_occurring",
    "Treatment for co-occurring disorders plus serious emotional disturbance (SED) in children": "co_occurring",
}
SAMHSA_TYPE = {"MH": "mental_health", "SA": "substance_use", "OTP": "opioid_treatment"}

COLUMNS = [
    "clinic_id", "source", "name", "organization", "clinic_type", "address", "city", "state",
    "zip", "county", "phone", "website", "lat", "lng", "miles_to_nb", "location_type",
    "setting", "hours_per_week", "care_types", "service_settings", "accepts_medicaid",
    "accepts_medicare", "accepts_private_insurance", "accepts_self_pay", "sliding_fee",
    "free_care", "languages", "serves_children", "serves_adults", "emergency_mh",
    "has_dental", "walk_in", "notes", "source_url", "last_verified",
]


def clean_phone(v):
    d = re.sub(r"\D", "", str(v or ""))
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    return f"({d[:3]}) {d[3:6]}-{d[6:]}" if len(d) == 10 else None


def clean_url(v):
    v = str(v or "").strip()
    if not v or v.lower() in {"nan", "none"}:
        return None
    return v if v.startswith("http") else "https://" + v


def blank(v):
    return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == ""


# ---------------------------------------------------------------------------
def hrsa(rep, zips):
    df = pd.read_csv(RAW / "Health_Center_Service_Delivery_and_LookAlike_Sites.csv", dtype=str)
    rep.count(f"HRSA: {len(df)} rows read (all US)")
    county = df["Complete County Name"].fillna("").str.upper()
    df = df[(df["Site State Abbreviation"] == "NJ") & county.str.contains("MIDDLESEX")]
    rep.count(f"HRSA: {len(df)} NJ sites in Middlesex")
    inactive = df[df["Site Status Description"] != "Active"]
    for _, r in inactive.iterrows():
        rep.count(f"HRSA: dropped {r['Site Name']} (status {r['Site Status Description']})")
    df = df[df["Site Status Description"] == "Active"]

    rows = []
    for _, r in df.iterrows():
        lat = float(r["Geocoding Artifact Address Primary Y Coordinate"])   # Y = latitude
        lng = float(r["Geocoding Artifact Address Primary X Coordinate"])   # X = longitude
        dist = round(miles(lat, lng), 1)
        if dist > RADIUS_MI:
            rep.count(f"HRSA: dropped {r['Site Name']} ({dist} mi from New Brunswick)")
            continue
        mobile = r["Health Center Location Type Description"] == "Mobile"
        setting = r["Health Center Service Delivery Site Location Setting Description"]
        look_alike = "Look-Alike" in str(r["Health Center Type"])
        rows.append({
            "clinic_id": "hrsa-" + r["BPHC Assigned Number"].replace("BPS-H80-", ""),
            "source": "hrsa",
            "name": r["Site Name"].strip(),
            "organization": r["Health Center Name"].strip(),
            "clinic_type": "fqhc_look_alike" if look_alike else "fqhc",
            "address": r["Site Address"].strip(),
            "city": r["Site City"].strip(),
            "state": "NJ",
            "zip": str(r["Site Postal Code"])[:5],
            "county": "Middlesex",
            "phone": clean_phone(r["Site Telephone Number"]),
            "website": clean_url(r["Site Web Address"]),
            "lat": lat, "lng": lng, "miles_to_nb": dist,
            "location_type": "mobile" if mobile else "permanent",
            "setting": None if setting == "Unknown" else setting,
            "hours_per_week": float(r["Operating Hours per Week"]) if not blank(r["Operating Hours per Week"]) else None,
            "care_types": ["primary_care"],
            "service_settings": ["Outpatient"],
            # Health center program rules: Medicaid accepted, sliding fee, nobody turned away
            "accepts_medicaid": True, "accepts_medicare": True,
            "accepts_private_insurance": True, "accepts_self_pay": True,
            "sliding_fee": True, "free_care": None,
            "languages": [], "serves_children": True, "serves_adults": True,
            "emergency_mh": False,
            "has_dental": None, "walk_in": None,
            "notes": ("Mobile van; the address is the home base, call for the schedule."
                      if mobile else None),
            "source_url": HRSA_URL, "last_verified": TODAY,
        })
    rep.count(f"HRSA: {len(rows)} active sites kept within {RADIUS_MI:g} mi")
    rep.warn("HRSA: accepts_medicaid / sliding_fee / accepts_self_pay set to true from the "
             f"health center program rules ({FQHC_RULE_URL}), not from the row itself")
    rep.warn("HRSA: has_dental, walk_in, languages are empty; fill by hand from each site's "
             "website (Site Web Address)")
    sites = {}
    for r in rows:   # same org at the same address = the mobile van's home base
        key = (r["organization"], r["address"])
        if key in sites:
            rep.warn(f"HRSA: {r['name']} shares its address with {sites[key]} "
                     "(mobile unit based at the permanent site); both kept")
        sites[key] = r["name"]
    domains = {}
    for r in rows:
        if r["website"]:
            domains.setdefault(r["organization"], set()).add(r["website"])
    for org, ws in domains.items():
        if len(ws) > 1:
            rep.warn(f"HRSA: {org} lists different websites {sorted(ws)}; check which is right")
    return rows


# ---------------------------------------------------------------------------
def samhsa(rep, zips):
    data = json.loads((RAW / "samhsa.json").read_text())
    raw = data["rows"]
    rep.count(f"SAMHSA: {len(raw)} rows read (15 mi radius, pageSize=2000, "
              f"{data.get('totalPages')} page)")
    in_scope = {z for z, r in zips.items() if r["in_scope"] == "1"}

    merged = {}
    for r in raw:
        r = {k: ("" if v is None and k != "services" else v) for k, v in r.items()}
        z = str(r.get("zip") or "")[:5]
        if z not in in_scope:
            continue
        key = (r["name1"].strip().lower(), r["street1"].strip().lower())
        svc = {}
        for s in r.get("services") or []:
            svc.setdefault(s["f2"], set()).update(x.strip() for x in s["f3"].split(";") if x.strip())
        if key in merged:   # same facility listed once per type (MH / SA / OTP): merge
            m = merged[key]
            m["types"].add(r["typeFacility"])
            for k, v in svc.items():
                m["svc"].setdefault(k, set()).update(v)
            m["dupes"] += 1
        else:
            merged[key] = {"row": r, "types": {r["typeFacility"]}, "svc": svc, "dupes": 0}
    kept_zip = sum(1 + m["dupes"] for m in merged.values())
    rep.count(f"SAMHSA: {kept_zip} rows in in-scope Middlesex ZIPs "
              f"({len(raw) - kept_zip} outside: other counties, NY, or ZIPs mostly outside Middlesex)")
    rep.count(f"SAMHSA: {len(merged)} unique facilities after merging duplicate name+street rows "
              f"({sum(m['dupes'] for m in merged.values())} duplicates merged)")

    rows, no_svc, no_pay, out_county = [], [], [], []
    for m in merged.values():
        r, svc = m["row"], m["svc"]
        if not svc:
            no_svc.append(r["name1"])
            continue
        pay = svc.get("PAY", set())
        pyas = svc.get("PYAS", set())
        medicaid = "Medicaid" in pay
        sliding = any(x.startswith("Sliding fee") for x in pyas)
        assist = any(x.startswith("Payment assistance") for x in pyas)
        free = bool(pay & FREE_FUNDS)
        if not (medicaid or sliding or assist or free):
            no_pay.append(r["name1"])
            continue
        if r["latitude"] and r["longitude"]:
            lat, lng = float(r["latitude"]), float(r["longitude"])
        else:   # fall back to the ZIP centroid
            zr = zips[str(r["zip"])[:5]]
            lat, lng = float(zr["lat"]), float(zr["lng"])
            rep.warn(f"SAMHSA: {r['name1']}: no lat/long, used ZIP {r['zip']} centroid")
        dist = round(miles(lat, lng), 1)
        if dist > RADIUS_MI:
            rep.count(f"SAMHSA: dropped {r['name1']} ({dist} mi)")
            continue
        if zips[str(r["zip"])[:5]]["pct_land_in_middlesex"] != "100.0" and r["latitude"]:
            cty = county_at(lat, lng)   # split ZIP: check the real county
            if cty is None:
                rep.warn(f"SAMHSA: {r['name1']}: county lookup failed, kept on ZIP alone")
            elif cty != "Middlesex":
                out_county.append(f"{r['name1']} ({r['city']}, {cty} County)")
                continue
        langs = set()
        if "Spanish" in svc.get("SL", set()):
            langs.add("Spanish")
        if any(x.startswith("Sign language") for x in svc.get("SL", set())):
            langs.add("Sign language")
        langs |= {x for x in svc.get("OL", set()) if x != "Any Chinese Language"}
        if "Any Chinese Language" in svc.get("OL", set()):
            langs.add("Chinese")
        care = sorted({CARE_TYPES[x] for x in svc.get("TC", set()) if x in CARE_TYPES}
                      | {SAMHSA_TYPE[t] for t in m["types"] if t in SAMHSA_TYPE})
        ages = svc.get("AGE", set())
        n1, n2 = r["name1"].strip(), (r.get("name2") or "").strip()
        if n2 and n2.lower() not in n1.lower():
            # name2 is either the rest of a cut-off name ("... of" + "Middlesex County")
            # or a program/location label
            joiner = " " if re.search(r"\b(of|and|&|for|the)$", n1, re.I) else " — "
            n1 = n1 + joiner + n2
        name = n1
        street = r["street1"].strip() + (f", {r['street2'].strip()}" if r.get("street2") else "")
        if not street:
            rep.warn(f"SAMHSA: {r['name1']} ({r['city']}): no street address listed; "
                     "kept with city/ZIP only, users must call")
            street = None
        sid = hashlib.sha1(f"{r['name1']}|{r['street1']}".lower().encode()).hexdigest()[:10]
        types = m["types"]
        ctype = ("opioid_treatment" if "OTP" in types else
                 "mental_health" if types == {"MH"} else
                 "substance_use" if types == {"SA"} else "behavioral_health")
        rows.append({
            "clinic_id": "samhsa-" + sid,
            "source": "samhsa",
            "name": name,
            "organization": None,
            "clinic_type": ctype,
            "address": street,
            "city": r["city"].strip(),
            "state": r["state"],
            "zip": str(r["zip"])[:5],
            "county": "Middlesex",
            "phone": clean_phone(r.get("phone")),
            "website": clean_url(r.get("website")),
            "lat": lat, "lng": lng, "miles_to_nb": dist,
            "location_type": "permanent",
            "setting": "; ".join(sorted(svc.get("FT", set()))) or None,
            "hours_per_week": None,
            "care_types": care,
            "service_settings": sorted(svc.get("SET", set())),
            "accepts_medicaid": medicaid,
            "accepts_medicare": "Medicare" in pay,
            "accepts_private_insurance": "Private health insurance" in pay,
            "accepts_self_pay": "Cash or self-payment" in pay,
            "sliding_fee": sliding,
            "free_care": free or assist,
            "languages": sorted(langs),
            "serves_children": "Children/Adolescents" in ages,
            "serves_adults": bool(ages & {"Adults", "Young Adults", "Seniors"}),
            "emergency_mh": bool(svc.get("EMS")),
            "has_dental": False, "walk_in": None,
            "notes": None,
            "source_url": SAMHSA_URL, "last_verified": TODAY,
        })
    for n in no_svc:
        rep.warn(f"SAMHSA: {n}: no service data (services = null), payment unknown, dropped. "
                 "Check by hand and add to data/manual/free_clinics.csv if it qualifies")
    rep.count(f"SAMHSA: {len(no_svc)} dropped with no service data")
    rep.count(f"SAMHSA: {len(no_pay)} dropped (no Medicaid, sliding fee, assistance or free care): "
              + "; ".join(sorted(no_pay)))
    rep.count(f"SAMHSA: {len(out_county)} dropped in split ZIPs whose point is outside Middlesex "
              "(Census geocoder): " + "; ".join(out_county))
    rep.count(f"SAMHSA: {len(rows)} facilities kept")
    return rows


# ---------------------------------------------------------------------------
def manual(rep):
    """Hand-built free / student-run clinics. Same columns; lists are '; '-separated."""
    if not MANUAL.exists():
        rep.warn(f"{MANUAL} not found: no free/student-run clinics added")
        return []
    df = pd.read_csv(MANUAL, dtype=str).fillna("")
    rows = []
    for _, r in df.iterrows():
        row = {c: (r[c] if c in r and r[c] != "" else None) for c in COLUMNS}
        for c in ("care_types", "service_settings", "languages"):
            row[c] = [x.strip() for x in (row[c] or "").split(";") if x.strip()]
        for c in ("accepts_medicaid", "accepts_medicare", "accepts_private_insurance",
                  "accepts_self_pay", "sliding_fee", "free_care", "serves_children",
                  "serves_adults", "emergency_mh", "has_dental", "walk_in"):
            row[c] = None if row[c] is None else str(row[c]).strip().lower() in {"true", "1", "yes"}
        for c in ("lat", "lng", "hours_per_week"):
            row[c] = float(row[c]) if row[c] else None
        if row["lat"] is None and row["address"]:
            g = geocode_batch({0: (row["address"], row["city"], "NJ", row["zip"] or "")}).get(0)
            if g:
                row["lat"], row["lng"] = round(g[0], 6), round(g[1], 6)
            else:
                rep.warn(f"{row['clinic_id']}: address didn't geocode")
        if row["lat"] is not None and row["lng"] is not None:
            row["miles_to_nb"] = round(miles(row["lat"], row["lng"]), 1)
        row["source"] = "manual"
        rows.append(row)
    rep.count(f"Manual free/student-run clinics: {len(rows)} rows")
    return rows


def main():
    rep = Report("clinics")
    zips = load_zips()
    rows = hrsa(rep, zips) + samhsa(rep, zips) + manual(rep)
    c = pd.DataFrame(rows)[COLUMNS]

    # --- validation -----------------------------------------------------------
    rep.check_required(c, ["clinic_id", "name", "city", "zip", "clinic_type",
                           "source_url", "last_verified"], "clinic_id")
    rep.check_unique(c, "clinic_id")
    for _, r in c.iterrows():
        if r["zip"] not in zips:
            rep.error(f"{r.clinic_id} {r['name']}: ZIP {r.zip} is not a Middlesex ZIP")
        if pd.isna(r["lat"]) or pd.isna(r["lng"]):
            rep.warn(f"{r.clinic_id} {r['name']}: no lat/long, distance unknown")
        elif not (40.2 < r["lat"] < 40.7 and -74.8 < r["lng"] < -74.1):
            rep.error(f"{r.clinic_id} {r['name']}: lat/long {r.lat},{r.lng} outside the area")
        if r["phone"] is None:
            rep.warn(f"{r.clinic_id} {r['name']}: no phone number")
        if (date.today() - date.fromisoformat(r["last_verified"])).days > 3 * 365:
            rep.warn(f"{r.clinic_id}: last_verified {r.last_verified} is over 3 years old")
    # the same place from two sources (e.g. a health center also listed by SAMHSA)
    seen = {}
    for _, r in c.iterrows():
        k = (re.sub(r"\W", "", str(r["address"]).lower())[:12], r["zip"])
        if k in seen and seen[k][0] != r["source"]:
            rep.warn(f"possible same place in two sources: {seen[k][1]} / {r['name']} ({r.address})")
        seen.setdefault(k, (r["source"], r["name"]))
    rep.warn("Always show 988 (Suicide & Crisis Lifeline) next to mental health results")

    summary = [f"- {k}: {v}" for k, v in c["clinic_type"].value_counts().items()]
    summary += [f"- accepts Medicaid: {int(c.accepts_medicaid.eq(True).sum())}",
                f"- sliding fee: {int(c.sliding_fee.eq(True).sum())}",
                f"- Spanish spoken: {int(c.languages.map(lambda l: 'Spanish' in l).sum())}",
                f"- serves children: {int(c.serves_children.eq(True).sum())}"]
    return rep.write(c, extra_sections={"Summary": summary})


if __name__ == "__main__":
    sys.exit(main())
