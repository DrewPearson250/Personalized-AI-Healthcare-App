# Validation report: hospitals
*Run 2026-11-24*

**Result:** PASSED — 7 rows, 0 errors, 7 warnings

## Counts
- General Information: 79 rows read (NJ)
- In Middlesex: 7 hospitals
- HCAHPS: 30 rows kept (5 measures x hospitals)
- Timely & Effective Care: 18 ER rows kept

## Errors (block loading)
- none

## Warnings (review)
- 310038 ROBERT WOOD JOHNSON UNIVERSITY HOSPITAL: address didn't geocode, using the ZIP centroid
- 313300 CHILDREN'S SPECIALIZED HOSPITAL: address didn't geocode, using the ZIP centroid
- 313300 Children's Specialized Hospital: no patient survey star rating
- 314011 University Behavioral Health Care: has an ER but no median ER time
- 314011 University Behavioral Health Care: no patient survey star rating
- 310010 University Medical Center Of Princeton At Plainsboro: pediatric columns not filled (data/manual/hospital_pediatrics.csv); check the hospital website
- 310039 Raritan Bay Medical Center: pediatric columns not filled (data/manual/hospital_pediatrics.csv); check the hospital website

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
| lat | 100 |
| lng | 100 |
| miles_to_nb | 100 |
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
| source_url | 100 |
| has_pediatric_er | 71 |
| has_childrens_hospital | 71 |
| pediatric_specialties | 71 |
| pediatric_source_url | 71 |
| last_verified | 100 |
