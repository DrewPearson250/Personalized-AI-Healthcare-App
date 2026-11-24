# Validation report: plans
*Run 2026-11-24*

**Result:** PASSED — 126 rows, 0 errors, 2 warnings

## Counts
- Service areas: 262 rows; plans: 204 plan variants
- Service areas serving Middlesex (county row or whole state): 23
- Plan variants in those service areas: 200 (4 dropped, service area doesn't reach Middlesex)
- Dropped 74 zero/limited cost-sharing variants (tribal members only)
- Median silver deductible by variant: csr_73 $2,250, csr_87 $800, csr_94 $100, standard $2,500
- Medical plans (standard variants): 39 from 5 insurers; Silver 21, Expanded Bronze 9, Gold 7, Catastrophic 2
- Dental-only plans: 24

## Errors (block loading)
- none

## Warnings (review)
- Premiums and deductibles are full price before financial help; the subsidy is calculated by Get Covered NJ. Plan brochure/SBC/formulary URLs are empty in the file, so link to Get Covered NJ
- cost_having_baby / cost_diabetes / cost_simple_fracture = sum of the SBC deductible + copay + coinsurance + limit amounts (the 'Coverage Examples' total)

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| plan_id | 100 |
| standard_component_id | 100 |
| issuer_id | 100 |
| issuer_name | 100 |
| plan_name | 100 |
| variant_name | 100 |
| dental_only | 100 |
| plan_type | 100 |
| metal_level | 100 |
| csr_variant | 100 |
| actuarial_value_pct | 75 |
| deductible_individual | 80 |
| deductible_family | 73 |
| coinsurance_pct | 61 |
| moop_individual | 100 |
| moop_family | 100 |
| hsa_eligible | 81 |
| referral_required | 81 |
| out_of_network_coverage | 100 |
| child_only_offering | 100 |
| cost_having_baby | 81 |
| cost_diabetes | 81 |
| cost_simple_fracture | 81 |
| plan_year | 100 |
| enroll_url | 100 |
| source_url | 100 |
| last_verified | 100 |
