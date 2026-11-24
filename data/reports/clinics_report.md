# Validation report: clinics
*Run 2026-11-24*

**Result:** PASSED — 42 rows, 0 errors, 16 warnings

## Counts
- HRSA: 18356 rows read (all US)
- HRSA: 9 NJ sites in Middlesex
- HRSA: 9 active sites kept within 15 mi
- SAMHSA: 120 rows read (15 mi radius, pageSize=2000, 1 page)
- SAMHSA: 67 rows in in-scope Middlesex ZIPs (53 outside: other counties, NY, or ZIPs mostly outside Middlesex)
- SAMHSA: 46 unique facilities after merging duplicate name+street rows (21 duplicates merged)
- SAMHSA: 4 dropped with no service data
- SAMHSA: 9 dropped (no Medicaid, sliding fee, assistance or free care): College Recovery LLC; Counseling Center at Middlesex; Counseling Center at Monmouth Junction; Guardian Recovery; Laszlo Center 4 Hope and Healing; Lifebulb Counseling and Therapy; Recovery Centers of America; SOBA New Jersey; Victor H Lopez LSW MSW LCADC CCS
- SAMHSA: 2 dropped in split ZIPs whose point is outside Middlesex (Census geocoder): YMCA of New Jersey Shore (Matawan, Monmouth County); CPC Integrated Health (Matawan, Monmouth County)
- SAMHSA: 31 facilities kept
- Manual free/student-run clinics: 2 rows

## Errors (block loading)
- none

## Warnings (review)
- HRSA: accepts_medicaid / sliding_fee / accepts_self_pay set to true from the health center program rules (https://bphc.hrsa.gov/compliance/compliance-manual/chapter9), not from the row itself
- HRSA: has_dental, walk_in, languages are empty; fill by hand from each site's website (Site Web Address)
- HRSA: Jewish Renaissance Foundation Community Health Center shares its address with JRF Community Health Center-Mobile Unit (mobile unit based at the permanent site); both kept
- HRSA: Central Jersey Medical Center Mobile Van 2 shares its address with Central Jersey Medical Center (mobile unit based at the permanent site); both kept
- HRSA: Central Jersey Medical Center Inc. lists different websites ['https://www.cjmc.us', 'https://www.jrmc.us']; check which is right
- SAMHSA: Eleanor Health: no lat/long, used ZIP 08820 centroid
- SAMHSA: Eleanor Health (Edison): no street address listed; kept with city/ZIP only, users must call
- SAMHSA: Wellness Meets World: no lat/long, used ZIP 08902 centroid
- SAMHSA: College Recovery, LLC: no service data (services = null), payment unknown, dropped. Check by hand and add to data/manual/free_clinics.csv if it qualifies
- SAMHSA: Center For Network Therapy LLP: no service data (services = null), payment unknown, dropped. Check by hand and add to data/manual/free_clinics.csv if it qualifies
- SAMHSA: South Amboy Health Center: no service data (services = null), payment unknown, dropped. Check by hand and add to data/manual/free_clinics.csv if it qualifies
- SAMHSA: 5034 Atlantic Avenue OPCO, LLC: no service data (services = null), payment unknown, dropped. Check by hand and add to data/manual/free_clinics.csv if it qualifies
- samhsa-41caf92d2e New Brunswick Counseling Center: no phone number
- samhsa-548e35f1ad Cooperative Counseling Services — Outpatient Program: no phone number
- possible same place in two sources: Rutgers RWJ Eric B. Chandler Health Center / HIPHOP Promise Clinic (student-run) (277 George St)
- Always show 988 (Suicide & Crisis Lifeline) next to mental health results

## Summary
- behavioral_health: 14
- mental_health: 12
- fqhc: 9
- substance_use: 4
- opioid_treatment: 1
- free_clinic: 1
- hospital_clinic: 1
- accepts Medicaid: 37
- sliding fee: 26
- Spanish spoken: 17
- serves children: 29

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| clinic_id | 100 |
| source | 100 |
| name | 100 |
| organization | 26 |
| clinic_type | 100 |
| address | 98 |
| city | 100 |
| state | 100 |
| zip | 100 |
| county | 100 |
| phone | 95 |
| website | 90 |
| lat | 100 |
| lng | 100 |
| miles_to_nb | 100 |
| location_type | 100 |
| setting | 69 |
| hours_per_week | 24 |
| care_types | 100 |
| service_settings | 100 |
| accepts_medicaid | 98 |
| accepts_medicare | 98 |
| accepts_private_insurance | 98 |
| accepts_self_pay | 98 |
| sliding_fee | 98 |
| free_care | 76 |
| languages | 45 |
| serves_children | 100 |
| serves_adults | 100 |
| emergency_mh | 100 |
| has_dental | 76 |
| walk_in | 2 |
| notes | 10 |
| source_url | 100 |
| last_verified | 100 |
