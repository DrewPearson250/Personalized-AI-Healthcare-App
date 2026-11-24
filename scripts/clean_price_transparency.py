"""Prefilter the hospital price transparency files into two small tables.

Run from the repo root:  python scripts/clean_price_transparency.py   (several minutes: files are GBs)
Inputs:  data/raw/price_transparency/<facility_id>.csv|.json + manifest.json
         (fetch_price_transparency.py; CMS v3 tall CSV or JSON,
          spec https://github.com/CMSgov/hospital-price-transparency)
Outputs (data/clean/ + data/reports/):
  hospital_payers  unique payer + plan names per hospital (= who the hospital has contracts with),
                   mapped to a brand and a product line (commercial / medicaid / medicare)
  hospital_prices  for a short list of common services: gross charge, cash price, min/max
                   negotiated, and the negotiated rate per payer + plan
Exit code 1 if any error-level validation check fails.
"""
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import ijson
import pandas as pd

from report import Report

RAW = Path("data/raw/price_transparency")
TODAY = date.today().isoformat()

# Common services people ask about (subset of CMS's shoppable services). code -> (label, group)
SERVICES = {
    "99281": ("ER visit, level 1 (minor)", "emergency"),
    "99282": ("ER visit, level 2", "emergency"),
    "99283": ("ER visit, level 3 (moderate)", "emergency"),
    "99284": ("ER visit, level 4 (high)", "emergency"),
    "99285": ("ER visit, level 5 (severe)", "emergency"),
    "99202": ("Office visit, new patient (15-29 min)", "office"),
    "99203": ("Office visit, new patient (30-44 min)", "office"),
    "99213": ("Office visit, established patient (20-29 min)", "office"),
    "99214": ("Office visit, established patient (30-39 min)", "office"),
    "59400": ("Vaginal delivery with prenatal and postpartum care", "maternity"),
    "59409": ("Vaginal delivery only", "maternity"),
    "59510": ("Cesarean delivery with prenatal and postpartum care", "maternity"),
    "59514": ("Cesarean delivery only", "maternity"),
    "76805": ("Pregnancy ultrasound", "maternity"),
    "71046": ("Chest X-ray, 2 views", "imaging"),
    "73030": ("Shoulder X-ray", "imaging"),
    "73610": ("Ankle X-ray", "imaging"),
    "70450": ("CT head/brain without contrast", "imaging"),
    "74177": ("CT abdomen and pelvis with contrast", "imaging"),
    "72148": ("MRI lower back without contrast", "imaging"),
    "76700": ("Abdominal ultrasound", "imaging"),
    "77067": ("Screening mammogram", "imaging"),
    "80053": ("Comprehensive metabolic panel (blood test)", "lab"),
    "85025": ("Complete blood count (CBC)", "lab"),
    "80061": ("Cholesterol (lipid) panel", "lab"),
    "83036": ("Hemoglobin A1c (diabetes test)", "lab"),
    "81001": ("Urinalysis", "lab"),
    "36415": ("Blood draw", "lab"),
    "93000": ("Electrocardiogram (EKG)", "other"),
    "90471": ("Vaccine administration", "other"),
}
CODE_TYPES = {"CPT", "HCPCS"}

BRANDS = [  # (regex on "payer plan", brand) - first match wins
    (r"braven", "Braven Health"), (r"horizon", "Horizon"), (r"aetna", "Aetna"),
    (r"oxford|united|uhc|americhoice|optum", "UnitedHealthcare"), (r"amerihealth", "AmeriHealth"),
    (r"cigna|evernorth", "Cigna"), (r"wellcare|fidelis|ambetter", "WellCare"),
    (r"wellpoint|amerigroup|anthem|empire", "Wellpoint/Anthem"), (r"oscar", "Oscar"),
    (r"humana", "Humana"), (r"clover", "Clover Health"), (r"qualcare", "QualCare"),
    (r"magnacare", "MagnaCare"), (r"multiplan|phcs", "MultiPlan"), (r"1199", "1199SEIU"),
    (r"tricare", "TRICARE"), (r"medicaid|nj ?familycare", "NJ Medicaid (fee-for-service)"),
    (r"medicare", "Medicare"),
]
MEDICAID = r"medicaid|familycare|mercy|community plan|managed md|\bmd\b|better health|njfc|dsnp|d-snp"
MEDICARE = r"medicare|advantage|\bmc\b|\bma\b|braven|senior|dual"


def brand(payer, plan):
    s = f"{payer} {plan}".lower()
    return next((b for rx, b in BRANDS if re.search(rx, s)), None)


def product(payer, plan):
    s = f"{payer} {plan}".lower()
    if re.search(r"dsnp|d-snp|dual", s):
        return "medicare_medicaid"
    if re.search(MEDICAID, s):
        return "medicaid"
    if re.search(MEDICARE, s):
        return "medicare"
    return "commercial"


