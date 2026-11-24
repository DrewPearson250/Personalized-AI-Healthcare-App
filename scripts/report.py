"""Shared validation-report helpers for the clean_*.py scripts.

Same format as clean_hospitals.py: counts, errors (block loading, exit 1),
warnings (review), coverage % per column.
"""
import json
from datetime import date
from pathlib import Path

import pandas as pd

CLEAN = Path("data/clean")
REPORTS = Path("data/reports")


class Report:
    def __init__(self, table):
        self.table = table
        self.counts, self.errors, self.warnings = [], [], []

    def count(self, msg):
        self.counts.append(msg)

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def check_required(self, df, cols, key):
        for c in cols:
            for k in df.loc[df[c].isna() | (df[c].astype(str).str.strip() == ""), key]:
                self.error(f"{k}: missing required field {c}")

    def check_unique(self, df, key):
        dup = df.loc[df[key].duplicated(), key]
        if len(dup):
            self.error(f"duplicate {key}: {sorted(dup.astype(str))[:20]}")

    def write(self, df, name=None, extra_sections=None, out_dir=None):
        """Write <out_dir or data/clean>/<name>.csv/.json and data/reports/<name>_report.md."""
        name = name or self.table
        out_dir = Path(out_dir) if out_dir else CLEAN
        out_dir.mkdir(parents=True, exist_ok=True)
        REPORTS.mkdir(exist_ok=True)
        out = df.copy()
        for c in out.columns:   # lists -> "a; b" in CSV, real lists in JSON
            if out[c].map(lambda v: isinstance(v, list)).any():
                out[c] = out[c].map(lambda v: "; ".join(v) if isinstance(v, list) else v)
        out.to_csv(out_dir / f"{name}.csv", index=False)
        recs = json.loads(df.to_json(orient="records"))
        (out_dir / f"{name}.json").write_text(json.dumps(recs, indent=2))

        def filled(v):
            if isinstance(v, list):
                return len(v) > 0
            return not pd.isna(v) and str(v) != ""

        cov = {c: round(100 * df[c].map(filled).mean()) if len(df) else 0 for c in df.columns}
        lines = [f"# Validation report: {name}", f"*Run {date.today().isoformat()}*", "",
                 f"**Result:** {'FAILED' if self.errors else 'PASSED'} — "
                 f"{len(df)} rows, {len(self.errors)} errors, {len(self.warnings)} warnings", "",
                 "## Counts", *[f"- {c}" for c in self.counts], "",
                 "## Errors (block loading)", *([f"- {e}" for e in self.errors] or ["- none"]), "",
                 "## Warnings (review)", *([f"- {w}" for w in self.warnings] or ["- none"]), ""]
        for title, body in (extra_sections or {}).items():
            lines += [f"## {title}", *body, ""]
        lines += ["## Coverage (% of rows filled)", "| column | % |", "| --- | --- |",
                  *[f"| {c} | {v} |" for c, v in cov.items()], ""]
        (REPORTS / f"{name}_report.md").write_text("\n".join(lines))
        print(f"{len(df)} rows -> {out_dir / (name + '.csv')}  "
              f"({len(self.errors)} errors, {len(self.warnings)} warnings)")
        return 1 if self.errors else 0
