# Validation report: hospitals
*Run 2026-11-24*

**Result:** PASSED — 7 rows, 0 errors, 5 warnings

## Counts
- General Information: 79 rows read (NJ)
- In Middlesex: 7 hospitals
- HCAHPS: 30 rows kept (5 measures x hospitals)
- Timely & Effective Care: 18 ER rows kept

## Errors (block loading)
- none

## Warnings (review)
- 310108 JFK UNIVERSITY MEDICAL CENTER: ZIP 08818 has no Census centroid (PO-box ZIP); distance unknown, kept because it's in Middlesex
- 313300 Children's Specialized Hospital: no patient survey star rating
- 314011 University Behavioral Health Care: has an ER but no median ER time
- 314011 University Behavioral Health Care: no patient survey star rating
- has_pediatric_er, has_childrens_hospital, pediatric_specialties: empty for all rows, fill by hand from hospital websites

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| facility_id | 100 |
| name | 100 |
| address | 100 |
| city | 100 |
| state | 100 |
| zip | 100 |
| county | 100 |
| phone | 100 |
| hospital_type | 100 |
| ownership | 100 |
| has_emergency | 100 |
| birthing_friendly | 100 |
| overall_rating | 71 |
| lat | 86 |
| lng | 86 |
| miles_to_nb | 86 |
| survey_star | 71 |
| nurse_comm_star | 71 |
| doctor_comm_star | 71 |
| recommend_pct | 71 |
| rating_9_10_pct | 71 |
| survey_count | 71 |
| survey_period_end | 86 |
| er_median_minutes | 71 |
| er_left_unseen_pct | 71 |
| er_volume | 71 |
| er_period_end | 86 |
| has_pediatric_er | 0 |
| has_childrens_hospital | 0 |
| pediatric_specialties | 0 |
| source_url | 100 |
| last_verified | 100 |
