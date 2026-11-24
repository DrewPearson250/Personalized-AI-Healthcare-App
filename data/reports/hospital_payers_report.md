# Validation report: hospital_payers
*Run 2026-11-24*

**Result:** PASSED — 193 rows, 0 errors, 4 warnings

## Counts
- 310038 Robert Wood Johnson University Hospital: 1,521,373 charge rows scanned, 35 payer+plan pairs, file version 3.0.0, last updated 2026-03-04
- 310039 Raritan Bay Medical Center: 5,640,873 charge rows scanned, 42 payer+plan pairs, file version 3.0.0, last updated 2025-12-31
- 310070 Saint Peter's University Hospital: 489,387 charge rows scanned, 48 payer+plan pairs, file version 3.0.0, last updated 1/8/2026
- 310108 JFK University Medical Center: 6,464,964 charge rows scanned, 47 payer+plan pairs, file version 3.0.0, last updated 2025-12-31
- 313300 Children's Specialized Hospital: 22,294 charge rows scanned, 21 payer+plan pairs, file version 3.0.0, last updated 2026-03-04

## Errors (block loading)
- none

## Warnings (review)
- 310010 University Medical Center Of Princeton At Plainsboro: no price file (see fetch_price_transparency.py)
- 314011 University Behavioral Health Care: no price file (see fetch_price_transparency.py)
- 34 payer+plan pairs with no brand mapping (shown under the payer name): ACTIVECARE FIRST MCO; All Other; BERGEN RISK; BRIGHTON HEALTH PLAN; Commercial; Emblem Health; First Health; INTERGROUP; Managed Care Other; No Fault; PRIME HEALTH; SEOUL MEDICAL GROUP; Self Pay; UBH; VACCN; Workman's Comp
- product (commercial / medicaid / medicare) is a keyword guess from payer and plan names; check the ones the app shows

## Summary
- 310038: 35 pairs, brands: Aetna, AmeriHealth, Cigna, Clover Health, Horizon, Humana, QualCare, UnitedHealthcare, WellCare, Wellpoint/Anthem
- 310039: 42 pairs, brands: Aetna, AmeriHealth, Braven Health, Cigna, Clover Health, Horizon, Medicare, MultiPlan, NJ Medicaid (fee-for-service), QualCare, UnitedHealthcare, WellCare, Wellpoint/Anthem
- 310070: 48 pairs, brands: Aetna, AmeriHealth, Braven Health, Cigna, Horizon, MagnaCare, Medicare, MultiPlan, NJ Medicaid (fee-for-service), Oscar, QualCare, UnitedHealthcare, WellCare, Wellpoint/Anthem
- 310108: 47 pairs, brands: Aetna, AmeriHealth, Braven Health, Cigna, Clover Health, Horizon, Medicare, MultiPlan, NJ Medicaid (fee-for-service), QualCare, UnitedHealthcare, WellCare, Wellpoint/Anthem
- 313300: 21 pairs, brands: Aetna, AmeriHealth, Cigna, Horizon, QualCare, UnitedHealthcare, WellCare, Wellpoint/Anthem

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| payer_id | 100 |
| facility_id | 100 |
| payer_name | 100 |
| plan_name | 100 |
| brand | 82 |
| product | 100 |
| charge_rows | 100 |
| file_last_updated | 100 |
| source_url | 100 |
| last_verified | 100 |