def num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
def scan_csv(path, payers, prices, meta):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        r = csv.reader(f)
        h1, v1 = next(r), next(r)
        meta.update({k: v for k, v in zip(h1, v1) if k in
                     ("hospital_name", "last_updated_on", "version", "location_name")})
        cols = next(r)
        ix = {c.lower(): i for i, c in enumerate(cols)}
        code_cols = [(ix[c], ix.get(c + "|type")) for c in ix if re.fullmatch(r"code\|\d+", c)]
        g = lambda row, c: row[ix[c]] if c in ix and ix[c] < len(row) else ""
        n = 0
        for row in r:
            n += 1
            payer, plan = g(row, "payer_name").strip(), g(row, "plan_name").strip()
            if payer:
                payers[(payer, plan)] += 1
            code = next((row[c] for c, t in code_cols
                         if c < len(row) and row[c] in SERVICES and t is not None
                         and row[t].upper() in CODE_TYPES), None)
            if not code:
                continue
            setting = g(row, "setting").lower() or "both"
            prices.append({
                "code": code, "description_raw": g(row, "description"), "setting": setting,
                "modifiers": g(row, "modifiers") or None,
                "billing_class": g(row, "billing_class").lower() or None,
                "gross_charge": num(g(row, "standard_charge|gross")),
                "discounted_cash": num(g(row, "standard_charge|discounted_cash")),
                "min_negotiated": num(g(row, "standard_charge|min")),
                "max_negotiated": num(g(row, "standard_charge|max")),
                "payer_name": payer or None, "plan_name": plan or None,
                "negotiated_dollar": num(g(row, "standard_charge|negotiated_dollar")),
                "negotiated_percentage": num(g(row, "standard_charge|negotiated_percentage")),
                "methodology": g(row, "standard_charge|methodology") or None,
            })
    return n


def scan_json(path, payers, prices, meta):
    with open(path, "rb") as f:
        head = {}
        for prefix, event, value in ijson.parse(f):
            if prefix in ("hospital_name", "last_updated_on", "version") and event in ("string",):
                head[prefix] = value
            if prefix == "standard_charge_information":
                break
    meta.update(head)
    n = 0
    with open(path, "rb") as f:
        for item in ijson.items(f, "standard_charge_information.item", use_float=True):
            codes = [c["code"] for c in item.get("code_information", [])
                     if c.get("type", "").upper() in CODE_TYPES and c.get("code") in SERVICES]
            for sc in item.get("standard_charges", []):
                for p in sc.get("payers_information", []) or []:
                    n += 1
                    payers[(p.get("payer_name", "").strip(), p.get("plan_name", "").strip())] += 1
                if not codes:
                    continue
                base = {"code": codes[0], "description_raw": item.get("description"),
                        "setting": (sc.get("setting") or "both").lower(),
                        "modifiers": "|".join(sc.get("modifier_code", []) or []) or None,
                        "billing_class": (sc.get("billing_class") or "").lower() or None,
                        "gross_charge": num(sc.get("gross_charge")),
                        "discounted_cash": num(sc.get("discounted_cash")),
                        "min_negotiated": num(sc.get("minimum")),
                        "max_negotiated": num(sc.get("maximum"))}
                pis = sc.get("payers_information") or [{}]
                for p in pis:
                    prices.append({**base,
                                   "payer_name": p.get("payer_name"), "plan_name": p.get("plan_name"),
                                   "negotiated_dollar": num(p.get("standard_charge_dollar")),
                                   "negotiated_percentage": num(p.get("standard_charge_percentage")),
                                   "methodology": p.get("methodology")})
    return n


