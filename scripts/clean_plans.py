"""Clean the 2026 NJ marketplace plan files + DOBI enrollment into four tables.

Run from the repo root:  python scripts/clean_plans.py
Inputs:  data/raw/insurance/NJPlans05072026.csv, NJRates05072026.csv,
         NJBenefits05072026.csv, NJServiceAreas05072026.csv  (CMS SBE QHP PUF, NJ 2026)
         data/raw/insurance/dobi_enrollment_2026q2.csv        (from extract_dobi.py)
Outputs (data/clean/ + data/reports/<name>_report.md):
  plans           one row per plan variant sold in Middlesex (standard + silver CSR variants)
  plan_rates      monthly full-price premium by plan, rating area and age
  plan_benefits   covered yes/no + limits per plan and benefit (standard variants only)
  insurers_local  DOBI Q2 2026 Middlesex enrollment per insurer, with brand + marketplace link
Exit code 1 if any error-level validation check fails.
"""
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from report import Report

RAW = Path("data/raw/insurance")
TODAY = date.today().isoformat()
SBE_URL = "https://www.cms.gov/marketplace/resources/data/state-based-public-use-files"
DOBI_URL = "https://www.nj.gov/dobi/lifehealthactuarial/26health02.pdf"
GCNJ_URL = "https://nj.gov/getcoverednj"

# ISSUER NAME is blank in the file; names from SERVICE AREA NAME / plan names
ISSUERS = {
    "17970": "Ambetter from WellCare of New Jersey",
    "23818": "Oscar Health",
    "37777": "UnitedHealthcare (Oxford)",
    "91661": "Horizon Blue Cross Blue Shield of New Jersey",
    "91762": "AmeriHealth New Jersey",
    "48608": "Dentegra",
    "93627": "Guardian",
    "99708": "Delta Dental of New Jersey",
    "35152": "Dominion Dental Services, Inc.",   # dental-only "Choice PPO"; blank in the file, filled by hand
}
# CSR VARIATION TYPE -> short code. Zero/limited cost-sharing variants are only for
# members of federally recognized tribes; dropped for v1.
CSR = {
    "Standard Silver On Exchange Plan": "standard", "Standard Bronze On Exchange Plan": "standard",
    "Standard Gold On Exchange Plan": "standard", "Standard Catastrophic On Exchange Plan": "standard",
    "Standard Low On Exchange Plan": "standard", "Standard High On Exchange Plan": "standard",
    "73% AV Level Silver Plan": "csr_73", "87% AV Level Silver Plan": "csr_87",
    "94% AV Level Silver Plan": "csr_94",
}

# DOBI insurer (legal entity) -> brand people recognize, and its marketplace ISSUER ID
DOBI_BRANDS = {
    "HBCBS of NJ": ("Horizon", "91661"),
    "Horizon HC of NJ, Inc": ("Horizon", "91661"),
    "Aetna Better Health Inc.": ("Aetna", None),
    "Aetna Health, Inc.": ("Aetna", None),
    "Aetna Life Ins Co": ("Aetna", None),
    "AmeriChoice": ("UnitedHealthcare", "37777"),
    "Oxford Health Ins, Inc": ("UnitedHealthcare", "37777"),
    "Oxford Health Plans of NJ, Inc": ("UnitedHealthcare", "37777"),
    "United HealthCare Ins Co": ("UnitedHealthcare", "37777"),
    "AmeriGroup (Wellpoint)": ("Wellpoint", None),
    "Wellpoint Life & Health Ins Co (formerly UniCare)": ("Wellpoint", None),
    "AmeriHealth HMO": ("AmeriHealth", "91762"),
    "AmeriHealth Ins Co": ("AmeriHealth", "91762"),
    "CIGNA Health & Life Ins Co": ("Cigna", None),
    "CIGNA HealthCare of New Jersey, Inc": ("Cigna", None),
    "Oscar Insurance Company of New Jersey": ("Oscar", "23818"),
    "WellCare Health Plans of New Jersey, Inc.": ("WellCare", "17970"),
}


def money(v):
    """'$2,500 ' -> 2500.0; 'Not Applicable' / blank -> None."""
    if pd.isna(v):
        return None
    m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", str(v))
    return float(m.group(1).replace(",", "")) if m else None


