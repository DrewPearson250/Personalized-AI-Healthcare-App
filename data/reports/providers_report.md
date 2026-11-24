# Validation report: providers
*Run 2026-11-24*

**Result:** PASSED — 1386 rows, 0 errors, 6 warnings

## Counts
- NPPES: 108 files, 1955 results, 1797 unique NPIs
- Doctors & Clinicians: 101340 NJ rows read, 54652 NPIs, 22360 rows with Telehlth = Y
- NPPES: 0 inactive NPIs dropped
- NPPES: 0 NPIs dropped whose taxonomies aren't dental / pediatric / OB-GYN (the API's taxonomy search is loose, e.g. medical-equipment suppliers)
- Candidate locations (NJ, ZIP touches Middlesex): 1460
- Dropped 74 locations outside Middlesex County (Census geocoder) or in an unmatched address in a mostly-outside ZIP
- Dropped 0 locations over 15 miles from New Brunswick

## Errors (block loading)
- none

## Warnings (review)
- 159 addresses didn't geocode; used the ZIP centroid (geo_precision = zip)
- 1 locations have no phone number
- 1109 locations from NPIs not updated in NPPES for over 3 years (addresses may be out of date; prefer recently updated rows)
- 235 addresses host several providers (group practices); fine, but the app should group them when listing
- accepts_medicaid, sliding_fee, accepting_new_patients, languages: not in NPPES; fill by hand for the providers the app shows first
- telehealth is only known for Medicare-enrolled clinicians (NULL = not in Doctors & Clinicians)

## Summary
- dentist: 1154 locations (1021 general care)
- obgyn: 86 locations (34 general care)
- pediatrics: 146 locations (101 general care)
- unique NPIs: 1357
- organizations: 323
- telehealth = true: 3
- geocoded to the address: 1227

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| provider_id | 100 |
| npi | 100 |
| name | 100 |
| credential | 68 |
| provider_kind | 100 |
| sex | 77 |
| specialty | 100 |
| taxonomy | 100 |
| taxonomy_code | 100 |
| general_care | 100 |
| other_specialties | 13 |
| address | 100 |
| city | 100 |
| state | 100 |
| zip | 100 |
| county | 100 |
| phone | 100 |
| lat | 100 |
| lng | 100 |
| geo_precision | 100 |
| miles_to_nb | 100 |
| is_primary_location | 100 |
| telehealth | 3 |
| accepts_medicaid | 0 |
| sliding_fee | 0 |
| accepting_new_patients | 0 |
| languages | 0 |
| nppes_last_updated | 100 |
| source_url | 100 |
| last_verified | 100 |
