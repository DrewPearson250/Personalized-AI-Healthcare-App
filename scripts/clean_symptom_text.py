"""Relabel the symptom-to-diagnosis text set to reason groups (reason classifier training text).

Run from the repo root:  python scripts/clean_symptom_text.py
Input:  data/raw/training/train.jsonl, test.jsonl
        (https://huggingface.co/datasets/gretelai/symptom_to_diagnosis, Apache 2.0)
Output: data/training/symptom_text.csv, data/reports/symptom_text_report.md

Each diagnosis maps to a group via symptom_set in config/reason_groups.yaml; diagnoses that
don't map are dropped. The original train/test split is kept: the test rows must never be used
for training (the main test set is the AI-generated one, this is a second, real-text check).
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

from reason_groups import load, symptom_set_map
from report import Report

RAW = Path("data/raw/training")
OUT = Path("data/training")
SOURCE = "https://huggingface.co/datasets/gretelai/symptom_to_diagnosis"


def main():
    rep = Report("symptom_text")
    cfg = load()
    mapping = symptom_set_map(cfg)
    rows = []
    for split in ("train", "test"):
        for i, line in enumerate(open(RAW / f"{split}.jsonl")):
            r = json.loads(line)
            rows.append({"text_id": f"s2d-{split}-{i}", "text": r["input_text"].strip(),
                         "diagnosis": r["output_text"].strip(), "split": split})
    df = pd.DataFrame(rows)
    rep.count(f"Read {len(df):,} rows ({(df.split == 'train').sum()} train, {(df.split == 'test').sum()} test), "
              f"{df.diagnosis.nunique()} diagnoses")
    df["reason_group"] = df["diagnosis"].map(mapping)
    unmapped = df[df.reason_group.isna()]
    if len(unmapped):
        rep.count(f"Dropped {len(unmapped)} rows whose diagnosis maps to no group: "
                  + ", ".join(sorted(unmapped.diagnosis.unique())))
    df = df[df.reason_group.notna()].copy()
    for lab in sorted(set(mapping) - set(df.diagnosis)):
        rep.error(f"symptom_set label '{lab}' in reason_groups.yaml not found in the data (typo?)")

    # exact duplicate texts inside or across splits leak test into train
    df["norm"] = df.text.str.lower().map(lambda t: re.sub(r"\W+", " ", t).strip())
    dup_within = df.duplicated(["norm", "split"])
    if dup_within.any():
        rep.count(f"Dropped {int(dup_within.sum())} exact duplicate texts within a split")
        df = df[~dup_within]
    leak = set(df[df.split == "train"].norm) & set(df[df.split == "test"].norm)
    if leak:
        rep.count(f"Dropped {len(leak)} test texts that also appear in train (leakage)")
        df = df[~((df.split == "test") & df.norm.isin(leak))]
    df["n_words"] = df.text.str.split().str.len()
    df = df.drop(columns="norm")
    rep.count(f"Source: {SOURCE} (Apache 2.0)")

    rep.check_unique(df, "text_id")
    rep.check_required(df, ["text", "reason_group"], "text_id")
    groups = {g["id"] for g in cfg["groups"]}
    missing = sorted(groups - set(df.reason_group))
    rep.warn(f"{len(missing)} of {len(groups)} reason groups have no text here (AI-generated messages "
             f"must cover them): {', '.join(missing)}")
    rep.warn("Texts are written in a patient voice but by a model (Gretel), short and tidy; real "
             "messages will be messier (typos, Spanish-English mix)")
    summary = ["| reason group | train | test | diagnoses |", "| --- | --- | --- | --- |"]
    for g, sub in df.groupby("reason_group"):
        summary.append(f"| {g} | {(sub.split == 'train').sum()} | {(sub.split == 'test').sum()} | "
                       f"{', '.join(sorted(sub.diagnosis.unique()))} |")
    return rep.write(df, extra_sections={"Summary": summary}, out_dir=OUT, formats=("csv",))


if __name__ == "__main__":
    sys.exit(main())