def family_group(v):
    """'$2500 per person | $5000 per group' -> 5000.0"""
    if pd.isna(v):
        return None
    m = re.search(r"\$([\d,]+(?:\.\d+)?)\s*per group", str(v))
    return float(m.group(1).replace(",", "")) if m else None


def pct(v):
    if pd.isna(v):
        return None
    m = re.search(r"([\d.]+)\s*%", str(v))
    return float(m.group(1)) if m else None


def yes(v):
    return None if pd.isna(v) else str(v).strip().lower() == "yes"


def sbc_total(r, what):
    """Cost-example total the member pays: deductible + copays + coinsurance + limits."""
    parts = [money(r[c]) for c in r.index if c.startswith("SBC HAVING") and what in c]
    parts = [p for p in parts if p is not None]
    return sum(parts) if parts else None


# ---------------------------------------------------------------------------
def plans_table():
    rep = Report("plans")
    sa = pd.read_csv(RAW / "NJServiceAreas05072026.csv", dtype=str)
    pl = pd.read_csv(RAW / "NJPlans05072026.csv", dtype=str)
    rep.count(f"Service areas: {len(sa)} rows; plans: {len(pl)} plan variants")
    serves = sa[(sa["COUNTY NAME"] == "Middlesex") | (sa["COVER ENTIRE STATE"].str.lower() == "true")]
    partial = serves[serves["PARTIAL COUNTY"].str.lower() == "true"]
    if len(partial):
        rep.warn(f"{len(partial)} Middlesex service areas are partial-county (ZIP lists): "
                 f"{sorted(set(partial['ISSUER ID'] + '/' + partial['SERVICE AREA ID']))}")
    keys = set(zip(serves["ISSUER ID"], serves["SERVICE AREA ID"]))
    rep.count(f"Service areas serving Middlesex (county row or whole state): {len(keys)}")
    mx = pl[[k in keys for k in zip(pl["ISSUER ID"], pl["SERVICE AREA ID"])]]
    rep.count(f"Plan variants in those service areas: {len(mx)} "
              f"({len(pl) - len(mx)} dropped, service area doesn't reach Middlesex)")
    tribal = mx[~mx["CSR VARIATION TYPE"].isin(CSR)]
    rep.count(f"Dropped {len(tribal)} zero/limited cost-sharing variants (tribal members only)")
    mx = mx[mx["CSR VARIATION TYPE"].isin(CSR)]

    rows = []
    for _, r in mx.iterrows():
        dental = r["DENTAL ONLY PLAN"] == "Yes"
        ded_col = "MEHB DED INN TIER1 INDIVIDUAL" if dental else "TEHB DED INN TIER 1 INDIVIDUAL"
        ded_fam = "MEHB DED INN TIER1 FAMILY" if dental else "TEHB DED INN TIER 1 FAMILY"
        moop_col = "MEHB INN TIER 1 INDIVIDUAL MOOP" if dental else "TEHB INN TIER 1 INDIVIDUAL MOOP"
        moop_fam = "MEHB INN TIER 1 FAMILY MOOP" if dental else "TEHB INN TIER 1 FAMILY MOOP"
        rows.append({
            "plan_id": r["PLAN ID"],
            "standard_component_id": r["STANDARD COMPONENT ID"],
            "issuer_id": r["ISSUER ID"],
            "issuer_name": ISSUERS.get(r["ISSUER ID"]),
            "plan_name": r["PLAN MARKETING NAME"].strip(),
            "variant_name": (r["PLAN VARIANT MARKETING NAME"] or "").strip() or None,
            "dental_only": dental,
            "plan_type": r["PLAN TYPE"],
            "metal_level": r["METAL LEVEL"],
            "csr_variant": CSR[r["CSR VARIATION TYPE"]],
            "actuarial_value_pct": pct(r["ISSUER ACTUARIAL VALUE"]),
            "deductible_individual": money(r[ded_col]),
            "deductible_family": family_group(r[ded_fam]),
            "coinsurance_pct": pct(r.get("TEHB DED INN TIER 1 COINSURANCE")) if not dental else None,
            "moop_individual": money(r[moop_col]),
            "moop_family": family_group(r[moop_fam]),
            "hsa_eligible": yes(r["IS HSA ELIGIBLE"]),
            "referral_required": yes(r["IS REFERRAL REQUIRED FOR SPECIALIST"]),
            "out_of_network_coverage": not dental and r["PLAN TYPE"] in {"PPO", "POS"},
            "child_only_offering": r["CHILD ONLY OFFERING"],
            "cost_having_baby": None if dental else sbc_total(r, "BABY"),
            "cost_diabetes": None if dental else sbc_total(r, "DIABETES"),
            "cost_simple_fracture": None if dental else sbc_total(r, "FRACTURE"),
            "plan_year": int(r["BUSINESS YEAR"]),
            "enroll_url": GCNJ_URL,
            "source_url": SBE_URL,
            "last_verified": TODAY,
        })
    p = pd.DataFrame(rows)
    rep.check_required(p, ["plan_id", "issuer_id", "plan_name", "metal_level", "csr_variant",
                           "source_url", "last_verified"], "plan_id")
    rep.check_unique(p, "plan_id")
    for _, r in p.iterrows():
        if r["issuer_name"] is None:
            rep.warn(f"{r.plan_id} ({r.plan_name}): issuer {r.issuer_id} has no name in the file; "
                     "look it up (HIOS issuer ID) and add it to ISSUERS")
        if not r["dental_only"] and r["deductible_individual"] is None:
            rep.error(f"{r.plan_id}: medical plan with no in-network deductible")
        if (r["deductible_individual"] is not None and r["moop_individual"] is not None
                and r["deductible_individual"] > r["moop_individual"]):
            rep.error(f"{r.plan_id}: deductible {r.deductible_individual} > out-of-pocket max "
                      f"{r.moop_individual}")
    # CSR sanity: silver deductibles should fall as the variant gets richer
    med = p[~p.dental_only & (p.metal_level == "Silver")]
    by = med.groupby("csr_variant")["deductible_individual"].median()
    rep.count("Median silver deductible by variant: " +
              ", ".join(f"{k} ${v:,.0f}" for k, v in by.items()))
    if not (by.get("standard", 0) >= by.get("csr_73", 0) >= by.get("csr_87", 0) >= by.get("csr_94", 0)):
        rep.error("silver CSR deductibles don't fall standard > 73 > 87 > 94")
    std = p[~p.dental_only & (p.csr_variant == "standard")]
    rep.count(f"Medical plans (standard variants): {len(std)} from {std.issuer_id.nunique()} insurers; "
              + ", ".join(f"{k} {v}" for k, v in std.metal_level.value_counts().items()))
    rep.count(f"Dental-only plans: {int(p.dental_only.sum())}")
    if (std.plan_type != "EPO").any():
        rep.warn("some medical plans aren't EPOs: " + str(std.plan_type.value_counts().to_dict()))
    rep.warn("Premiums and deductibles are full price before financial help; the subsidy is "
             "calculated by Get Covered NJ. Plan brochure/SBC/formulary URLs are empty in the file, "
             "so link to Get Covered NJ")
    rep.warn("cost_having_baby / cost_diabetes / cost_simple_fracture = sum of the SBC "
             "deductible + copay + coinsurance + limit amounts (the 'Coverage Examples' total)")
    return rep.write(p), p


