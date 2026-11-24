# CareBridge NB — Progress

*Updated 2026-11-24 · Stage: training data, models next*

## Done

- [x] Dataset catalog, repo layout, Middlesex ZIP list (36 in scope)
- [x] All raw downloads, incl. NPPES and hospital price files (5 of 6 hospitals)
- [x] Cleaned + validated (reports in `data/reports/`, all PASSED):
  - hospitals (7, pediatric columns for 5)
  - clinics (42: HRSA, SAMHSA, free clinics)
  - providers (1,386 dentist / pediatric / OB-GYN locations)
  - plans, plan_rates, plan_benefits, insurers_local (2026 NJ marketplace + DOBI)
  - hospital_payers, hospital_prices (price transparency, 30 common services)
  - services (110: food, prescriptions, transportation, benefits, housing, legal, DV, mental health)
- [x] `config/eligibility_rules.yaml` + `links.yaml` (checked by `check_rules.py`)
- [x] `db/schema.sql` (10 tables) + `scripts/load.py` (tested on Postgres 16)

## To do

- [ ] Set aside (blocked sites / hand input, listed in current_stage.md): Princeton + Raritan Bay pediatric info, Princeton price file, a few local services, human check of services
- [x] Training data cleaned: NHAMCS 2022 (9,774 triaged visits) + symptom text (1,060), 27 shared reason groups
- [ ] AI-generated training/test messages
- [ ] Models: urgency classifier, service matcher
- [ ] Backend (FastAPI) + frontend (Next.js) + LLM explanations
