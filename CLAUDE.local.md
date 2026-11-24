# CareBridge NB — Context for Claude Code

Read this first, then `current_stage.md` (short status) and `dataset_catalog.pdf` (full dataset catalog: sources, columns, filters, links).

## Working with Jason
- Concise, practical answers; casual and direct is fine.
- **Never run or suggest destructive/irreversible git commands (reset, rebase, force push, abort, etc.) without warning about the risks and getting a yes first.**
- Commit as Jason Lam <jasonlamc18@gmail.com>. The team has been pushing to `main`; ask before pushing.
- Remote: https://github.com/DrewPearson250/Personalized-AI-Healthcare-App (team club project, mentor Hir).

## The project
CareBridge NB matches uninsured/underinsured New Brunswick, NJ residents to hospitals, clinics, providers, insurance plans and programs.
Flow: questionnaire (needs, insurance, income, language, transport) → deterministic rules engine (eligibility) → transparent scoring function (ranking) → LLM explains results.

Architecture rules:
- **The database is the source of truth.** No live web research at query time.
- **The LLM never invents facts** (no made-up costs or eligibility rules). It only explains rows the DB returns.
- Every stored fact carries `source_url` and `last_verified`.
- Ranking is code, not the LLM. Trained models: urgency classifier (NHAMCS + symptom text + AI-generated messages) and service matcher (sentence embeddings). Lookup data is never used for training.
- Stack: FastAPI, PostgreSQL (+ pgvector if needed), Next.js/React/Tailwind, OpenAI API with plain tool calling (no LangChain).
- Only free datasets with no access request.

## Scope decision (settled)
**Middlesex County, NJ AND within 15 miles of New Brunswick** (center 40.4862, -74.4518).
- Download wide (e.g. all NJ), filter in the cleaning scripts — reproducible, catches messy values, easy to widen later.
- Exceptions filtered at download because they're query-only or huge: NPPES (by ZIP), SAMHSA (radius), price transparency files.
- Every Middlesex ZIP center is within 15 miles (farthest: Carteret 07008, 13.6 mi), so in practice the county filter does the work.
- `config/middlesex_zips.csv`: 44 ZIPs touch Middlesex; `in_scope=1` for 36 (≥50% of land in Middlesex and within 15 mi). Built by `scripts/build_middlesex_zips.py` from Census extracts in `data/raw/geo/`. PO-box ZIPs (e.g. 08818, 08903, 08906) have no Census centroid → distance unknown; keep them if county = Middlesex and warn.

## Repo layout and conventions
```
data/raw/<batch>/   downloads — GITIGNORED (re-download from catalog links)
data/clean/         cleaned, schema-shaped seed files (.csv + .json) — committed
data/reports/       validation report per cleaning run (<table>_report.md) — committed
data/synthetic/     AI-generated training/test messages (to create) — committed
db/schema.sql       Postgres tables
config/             middlesex_zips.csv; later eligibility_rules.yaml, links.yaml
scripts/            run from repo root: python scripts/<name>.py
```
- Pipeline: raw → `scripts/clean_<table>.py` → `data/clean/` + `data/reports/` → `scripts/load.py` (todo) → Postgres.
- `scripts/geo.py` has shared helpers: `miles()`, `load_zips()`, `query_zips()`, `NB_LAT/NB_LNG`, `RADIUS_MI`. Scripts import it as `from geo import ...` (works because scripts/ is on sys.path when run as `python scripts/x.py`).
- Validation report format (see `clean_hospitals.py`): counts (read/kept/dropped + why), **errors** (block loading, exit code 1: missing required fields, duplicates, bad types, broken joins), **warnings** (review: stale >3 yrs, unparseable values, odd values, missing optional data), coverage % per column.
- Keep only the columns that support an app feature. Don't drop columns before knowing they're unneeded.

## Data status
| Batch | Files in `data/raw/` | Status |
|---|---|---|
| hospitals | `CMS.csv` (General Info, 79 NJ rows), `survey.csv` (HCAHPS), `timely.csv` | **Cleaned** → `data/clean/hospitals.*`, 7 hospitals, report passed (0 errors, 5 warnings) |
| clinics | `Health_Center_Service_Delivery_and_LookAlike_Sites.csv` (HRSA, 18,356 rows), `samhsa.json` (120 rows) | Next to clean |
| providers | `doc_clinics.zip` (CMS Doctors & Clinicians, NJ; contains `doc_clinics.csv`) | NPPES not fetched yet |
| insurance | `NJPlans/NJRates/NJBenefits/NJServiceAreas05072026.csv`, `dobi_enrollment_2026q2.csv` | To clean |
| training | `ed2022.zip` (NHAMCS, one fixed-width file `ed2022`), `train.jsonl` (853), `test.jsonl` (212) | To clean (separate from app DB) |
| geo | Census ZCTA→county and centroid extracts (Middlesex rows) | Used by build_middlesex_zips.py |
| price_transparency | empty | Later |