def rates_table(plans):
    rep = Report("plan_rates")
    r = pd.read_csv(RAW / "NJRates05072026.csv", dtype=str)
    rep.count(f"Rates: {len(r)} rows read")
    ids = set(plans["standard_component_id"])
    r = r[r["PLAN ID"].isin(ids)]
    rep.count(f"Rates for plans sold in Middlesex: {len(r)}")
    out = pd.DataFrame({
        "standard_component_id": r["PLAN ID"],
        "issuer_id": r["ISSUER ID"],
        "rating_area": r["RATING AREA ID"].str.replace("Rating Area ", "", regex=False).astype(int),
        "age": r["AGE"].replace({"0-14": "0", "64 and over": "64"}).astype(int),
        "age_label": r["AGE"],
        "monthly_premium": r["INDIVIDUAL RATE"].astype(float),
        "tobacco_premium": pd.to_numeric(r["INDIVIDUAL TOBACCO RATE"], errors="coerce"),
        "rate_effective": r["RATE EFFECTIVE DATE"],
        "rate_expiration": r["RATE EXPIRATION"],
        "source_url": SBE_URL,
        "last_verified": TODAY,
    })
    out["rate_id"] = (out["standard_component_id"] + "-" + out["rating_area"].astype(str)
                      + "-" + out["age"].astype(str))
    out = out[["rate_id"] + [c for c in out.columns if c != "rate_id"]]
    rep.check_unique(out, "rate_id")
    rep.check_required(out, ["rate_id"], "rate_id")
    missing = ids - set(out["standard_component_id"])
    for m in sorted(missing):
        rep.error(f"plan {m} has no rates")
    # $0 = plan not sold at that age (child-only dental / pediatric plans): store NULL
    zero = out[out.monthly_premium <= 0]
    for plan, g in zero.groupby("standard_component_id"):
        rep.warn(f"{plan}: $0 premium for ages {g.age.min()}-{g.age.max()} "
                 f"({g.rating_area.nunique()} rating area(s)) -> stored as NULL (not offered at that age)")
    out.loc[out.monthly_premium <= 0, ["monthly_premium", "tobacco_premium"]] = None
    for _, b in out[out.monthly_premium > 5000].iterrows():
        rep.warn(f"{b.rate_id}: odd premium {b.monthly_premium}")
    # NJ's individual market is one rating area. A plan priced in several areas only matters if
    # the prices differ (Horizon lists its dental plans in 6 areas at identical prices).
    for plan, g in out.groupby("standard_component_id"):
        if g["rating_area"].nunique() > 1:
            differ = g.groupby("age")["monthly_premium"].nunique(dropna=True).max() > 1
            if differ:
                rep.warn(f"{plan}: prices differ across rating areas; confirm which area is Middlesex")
            else:
                rep.count(f"{plan}: listed in {g.rating_area.nunique()} rating areas at identical prices")
    if (out.tobacco_premium.notna() & (out.tobacco_premium != out.monthly_premium)).any():
        rep.warn("some plans charge tobacco users more")
    return rep.write(out)


