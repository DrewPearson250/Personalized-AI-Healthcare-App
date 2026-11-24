# Validation report: insurers_local
*Run 2026-11-24*

**Result:** PASSED — 18 rows, 0 errors, 2 warnings

## Counts
- DOBI: 1191 rows read (long format, all counties)
- Dropped 3 insurers with 0 Middlesex enrollment: American National Life Ins Co of NY, Oxford Health Plans of NJ, Inc, Wellpoint Life & Health Ins Co (formerly UniCare)
- Middlesex total_enrollment: sum 235,700 vs DOBI total 235,700
- Middlesex commercial_network: sum 96,103 vs DOBI total 96,103
- Middlesex commercial_non_network: sum 285 vs DOBI total 285
- Middlesex medicaid_enrollment: sum 139,312 vs DOBI total 139,312
- Medicaid (NJ FamilyCare) plans in Middlesex: Horizon HC of NJ, Inc 80,421, AmeriChoice 31,639, Aetna Better Health Inc. 10,028, AmeriGroup (Wellpoint) 9,988, WellCare Health Plans of New Jersey, Inc. 7,236

## Errors (block loading)
- none

## Warnings (review)
- no brand mapping (shown under their legal name): Nippon Life Ins Co, Nationwide Life Insurance Company, ShelterPoint Life Ins Co (formerly First Rehab)
- Counts include out-of-state residents who work in NJ (DOBI note)

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| insurer_id | 100 |
| insurer_name | 100 |
| naic | 100 |
| brand | 100 |
| marketplace_issuer_id | 50 |
| total_enrollment | 100 |
| commercial_enrollment | 100 |
| commercial_network | 100 |
| commercial_non_network | 100 |
| medicaid_enrollment | 100 |
| is_medicaid_plan | 100 |
| share_of_county_pct | 100 |
| rank | 100 |
| brand_rank | 100 |
| quarter | 100 |
| source_url | 100 |
| last_verified | 100 |
