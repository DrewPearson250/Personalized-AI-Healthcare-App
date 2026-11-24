"""Validate config/eligibility_rules.yaml and config/links.yaml.

Run from the repo root:  python scripts/check_rules.py
Writes data/reports/eligibility_rules_report.md. Exit code 1 on any error.

Checks: every rule block has source_url + last_verified; the poverty table follows
base + per-person steps; the dollar examples quoted from official pages match
%FPL x guideline (catches typos); income bands are contiguous; links have ids/urls.
"""
import math
import sys
from datetime import date
from pathlib import Path

import yaml

RULES = Path("config/eligibility_rules.yaml")
LINKS = Path("config/links.yaml")
REPORT = Path("data/reports/eligibility_rules_report.md")


def guideline(rules, size):
    pg = rules["poverty_guidelines"]
    table = pg["by_household_size"]
    if size in table:
        return table[size]
    return table[8] + (size - 8) * pg["per_additional_person"]


def fpl_percent(rules, annual_income, household_size):
    return 100 * annual_income / guideline(rules, household_size)


def monthly_limit(rules, pct, size):
    return math.ceil(guideline(rules, size) * pct / 100 / 12)   # NJ rounds up


def main():
    errors, warnings, checks = [], [], []
    rules = yaml.safe_load(RULES.read_text())
    links = yaml.safe_load(LINKS.read_text())
    today = date.today()

    for key in ("poverty_guidelines", "nj_familycare", "cover_all_kids", "charity_care", "marketplace",
                "prescription_assistance"):
        block = rules.get(key)
        if not block:
            errors.append(f"missing block {key}")
            continue
        for f in ("source_url", "last_verified"):
            if not block.get(f):
                errors.append(f"{key}: missing {f}")
        lv = block.get("last_verified")
        if lv and (today - (lv if isinstance(lv, date) else date.fromisoformat(str(lv)))).days > 365:
            warnings.append(f"{key}: last_verified {lv} is over a year old, re-check")
        if block.get("verified") is False or block.get("csr_verified") is False:
            warnings.append(f"{key}: has values marked verified: false, confirm before launch")

    pg = rules["poverty_guidelines"]
    t = pg["by_household_size"]
    for n in range(2, 9):
        if t[n] - t[n - 1] != pg["per_additional_person"]:
            errors.append(f"poverty table: size {n} - size {n - 1} = {t[n] - t[n - 1]}, "
                          f"expected {pg['per_additional_person']}")
    checks.append(f"poverty table steps by ${pg['per_additional_person']:,} per person: ok")

    g = rules["nj_familycare"]["groups"]
    for label, pct, size, quoted in [("children", g["children"]["max_fpl_pct"], 4, 9763),
                                     ("adults, 1 person", g["adults"]["max_fpl_pct"], 1, 1836),
                                     ("adults, couple", g["adults"]["max_fpl_pct"], 2, 2489),
                                     ("pregnant", g["pregnant"]["max_fpl_pct"], 4, 5638)]:
        calc = monthly_limit(rules, pct, size)
        msg = f"NJ FamilyCare {label}: {pct}% FPL, household {size} = ${calc:,}/month (page says ${quoted:,})"
        (checks if calc == quoted else errors).append(msg)

    for name, bands in [("charity_care", rules["charity_care"]["income_bands"]),
                        ("silver_csr", rules["marketplace"]["silver_csr_bands"])]:
        for a, b in zip(bands, bands[1:]):
            if a.get("max_fpl_pct") != b.get("min_fpl_pct"):
                errors.append(f"{name}: gap/overlap between bands {a} and {b}")
        checks.append(f"{name} bands contiguous: {len(bands)} bands")

    ids = set()
    for group, items in links.items():
        for it in items:
            if not it.get("id") or not (it.get("url") or it.get("phone")):
                errors.append(f"links.{group}: entry missing id or url/phone: {it}")
            if it.get("id") in ids:
                errors.append(f"links: duplicate id {it['id']}")
            ids.add(it.get("id"))
            if not it.get("last_verified"):
                errors.append(f"links.{it.get('id')}: missing last_verified")
    checks.append(f"links.yaml: {len(ids)} entries")

    # worked examples for the report (what the engine will say)
    ex = []
    for income, size in [(20000, 1), (45000, 4), (60000, 3)]:
        p = fpl_percent(rules, income, size)
        cc = next(b["patient_pays_pct"] for b in rules["charity_care"]["income_bands"]
                  if p > b.get("min_fpl_pct", -1) and p <= b.get("max_fpl_pct", 1e9))
        ex.append(f"- ${income:,}/yr, household {size}: {p:.0f}% FPL -> adult NJ FamilyCare "
                  f"{'yes' if p <= g['adults']['max_fpl_pct'] else 'no'}, children "
                  f"{'yes' if p <= g['children']['max_fpl_pct'] else 'no'}, Charity Care patient pays {cc}%")

    lines = ["# Validation report: eligibility_rules", f"*Run {today.isoformat()}*", "",
             f"**Result:** {'FAILED' if errors else 'PASSED'} — {len(errors)} errors, "
             f"{len(warnings)} warnings", "", "## Checks", *[f"- {c}" for c in checks], "",
             "## Errors (block loading)", *([f"- {e}" for e in errors] or ["- none"]), "",
             "## Warnings (review)", *([f"- {w}" for w in warnings] or ["- none"]), "",
             "## Worked examples", *ex, ""]
    REPORT.write_text("\n".join(lines))
    print(f"eligibility rules: {len(errors)} errors, {len(warnings)} warnings -> {REPORT}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
