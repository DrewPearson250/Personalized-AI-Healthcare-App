"""Build the AI-generated message sets from data/synthetic/raw/*.txt.

Run from the repo root:  python scripts/build_synthetic.py
Inputs:  data/synthetic/raw/train_*.txt, test_*.txt   (written per data/synthetic/prompts.md)
         raw line format:  <style>|<urgency>|<text>   under a "# group: <reason_group>" header
Outputs: data/synthetic/train.jsonl, test.jsonl (+ .csv), spot_check.csv,
         data/reports/synthetic_messages_report.md
Exit code 1 if any error-level validation check fails.

Fields: message_id, text, reason_group, urgency, prompt_id, split, generator, created.
urgency is AI-assigned (for end-to-end evaluation), not a training label for the urgency model.
"""
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from reason_groups import load
from report import Report

RAW = Path("data/synthetic/raw")
OUT = Path("data/synthetic")
GENERATOR = "claude-opus-5-5 (Claude Code session)"
CREATED = "2026-11-24"
STYLES = {
    "train": {"s": "train-short", "r": "train-rambling", "m": "train-misspelled",
              "x": "train-spanglish", "p": "train-parent", "o": "train-older"},
    "test": {"t": "test-textspeak", "c": "test-caregiver", "f": "test-formal",
             "q": "test-question", "n": "test-spanish", "l": "test-runon"},
}
URGENCY = {"e": "emergency", "u": "urgent", "r": "routine"}
MIN_TRAIN_PER_GROUP, MIN_TEST_PER_GROUP = 35, 10
SPOT_CHECK_N = 50


def norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()


def parse(path, split, rep):
    rows, group = [], None
    for n, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"#\s*group:\s*(\w+)", line)
        if m:
            group = m.group(1)
            continue
        if line.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) != 3 or group is None:
            rep.error(f"{path.name}:{n}: can't parse line: {line[:60]}")
            continue
        style, urg, text = parts
        if style not in STYLES[split]:
            rep.error(f"{path.name}:{n}: style '{style}' isn't a {split} prompt")
            continue
        if urg not in URGENCY:
            rep.error(f"{path.name}:{n}: urgency '{urg}' must be e/u/r")
            continue
        rows.append({"text": text.strip(), "reason_group": group, "urgency": URGENCY[urg],
                     "prompt_id": STYLES[split][style], "split": split,
                     "source_file": path.name, "line": n})
    return rows


def main():
    rep = Report("synthetic_messages")
    cfg = load()
    groups = [g["id"] for g in cfg["groups"]]
    rows = []
    for split in ("train", "test"):
        files = sorted(RAW.glob(f"{split}_*.txt"))
        for f in files:
            rows += parse(f, split, rep)
        rep.count(f"{split}: {len(files)} raw files, "
                  f"{sum(r['split'] == split for r in rows)} messages")
    df = pd.DataFrame(rows)

    # --- validation -----------------------------------------------------------
    unknown = sorted(set(df.reason_group) - set(groups))
    for g in unknown:
        rep.error(f"unknown reason_group '{g}' (not in config/reason_groups.yaml)")
    for split, minimum in (("train", MIN_TRAIN_PER_GROUP), ("test", MIN_TEST_PER_GROUP)):
        counts = df[df.split == split].reason_group.value_counts()
        for g in groups:
            if counts.get(g, 0) < minimum:
                rep.error(f"{split}: group {g} has {counts.get(g, 0)} messages, need >= {minimum}")
    df["norm"] = df.text.map(norm)
    dup = df[df.duplicated(["norm"], keep=False)].sort_values("norm")
    within = dup.groupby("norm").split.nunique()
    for t in within[within == 1].index:
        rep.warn(f"duplicate text within a split, keeping the first: '{t[:60]}'")
    for t in within[within > 1].index:
        rep.error(f"text appears in both train and test: '{t[:60]}'")
    df = df.drop_duplicates(["norm", "split"], keep="first")

    # near-duplicates between test and train (token Jaccard), so test phrasing is really new
    train_sets = [(set(t.split()), t) for t in df[df.split == "train"].norm]
    near = 0
    for t in df[df.split == "test"].norm:
        a = set(t.split())
        best = max((len(a & b) / len(a | b), s) for b, s in train_sets if a | b)
        if best[0] >= 0.7:
            near += 1
            rep.warn(f"test message close to a train message (Jaccard {best[0]:.2f}): '{t[:50]}' ~ '{best[1][:50]}'")
    rep.count(f"Test messages with a near-duplicate in train (Jaccard >= 0.7): {near}")
    short = df[df.text.str.split().str.len() < 3]
    for _, r in short.iterrows():
        rep.warn(f"very short message: '{r.text}'")

    # ids, final columns
    df = df.sort_values(["split", "reason_group", "source_file", "line"]).reset_index(drop=True)
    df["message_id"] = [f"syn-{s}-{i:04d}" for s, i in zip(df.split, df.groupby("split").cumcount() + 1)]
    df["generator"] = GENERATOR
    df["created"] = CREATED
    df["n_words"] = df.text.str.split().str.len()
    cols = ["message_id", "text", "reason_group", "urgency", "prompt_id", "split", "n_words",
            "generator", "created"]
    df = df[cols]
    rep.check_unique(df, "message_id")

    OUT.mkdir(parents=True, exist_ok=True)
    for split in ("train", "test"):
        part = df[df.split == split]
        with open(OUT / f"{split}.jsonl", "w") as f:
            for r in part.to_dict("records"):
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        part.to_csv(OUT / f"{split}.csv", index=False)

    # spot check: fixed seed so the sample is reproducible
    sample = df.sample(SPOT_CHECK_N, random_state=42)[["message_id", "text", "reason_group", "urgency",
                                                       "prompt_id", "split"]].copy()
    sample["ok"] = ""
    sample["note"] = ""
    spot = OUT / "spot_check.csv"
    if spot.exists():
        rep.count(f"{spot} already exists, not overwritten (it may hold a person's review)")
    else:
        sample.to_csv(spot, index=False)

    rep.warn("All messages are AI-generated, not from real users; the test set is too, so scores "
             "on it will likely overstate real-world performance. Say so when reporting results")
    rep.warn("urgency labels are AI-assigned from message content; use them only for end-to-end "
             "evaluation, never to train the urgency model (that uses NHAMCS triage)")
    rep.warn(f"Spot-check {SPOT_CHECK_N} messages by hand: fill ok/note in data/synthetic/spot_check.csv")

    summary = ["| reason group | train | test | train e/u/r |", "| --- | --- | --- | --- |"]
    for g in groups:
        tr, te = df[(df.split == "train") & (df.reason_group == g)], df[(df.split == "test") & (df.reason_group == g)]
        u = Counter(tr.urgency)
        summary.append(f"| {g} | {len(tr)} | {len(te)} | {u['emergency']}/{u['urgent']}/{u['routine']} |")
    summary += ["", "Messages per prompt:"]
    summary += [f"- {k}: {v}" for k, v in df.prompt_id.value_counts().sort_index().items()]
    summary += ["", "Urgency overall: " + ", ".join(f"{k} {v}" for k, v in df.urgency.value_counts().items())]
    return rep.write(df, name="synthetic_messages", extra_sections={"Summary": summary}, out_dir=OUT / "build")


if __name__ == "__main__":
    sys.exit(main())
