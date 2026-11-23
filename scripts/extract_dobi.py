"""Extract the NJ DOBI quarterly health enrollment PDF into a tidy CSV.

Usage (repo root):
    python scripts/extract_dobi.py data/raw/insurance/dobi_health.pdf data/raw/insurance/dobi_enrollment_2026q2.csv

Output columns: insurer, naic, line, county, enrollment
  line = comm_net | comm_non_net | medicaid | total, or county_total_* for the summary rows.
All counties are kept; the cleaning script filters to Middlesex.
Numbers are placed into columns by their x position under the header,
then checked: each insurer's line values must sum to its TOTAL column,
and insurer totals must sum to "Totals By County".
"""
import csv
import re
import sys
from collections import defaultdict

import pdfplumber

LINE_LABELS = {
    "comm net": "comm_net",
    "comm non net": "comm_non_net",
    "medicaid": "medicaid",
    "medicaid (from quarterlies)": "medicaid",
    "total": "total",
    "totals by county": "county_total_all",
    "comm net total by county": "county_total_comm_net",
    "comm non net by county": "county_total_comm_non_net",
    "medicaid total by county": "county_total_medicaid",
}
NUM = re.compile(r"^-?[\d,]+$")


def group_lines(words, tol=3):
    lines = []
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if lines and abs(lines[-1][0] - w["top"]) <= tol:
            lines[-1][1].append(w)
        else:
            lines.append([w["top"], [w]])
    return [sorted(ws, key=lambda w: w["x0"]) for _, ws in lines]


def parse(pdf_path):
    rows, insurer, naic = [], None, None
    for page in pdfplumber.open(pdf_path).pages:
        lines = group_lines(page.extract_words(keep_blank_chars=False))
        header = next(l for l in lines if any(w["text"] == "Middlesex" for w in l))
        # merge multi-word county names in the header (e.g. "Cape May")
        merged = []
        for w in header:
            if merged and w["x0"] - merged[-1]["x1"] < 8:
                merged[-1] = {**merged[-1], "text": merged[-1]["text"] + " " + w["text"], "x1": w["x1"]}
            else:
                merged.append(dict(w))
        cols = [(w["text"], (w["x0"] + w["x1"]) / 2) for w in merged]
        first_col_x = header[0]["x0"]
        for l in lines:
            if l is header:
                continue
            label_words = [w for w in l if w["x1"] < first_col_x - 5]
            nums = [w for w in l if w["x1"] >= first_col_x - 5 and NUM.match(w["text"])]
            label = " ".join(w["text"] for w in label_words).strip()
            key = re.sub(r"\s*\(.*?\)", "", label).lower().strip()
            if key in LINE_LABELS:
                line = LINE_LABELS[key]
                who = ("ALL", "") if line.startswith("county_total") else (insurer, naic)
                for w in nums:
                    xc = (w["x0"] + w["x1"]) / 2
                    county = min(cols, key=lambda c: abs(c[1] - xc))[0]
                    rows.append({"insurer": who[0], "naic": who[1], "line": line,
                                 "county": county, "enrollment": int(w["text"].replace(",", ""))})
            elif label and not nums and not label.startswith("*") and "Enrollment" not in label:
                m = re.search(r"\b(\d{5}(?:/\d{5})?)\b", label)
                naic = m.group(1) if m else ""
                insurer = re.sub(r"\s*\b\d{5}(?:/\d{5})?\b", "", label).strip()
    # drop duplicate county_total rows (repeated on each page)
    seen, out = set(), []
    for r in rows:
        k = (r["insurer"], r["line"], r["county"])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


TOLERANCE = 2  # DOBI's own totals are sometimes off by 1-2 (verified by hand in Q2 2026)


def validate(rows):
    """Return (errors, warnings): diffs > TOLERANCE are errors, smaller ones warnings."""
    errors = []
    by = defaultdict(int)
    for r in rows:
        by[(r["insurer"], r["line"], r["county"])] += r["enrollment"]
    insurers = {r["insurer"] for r in rows if r["insurer"] != "ALL"}
    counties = {r["county"] for r in rows if r["county"] != "TOTAL"}
    for ins in insurers:
        for line in ("comm_net", "comm_non_net", "medicaid", "total"):
            row_sum = sum(by.get((ins, line, c), 0) for c in counties)
            stated = by.get((ins, line, "TOTAL"))
            if stated is not None and row_sum != stated:
                errors.append(f"{ins} {line}: counties sum {row_sum} != TOTAL {stated}")
    for c in counties | {"TOTAL"}:
        s = sum(by.get((i, "total", c), 0) for i in insurers)
        stated = by.get(("ALL", "county_total_all", c))
        if stated is not None and s != stated:
            errors.append(f"{c}: insurer totals {s} != Totals By County {stated}")
    big = [e for e in errors if abs(int(e.split("!=")[0].split()[-1]) - int(e.split()[-1])) > TOLERANCE]
    small = [e for e in errors if e not in big]
    return big, small


def main(pdf_path, csv_path):
    rows = parse(pdf_path)
    with open(csv_path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["insurer", "naic", "line", "county", "enrollment"])
        wr.writeheader()
        wr.writerows(rows)
    errors, warnings = validate(rows)
    print(f"{len(rows)} rows -> {csv_path}")
    print(f"validation: {len(errors)} errors, {len(warnings)} warnings (off by <= {TOLERANCE}, in the source PDF itself)")
    for e in errors + warnings:
        print("  ", "ERROR" if e in errors else "warn ", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