def benefits_table(plans):
    rep = Report("plan_benefits")
    b = pd.read_csv(RAW / "NJBenefits05072026.csv", dtype=str)
    rep.count(f"Benefits: {len(b)} rows read")
    std = plans[plans.csr_variant == "standard"]
    b = b[b["PLAN ID"].isin(set(std["plan_id"]))]
    rep.count(f"Rows for standard plan variants sold in Middlesex: {len(b)} "
              "(CSR variants have the same covered services, only cost sharing differs)")
    out = pd.DataFrame({
        "plan_id": b["PLAN ID"],
        "benefit_name": b["BENEFIT NAME"].str.strip(),
        "is_covered": b["IS COVERED"].map(yes),
        "is_ehb": b["IS EHB"].map(yes),
        "quantity_limit": b["QUANTITY LIMIT ON SVC"].map(yes),
        "limit_quantity": pd.to_numeric(b["LIMIT QUANTITY"], errors="coerce"),
        "limit_unit": b["LIMIT UNIT"],
        "exclusions": b["EXCLUSIONS"],
        "explanation": b["EXPLANATION"],
        "subject_to_deductible": b["IS SUBJECTED TO DED TIER 1"].map(yes),
        "source_url": SBE_URL,
        "last_verified": TODAY,
    })
    out["benefit_id"] = out["plan_id"] + "|" + out["benefit_name"]
    out = out[["benefit_id"] + [c for c in out.columns if c != "benefit_id"]]
    rep.check_unique(out, "benefit_id")
    unk = out[out.is_covered.isna()]
    if len(unk):
        rep.warn(f"{len(unk)} rows with blank IS COVERED (treated as unknown)")
    vals = set(b["IS COVERED"].dropna())
    if vals - {"Yes", "No"}:
        rep.warn(f"unexpected IS COVERED values: {vals}")
    med = out[out.plan_id.isin(std[~std.dental_only].plan_id)]
    for name in ["Routine Dental Services (Adult)", "Routine Eye Exam (Adult)",
                 "Dental Check-Up for Children"]:
        sub = med[med.benefit_name == name]
        if len(sub):
            rep.count(f"Medical plans covering '{name}': {int(sub.is_covered.fillna(False).sum())} "
                      f"of {len(sub)}")
    return rep.write(out)


