# CareBridge NB — Current Stage

*Updated 2026-11-23*

**Stage:** collecting data. Most datasets are downloaded; cleaning hasn't started.
**Scope:** Middlesex County, within 15 miles of New Brunswick.

## Done

- **Catalog** updated: `dataset_catalog.pdf` (links fixed)
- **Repo layout:** `data/raw/` (downloads, not committed), `data/clean/`, `data/reports/`, `db/`, `scripts/`, `config/`
- **Downloaded into `data/raw/`:**
  - `hospitals/` — CMS General Info, HCAHPS survey, Timely & Effective Care
  - `clinics/` — HRSA health center sites, SAMHSA (120 facilities)
  - `insurance/` — 4 NJ 2026 plan files, DOBI enrollment (converted from PDF to CSV)
  - `providers/` — CMS Doctors & Clinicians
- **Scripts:**
  - `extract_dobi.py` — turns the DOBI enrollment PDF into a CSV
  - `fetch_nppes.py` — downloads providers from the NPPES API

## Do now

1. **Download into `data/raw/training/`:**
   - NHAMCS 2022: `ED2022.zip`
   - Hugging Face symptom set: `train.jsonl` and `test.jsonl`
   (links are in the catalog)
2. **Build `config/middlesex_zips.csv`** and update `fetch_nppes.py` to use it (it only covers 5 ZIPs right now)
3. **Run** `python scripts/fetch_nppes.py` (saves to `data/raw/providers/`)

## Next steps

1. **Database schema** — `db/schema.sql` with tables for hospitals, clinics, providers, plans, insurers
2. **Cleaning scripts** — one per source: filter to Middlesex + 15 miles, keep needed columns, write to `data/clean/`
3. **Validation reports** — each cleaning run writes a report to `data/reports/` (row counts, errors, warnings)
4. **Eligibility rules** — `config/eligibility_rules.yaml` (poverty guidelines, NJ FamilyCare, Charity Care, Cover All Kids)
5. **Price transparency** — download files for the local hospitals once the hospital list is cleaned
6. **Hand-built lists** — free/student-run clinics and local services, with a `source_url` for every entry
7. **Load into Postgres**, then move on to the models (urgency classifier, service matcher)

## Optional / later

- Census ACS + SAHIE for the community dashboard (needs a free API key)
- AI-generated training messages go in `data/synthetic/` (committed)
