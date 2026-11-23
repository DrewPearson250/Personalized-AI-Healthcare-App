# Data pipeline

raw CSV/JSON -> scripts/clean_*.py -> data/clean/ (seed files) -> scripts/load.py -> Postgres (db/schema.sql)

- `data/raw/<batch>/` — downloads from the dataset catalog. Gitignored; re-download from catalog links.
- `data/clean/` — cleaned, schema-shaped seed files (committed).
- `data/reports/` — validation report from each cleaning run.
- `db/schema.sql` — table definitions.
- `config/` — eligibility rules (FPL, NJ FamilyCare, Charity Care).

Batch order: hospitals -> clinics -> providers -> insurance -> price transparency -> optional/training.