def main():
    manifest = json.loads((RAW / "manifest.json").read_text())
    rp, rs = Report("hospital_payers"), Report("hospital_prices")
    hosp = pd.read_csv("data/clean/hospitals.csv", dtype=str).set_index("facility_id")
    payer_rows, price_rows = [], []
    for fid in hosp.index:
        files = [p for p in RAW.glob(f"{fid}.*") if p.suffix in (".csv", ".json")]
        if not files:
            for rep in (rp, rs):
                rep.warn(f"{fid} {hosp.at[fid, 'name']}: no price file (see fetch_price_transparency.py)")
            continue
        path = files[0]
        m = manifest.get(fid, {})
        src = m.get("mrf_url") or m.get("source_page_url") or str(path.name)
        payers, prices, meta = defaultdict(int), [], {}
        n = (scan_json if path.suffix == ".json" else scan_csv)(path, payers, prices, meta)
        rp.count(f"{fid} {hosp.at[fid, 'name']}: {n:,} charge rows scanned, "
                 f"{len(payers)} payer+plan pairs, file version {meta.get('version')}, "
                 f"last updated {meta.get('last_updated_on')}")
        rs.count(f"{fid}: {len(prices):,} rows for the {len(SERVICES)} common services")
        lu = meta.get("last_updated_on")
        try:
            lu = pd.to_datetime(lu).date().isoformat() if lu else None   # "1/8/2026" -> ISO
        except (ValueError, TypeError):
            rp.warn(f"{fid}: unparseable last_updated_on {lu!r}")
            lu = None
        for (payer, plan), cnt in payers.items():
            if not payer:
                continue
            payer_rows.append({"facility_id": fid, "payer_name": payer, "plan_name": plan or None,
                               "brand": brand(payer, plan), "product": product(payer, plan),
                               "charge_rows": cnt, "file_last_updated": lu,
                               "source_url": src, "last_verified": TODAY})
        for p in prices:
            p.update(facility_id=fid, file_last_updated=lu, source_url=src, last_verified=TODAY)
            price_rows.append(p)
        if lu:
            try:
                age = (date.today() - pd.to_datetime(lu).date()).days
                if age > 365:
                    rs.warn(f"{fid}: price file last updated {lu}, over a year old")
            except (ValueError, TypeError):
                rs.warn(f"{fid}: unparseable last_updated_on {lu!r}")

    # --- hospital_payers --------------------------------------------------------
    hp = pd.DataFrame(payer_rows)
    hp["payer_id"] = hp["facility_id"] + "|" + hp["payer_name"] + "|" + hp["plan_name"].fillna("")
    hp = hp[["payer_id"] + [c for c in hp.columns if c != "payer_id"]]
    rp.check_unique(hp, "payer_id")
    nob = hp[hp.brand.isna()]
    if len(nob):
        rp.warn(f"{len(nob)} payer+plan pairs with no brand mapping (shown under the payer name): "
                + "; ".join(sorted(set(nob.payer_name))[:40]))
    rp.warn("product (commercial / medicaid / medicare) is a keyword guess from payer and plan "
            "names; check the ones the app shows")
    summ = [f"- {fid}: {len(g)} pairs, brands: " + ", ".join(sorted(set(g.brand.dropna())))
            for fid, g in hp.groupby("facility_id")]
    code_p = rp.write(hp, extra_sections={"Summary": summ})

    # --- hospital_prices -------------------------------------------------------
    pr = pd.DataFrame(price_rows)
    pr["service"] = pr["code"].map(lambda c: SERVICES[c][0])
    pr["service_group"] = pr["code"].map(lambda c: SERVICES[c][1])
    pr["brand"] = [brand(a or "", b or "") if a else None for a, b in zip(pr.payer_name, pr.plan_name)]
    key = ["facility_id", "code", "setting", "billing_class", "modifiers", "payer_name", "plan_name"]
    vals = ["gross_charge", "discounted_cash", "min_negotiated", "max_negotiated",
            "negotiated_dollar", "negotiated_percentage", "methodology"]
    # the same charge is often listed under several chargemaster items: drop exact repeats only
    dup = pr.duplicated(key + vals, keep="first")
    rs.count(f"{int(dup.sum())} repeated rows dropped (same code, setting, billing class, "
             "modifiers, payer, plan and the same prices)")
    pr = pr[~dup].copy()
    multi = pr.duplicated(key, keep=False)
    if multi.any():
        rs.warn(f"{int(multi.sum())} rows share code/setting/payer/plan but list different prices "
                "(different chargemaster items); all kept, show the range")
    pr["variant"] = pr.groupby(key, dropna=False).cumcount() + 1
    pr["price_id"] = pr[key].fillna("").astype(str).agg("|".join, axis=1) + "|" + pr["variant"].astype(str)
    cols = ["price_id", "facility_id", "code", "service", "service_group", "description_raw",
            "setting", "billing_class", "modifiers", "gross_charge", "discounted_cash", "min_negotiated",
            "max_negotiated", "payer_name", "plan_name", "brand", "negotiated_dollar",
            "negotiated_percentage", "methodology", "file_last_updated", "source_url", "last_verified"]
    pr = pr[cols].sort_values(["facility_id", "code", "setting", "payer_name"], na_position="first")
    rs.check_unique(pr, "price_id")
    for (fid, code), g in pr.groupby(["facility_id", "code"]):
        cash = g.discounted_cash.dropna()
        gross = g.gross_charge.dropna()
        if len(cash) and len(gross) and (cash.max() > gross.max() * 1.01):
            rs.warn(f"{fid} {code}: cash price {cash.max():,.0f} above gross charge {gross.max():,.0f}")
    for fid in pr.facility_id.unique():
        missing = sorted(set(SERVICES) - set(pr.loc[pr.facility_id == fid, "code"]))
        if missing:
            rs.warn(f"{fid}: no rows for {len(missing)} services: {', '.join(missing)}")
    cash = (pr.dropna(subset=["discounted_cash"]).groupby(["code", "facility_id"])["discounted_cash"]
            .min().unstack())
    summary = ["Lowest listed cash price per service ($):", "",
               "| code | service | " + " | ".join(cash.columns) + " |",
               "| --- | --- | " + " | ".join("---" for _ in cash.columns) + " |"]
    for code, row in cash.iterrows():
        summary.append(f"| {code} | {SERVICES[code][0]} | " +
                       " | ".join("" if pd.isna(v) else f"{v:,.0f}" for v in row) + " |")
    rs.warn("Cash prices are the hospital's listed self-pay rate before Charity Care; "
            "physician fees are usually billed separately")
    code_s = rs.write(pr, extra_sections={"Cash prices": summary})
    return 1 if (code_p or code_s) else 0


if __name__ == "__main__":
    sys.exit(main())