Hospitals in scope (also the price transparency list): RWJ University Hospital 310038, Saint Peter's 310070, Princeton Plainsboro 310010, Raritan Bay 310039, JFK 310108 (acute care), plus Children's Specialized 313300 (no ER) and University Behavioral Health Care 314011 (psychiatric).

## Notes per source (learned so far)
- **CMS hospitals:** missing values are text ("Not Available"/"Not Applicable"). Names are ALL CAPS → `nice()` title-cases them. HCAHPS kept: H_STAR_RATING, H_COMP_1/2_STAR_RATING (nurse/doctor), H_RECMND_DY, H_HSP_RATING_9_10. ER kept: OP_18b (median minutes), OP_22 (% left before seen), EDV (volume). No lat/long in CMS → ZIP centroid. Pediatric columns (`has_pediatric_er`, `has_childrens_hospital`, `pediatric_specialties`) must be filled by hand.
- **HRSA:** 9 rows with State = NJ and `Complete County Name` contains Middlesex (Chandler/Rutgers RWJ ×3, Central Jersey Medical Center ×3 incl. mobile van, JRF ×2, Zufall Plainsboro). Lat/long in `Geocoding Artifact Address Primary X/Y Coordinate` (X = longitude). Keep `Site Status Description` = Active. `Site Web Address` is useful for later LLM extraction.
- **SAMHSA:** fetched with `pageSize=2000` → 1 page, 120 rows (116 NJ, 4 NY), only 88 unique name+street (duplicates). `services` is a list of `{f1: category, f2: code, f3: values}` already decoded to text (10 rows have `services: null`). Useful codes: TC type of care, PAY payment/insurance accepted, PYAS payment assistance (sliding fee), SL/OL languages, AGE, SET setting, EMS emergency MH. Filter to Middlesex via ZIP (no county field) and keep Medicaid/sliding-fee/free-care facilities. Show 988 alongside.
- **NPPES:** API is free, no key; no county filter; ZIP search also matches mailing addresses → keep `address_purpose = LOCATION` in Middlesex. `fetch_nppes.py` queries 36 in-scope ZIPs × Dentist / Pediatrics / Obstetrics & Gynecology → `data/raw/providers/nppes/`, skips existing files. Must run on Jason's Mac (no network from Claude's sandbox). If a specialty returns 0, the taxonomy wording is wrong.
- **Doctors & Clinicians:** optional; only for the `Telehlth` flag joined on `NPI`. Columns include NPI, pri_spec, Telehlth, Facility Name, adr_ln_1, City/Town, ZIP Code.
- **SBE plan files:** filtering recipe is in the catalog (Insurance → Filtering). `ISSUER NAME` is blank: 17970 WellCare/Ambetter, 23818 Oscar, 37777 Oxford/UHC, 91661 Horizon, 91762 AmeriHealth. NJNetworks and NJBusinessRules were dropped for v1.
- **DOBI:** converted from PDF by `scripts/extract_dobi.py` (long format: insurer, naic, line, county, enrollment). 11 off-by-1–2 mismatches are in DOBI's own PDF (logged as warnings, tolerance 2). Middlesex totals verified: 235,700 / 96,103 commercial / 139,312 Medicaid. County column is spelled "Passiac" in the source.
- **Get Covered NJ / eligibility rules:** no downloads. Values go into `config/eligibility_rules.yaml` and `config/links.yaml` with source_url + last_verified. 2026 values and things to confirm are in the catalog (Eligibility rules section).
- **NHAMCS:** fixed-width; needs the column layout from https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHAMCS/doc22-ed-508.pdf. Keep triaged, non-administrative visits; group reason codes (~25); map triage to emergency/urgent/routine.

## Next steps
1. Jason runs `python scripts/fetch_nppes.py`; commit the uncommitted work (schema, geo, ZIP list, hospitals clean/report).
2. Fill hospital pediatric columns by hand.
3. `clinics`: add table to `db/schema.sql`, write `clean_clinics.py` (HRSA + SAMHSA, dedupe, Middlesex filter, payment/language flags) + report.
4. `providers` (after NPPES fetch), then `plans` + `insurers_local`.
5. `config/eligibility_rules.yaml` and `links.yaml`.
6. Price transparency for the 5 acute hospitals (files are huge; prefilter locally to common services + unique payer/plan pairs; CMS spec: https://github.com/CMSgov/hospital-price-transparency).
7. Hand-built lists (free/student-run clinics, local services) via LLM extraction + human check; `load.py` into Postgres; then the models.

## Catalog copies
Live editable catalog: https://claude.ai/artifact/KqRH4dnixkEsGAV8Vvnkhk · repo PDF: `dataset_catalog.pdf`. Keep them in sync when scope or sources change.
