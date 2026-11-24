# CareBridge NB — Progress

*Updated 2026-11-24 · Stage: data cleaning*

## Done
- [x] Dataset catalog (`dataset_catalog.pdf`)
- [x] Repo layout (`data/`, `db/`, `scripts/`, `config/`)
- [x] Raw downloads: hospitals, clinics, insurance, providers (CMS), training data
- [x] Middlesex ZIP list (`config/middlesex_zips.csv`, 36 in scope)
- [x] `hospitals` table in `db/schema.sql`
- [x] Hospitals cleaned → `data/clean/hospitals.*` (7 hospitals, report passed)
- [x] Scripts: DOBI extraction, NPPES fetcher, ZIP builder, hospitals cleaner

## To do
- [ ] Run NPPES fetch (provider data)
- [ ] Fill hospital pediatric columns by hand
- [ ] Clean clinics (HRSA + SAMHSA) + schema + report
- [ ] Clean providers, plans, insurers + schema + reports
- [ ] Eligibility rules + links config
- [ ] Price transparency for local hospitals
- [ ] Hand-built lists (free/student-run clinics, local services)
- [ ] Load everything into Postgres
- [ ] Models: urgency classifier, service matcher
- [ ] Backend (FastAPI) + frontend (Next.js) + LLM explanations