def insurers_table():
    rep = Report("insurers_local")
    d = pd.read_csv(RAW / "dobi_enrollment_2026q2.csv", dtype=str)
    rep.count(f"DOBI: {len(d)} rows read (long format, all counties)")
    m = d[d["county"] == "Middlesex"].copy()
    m["enrollment"] = m["enrollment"].astype(int)
    totals = m[m.insurer == "ALL"].set_index("line")["enrollment"]
    m = m[m.insurer != "ALL"]
    w = m.pivot_table(index=["insurer", "naic"], columns="line", values="enrollment",
                      aggfunc="sum", fill_value=0).reset_index()
    for c in ("comm_net", "comm_non_net", "medicaid", "total"):
        if c not in w:
            w[c] = 0
    zero = w[w.total == 0]
    rep.count(f"Dropped {len(zero)} insurers with 0 Middlesex enrollment: {', '.join(zero.insurer)}")
    w = w[w.total > 0].copy()
    w["brand"] = w["insurer"].map(lambda n: DOBI_BRANDS.get(n, (n, None))[0])
    w["marketplace_issuer_id"] = w["insurer"].map(lambda n: DOBI_BRANDS.get(n, (None, None))[1])
    w["commercial"] = w["comm_net"] + w["comm_non_net"]
    w["is_medicaid_plan"] = w["medicaid"] > 0
    w["share_of_county_pct"] = (100 * w["total"] / totals["county_total_all"]).round(1)
    w = w.sort_values("total", ascending=False).reset_index(drop=True)
    w["rank"] = range(1, len(w) + 1)
    w["brand_rank"] = w["brand"].map(w.groupby("brand")["total"].sum().rank(ascending=False, method="min")).astype(int)
    w["insurer_id"] = w["naic"].str.replace("/", "-", regex=False)
    w["quarter"] = "2026Q2"
    w["source_url"] = DOBI_URL
    w["last_verified"] = TODAY
    w = w.rename(columns={"insurer": "insurer_name", "medicaid": "medicaid_enrollment",
                          "commercial": "commercial_enrollment", "total": "total_enrollment",
                          "comm_net": "commercial_network", "comm_non_net": "commercial_non_network"})
    cols = ["insurer_id", "insurer_name", "naic", "brand", "marketplace_issuer_id",
            "total_enrollment", "commercial_enrollment", "commercial_network",
            "commercial_non_network", "medicaid_enrollment", "is_medicaid_plan",
            "share_of_county_pct", "rank", "brand_rank", "quarter", "source_url", "last_verified"]
    w = w[cols]
    rep.check_unique(w, "insurer_id")
    rep.check_required(w, ["insurer_id", "insurer_name", "total_enrollment"], "insurer_id")
    # totals must tie out to DOBI's own county totals (tolerance 2, see extract_dobi.py)
    for col, line in [("total_enrollment", "county_total_all"),
                      ("commercial_network", "county_total_comm_net"),
                      ("commercial_non_network", "county_total_comm_non_net"),
                      ("medicaid_enrollment", "county_total_medicaid")]:
        s, t = int(w[col].sum()), int(totals.get(line, 0))
        msg = f"Middlesex {col}: sum {s:,} vs DOBI total {t:,}"
        rep.count(msg)
        if abs(s - t) > 2:
            rep.error(msg + " (off by more than 2)")
    unmapped = [n for n in w.insurer_name if n not in DOBI_BRANDS]
    if unmapped:
        rep.warn(f"no brand mapping (shown under their legal name): {', '.join(unmapped)}")
    rep.warn("Counts include out-of-state residents who work in NJ (DOBI note)")
    rep.count("Medicaid (NJ FamilyCare) plans in Middlesex: " + ", ".join(
        f"{r.insurer_name} {r.medicaid_enrollment:,}" for r in w[w.is_medicaid_plan].itertuples()))
    return rep.write(w)


def main():
    codes = []
    c, plans = plans_table()
    codes.append(c)
    codes.append(rates_table(plans))
    codes.append(benefits_table(plans))
    codes.append(insurers_table())
    return 1 if any(codes) else 0


if __name__ == "__main__":
    sys.exit(main())
