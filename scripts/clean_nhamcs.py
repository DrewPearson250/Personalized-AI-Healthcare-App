"""Clean the NHAMCS 2022 emergency department file into urgency-model training rows.

Run from the repo root:  python scripts/clean_nhamcs.py
Input:  data/raw/training/ed2022.zip (one fixed-width file, 16,025 visits)
        layout: 2022 codebook, https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHAMCS/doc22-ed-508.pdf
Output: data/training/nhamcs_visits.csv, data/reports/nhamcs_visits_report.md
Kept apart from the app database (catalog rule: lookup data is never training data, and
training data never goes into the app DB).

Keeps visits with a real triage level (IMMEDR 1-5) and a first reason (RFV1) that maps to a
reason group in config/reason_groups.yaml; drops administrative / follow-up / test-result /
exam / refill / uncodable reasons. Triage 1-2 -> emergency, 3 -> urgent, 4-5 -> routine.
"""
import sys
import zipfile
from pathlib import Path

import pandas as pd

from reason_groups import load, rfv_mapper
from report import Report

RAW = Path("data/raw/training/ed2022.zip")
OUT = Path("data/training")
SOURCE = "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHAMCS/"
# [name]: (start, end) 1-based inclusive columns, from the 2022 codebook
LAYOUT = {
    "AGE": (16, 18), "SEX": (25, 25), "ARREMS": (33, 34), "IMMEDR": (67, 68),
    "PAINSCALE": (69, 70), "RFV1": (73, 77), "RFV2": (78, 82), "RFV3": (83, 87),
    "INJURY": (100, 101), "LWBS": (491, 491), "DIEDED": (495, 495), "ADMITHOS": (499, 499),
    "CSTRATM": (2345, 2352), "CPSUM": (2353, 2358), "PATWT": (2359, 2369),
}
EXPECTED_ROWS = 16025          # codebook: 16,025 sample visits
EXPECTED_LINE_LEN = 2383       # record length (PATWT ends at 2369, EDWT at 2378, ...)


