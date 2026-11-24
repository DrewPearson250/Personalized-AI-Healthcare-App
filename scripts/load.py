"""Load data/clean/*.json into PostgreSQL using db/schema.sql.

Run from the repo root:
    python scripts/load.py --dry-run      # check every clean file against the schema, no database
    DATABASE_URL=postgresql://user:pass@localhost:5432/carebridge python scripts/load.py

What it does:
1. Refuses to load if any data/reports/*_report.md says FAILED.
2. Parses db/schema.sql: tables, columns, NOT NULL, foreign keys.
3. Checks each clean file: same columns as the table, NOT NULL filled, FK values exist.
4. (not dry-run) Runs schema.sql, then per table: TRUNCATE + INSERT in one transaction,
   so a failed load leaves the old data in place.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

CLEAN = Path("data/clean")
REPORTS = Path("data/reports")
SCHEMA = Path("db/schema.sql")
# parents before children (FKs)
ORDER = ["hospitals", "clinics", "providers", "insurers_local", "plans", "plan_rates",
         "plan_benefits", "hospital_payers", "hospital_prices", "services"]


def parse_schema(sql):
    tables = {}
    for m in re.finditer(r"CREATE TABLE IF NOT EXISTS (\w+) \((.*?)\n\);", sql, re.S):
        name, body = m.group(1), m.group(2)
        cols = {}
        for line in body.splitlines():
            line = re.sub(r"--.*", "", line).strip().rstrip(",")
            cm = re.match(r"(\w+)\s+([A-Z]+[A-Z0-9_(),\[\] ]*?)(\s|$)(.*)", line)
            if not cm or cm.group(1).upper() in {"PRIMARY", "CONSTRAINT", "UNIQUE", "CHECK"}:
                continue
            rest = line[len(cm.group(1)):]
            fk = re.search(r"REFERENCES (\w+) \((\w+)\)", rest)
            cols[cm.group(1)] = {
                "type": cm.group(2).strip(),
                "not_null": "NOT NULL" in rest or "PRIMARY KEY" in rest,
                "array": "[]" in rest.split("--")[0],
                "pk": "PRIMARY KEY" in rest,
                "fk": (fk.group(1), fk.group(2)) if fk else None,
            }
        tables[name] = cols
    return tables


def blank(v):
    return v is None or (isinstance(v, str) and v.strip() == "") or (isinstance(v, list) and False)


def check(tables):
    problems, data = [], {}
    for rep in sorted(REPORTS.glob("*_report.md")):
        if "**Result:** FAILED" in rep.read_text():
            problems.append(f"{rep.name}: report says FAILED; fix the cleaning errors first")
    for t in ORDER:
        if t not in tables:
            problems.append(f"{t}: not in schema.sql")
            continue
        path = CLEAN / f"{t}.json"
        if not path.exists():
            problems.append(f"{t}: {path} missing (run its clean_*.py)")
            continue
        rows = json.loads(path.read_text())
        data[t] = rows
        cols = tables[t]
        file_cols = set(rows[0]) if rows else set()
        if file_cols - set(cols):
            problems.append(f"{t}: columns in file but not in schema: {sorted(file_cols - set(cols))}")
        if set(cols) - file_cols:
            problems.append(f"{t}: columns in schema but not in file: {sorted(set(cols) - file_cols)}")
        for c, spec in cols.items():
            if spec["not_null"]:
                n = sum(1 for r in rows if blank(r.get(c)))
                if n:
                    problems.append(f"{t}.{c}: {n} empty values in a NOT NULL column")
            if spec["array"]:
                bad = sum(1 for r in rows if r.get(c) is not None and not isinstance(r.get(c), list))
                if bad:
                    problems.append(f"{t}.{c}: {bad} values are not lists (column is an array)")
        pk = next((c for c, s in cols.items() if s["pk"]), None)
        if pk:
            keys = [r.get(pk) for r in rows]
            if len(keys) != len(set(keys)):
                problems.append(f"{t}.{pk}: duplicate primary keys")
        print(f"  {t:16s} {len(rows):6d} rows, {len(cols)} columns")
    for t, rows in data.items():
        for c, spec in tables[t].items():
            if spec["fk"] and spec["fk"][0] in data:
                parent = {r[spec["fk"][1]] for r in data[spec["fk"][0]]}
                missing = {r[c] for r in rows if r.get(c) is not None} - parent
                if missing:
                    problems.append(f"{t}.{c}: {len(missing)} values not in {spec['fk'][0]}: "
                                    f"{sorted(missing)[:5]}")
    return problems, data


def load(tables, data, url):
    import psycopg2
    from psycopg2.extras import execute_values
    conn = psycopg2.connect(url)
    with conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA.read_text())
            for t in reversed(ORDER):          # children first so TRUNCATE doesn't hit FKs
                if t in data:
                    cur.execute(f"TRUNCATE {t} CASCADE")
            for t in ORDER:
                if t not in data:
                    continue
                cols = list(tables[t])
                vals = [tuple(r.get(c) for c in cols) for r in data[t]]
                execute_values(cur, f"INSERT INTO {t} ({', '.join(cols)}) VALUES %s", vals,
                               page_size=1000)
                print(f"  loaded {t}: {len(vals)} rows")
    conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="check files against the schema only")
    args = ap.parse_args()
    tables = parse_schema(SCHEMA.read_text())
    print(f"schema: {len(tables)} tables")
    problems, data = check(tables)
    if problems:
        print("\nPROBLEMS (nothing loaded):")
        for p in problems:
            print(" -", p)
        return 1
    print("all clean files match the schema")
    if args.dry_run:
        return 0
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("set DATABASE_URL to load, e.g. postgresql://postgres:postgres@localhost:5432/carebridge")
        return 1
    load(tables, data, url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