def main():
    rep = Report("nhamcs_visits")
    cfg = load()
    to_group = rfv_mapper(cfg)
    urg = {int(k): v for k, v in cfg["urgency"].items() if k != "dropped"}
    labels = {g["id"]: g["label"] for g in cfg["groups"]}

    lines = zipfile.ZipFile(RAW).read("ed2022").decode("latin-1").splitlines()
    rep.count(f"NHAMCS 2022 ED: {len(lines):,} visits read")
    if len(lines) != EXPECTED_ROWS:
        rep.error(f"expected {EXPECTED_ROWS:,} visits (codebook), got {len(lines):,}")
    short = sum(1 for l in lines if len(l) < 2369)
    if short:
        rep.error(f"{short} records shorter than the PATWT column; layout mismatch")

    rows = [{k: l[a - 1:b].strip() for k, (a, b) in LAYOUT.items()} for l in lines]
    df = pd.DataFrame(rows)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    tri = df["IMMEDR"].value_counts().to_dict()
    names = {1: "immediate", 2: "emergent", 3: "urgent", 4: "semi-urgent", 5: "nonurgent",
             0: "no triage reported", 7: "ED doesn't triage", -8: "unknown", -9: "blank"}
    rep.count("Triage level (IMMEDR): " + ", ".join(f"{names.get(k, k)} {v:,}" for k, v in sorted(tri.items())))
    df = df[df["IMMEDR"].isin(urg)]
    rep.count(f"Kept {len(df):,} visits with a triage level 1-5")

    df["reason_group"] = df["RFV1"].map(to_group)
    dropped = df[df["reason_group"].isna()]
    mod = (dropped["RFV1"] // 10000).map({3: "exam/screening", 4: "treatment/refill/follow-up",
                                           6: "test results", 7: "administrative",
                                           8: "uncodable"}).fillna("blank/other")
    rep.count(f"Dropped {len(dropped):,} visits whose first reason isn't a symptom/injury group: "
              + ", ".join(f"{k} {v}" for k, v in mod.value_counts().items()))
    df = df[df["reason_group"].notna()].copy()

    # Compact on purpose (GitHub shows files under ~1 MB): constant columns (source, URL) live in
    # the report; derivable ones (reason label, age group) come from config / age; yes/no as 1/0.
    b = lambda s: s.astype("Int64")
    out = pd.DataFrame({
        "visit_id": df.index.astype(int),                     # row number in ed2022
        "age": df["AGE"].astype(int),
        "sex": df["SEX"].map({1: "F", 2: "M"}),
        "pain_score": df["PAINSCALE"].where(df["PAINSCALE"].between(0, 10)).astype("Int64"),
        "ambulance": b(df["ARREMS"].map({1: 1, 2: 0})),
        "rfv1_code": (df["RFV1"] / 10).round(1),
        "reason_group": df["reason_group"],
        "rfv2_group": df["RFV2"].map(to_group),
        "rfv3_group": df["RFV3"].map(to_group),
        "triage_level": df["IMMEDR"].astype(int),
        "urgency": df["IMMEDR"].astype(int).map(urg),
        "injury": b(df["INJURY"].map({1: 1, 2: 0})),
        "admitted": (df["ADMITHOS"] == 1).astype(int),
        "patwt": df["PATWT"].round(3),
    })
    rep.count(f"Source: NHAMCS 2022 ED public-use file, {SOURCE} (visit_id = row number in ed2022); "
              "reason labels in config/reason_groups.yaml")

    # --- validation -----------------------------------------------------------
    rep.check_unique(out, "visit_id")
    if out["age"].between(0, 94).all() is False:
        rep.error("age outside 0-94")
    if (out["patwt"] <= 0).any():
        rep.error("non-positive visit weights")
    n_pain = int(out["pain_score"].isna().sum())
    rep.warn(f"pain_score missing for {n_pain:,} visits ({100 * n_pain / len(out):.0f}%); the model "
             "must handle a missing pain score (the questionnaire may also skip it)")
    small = out["reason_group"].value_counts()
    for g, n in small[small < 30].items():
        rep.warn(f"reason group {g}: only {n} visits; urgency estimates will be noisy "
                 "(combine 2019-2022 files if needed)")
    for g in set(labels) - set(out["reason_group"]):
        rep.warn(f"reason group {g}: no visits (it's trained only from text data)")
    rep.warn("Triage nurses also used vital signs and an exam; the model only sees reason, age and "
             "pain, so report that as a known limit. NHAMCS 2022 is national, not NJ-specific")
    # admitted share by urgency: a sanity check that labels mean something
    adm = out.groupby("urgency")["admitted"].mean().mul(100).round(1)
    rep.count("Admitted to hospital by urgency class: " + ", ".join(f"{k} {v}%" for k, v in adm.items()))
    if not adm.get("emergency", 0) > adm.get("urgent", 0) > adm.get("routine", 0):
        rep.error("admission rate doesn't fall from emergency > urgent > routine; check the mapping")

    w = out.groupby("urgency")["patwt"].sum()
    summary = ["Visits by urgency (sample count, weighted national estimate):"]
    summary += [f"- {k}: {(out.urgency == k).sum():,} visits, ~{w[k] / 1e6:.1f} million"
                for k in ("emergency", "urgent", "routine")]
    summary += ["", "| reason group | visits | % emergency | % urgent | % routine |",
                "| --- | --- | --- | --- | --- |"]
    ct = pd.crosstab(out.reason_group, out.urgency, normalize="index").mul(100).round(0)
    for g, n in out.reason_group.value_counts().items():
        summary.append(f"| {g} | {n} | {ct.at[g, 'emergency']:.0f} | {ct.at[g, 'urgent']:.0f} | "
                       f"{ct.at[g, 'routine']:.0f} |")

    return rep.write(out, extra_sections={"Summary": summary}, out_dir=OUT,   # not data/clean (app DB)
                     formats=("csv",))


if __name__ == "__main__":
    sys.exit(main())
