# Validation report: plan_rates
*Run 2026-11-24*

**Result:** PASSED — 3978 rows, 0 errors, 5 warnings

## Counts
- Rates: 4182 rows read
- Rates for plans sold in Middlesex: 3978
- 91661NJ2310001: listed in 6 rating areas at identical prices
- 91661NJ2310003: listed in 6 rating areas at identical prices
- 91661NJ2310004: listed in 6 rating areas at identical prices

## Errors (block loading)
- none

## Warnings (review)
- 35152NJ0010003: $0 premium for ages 19-64 (1 rating area(s)) -> stored as NULL (not offered at that age)
- 35152NJ0010004: $0 premium for ages 19-64 (1 rating area(s)) -> stored as NULL (not offered at that age)
- 91661NJ2310001: $0 premium for ages 19-64 (6 rating area(s)) -> stored as NULL (not offered at that age)
- 99708NJ0120020: $0 premium for ages 19-64 (1 rating area(s)) -> stored as NULL (not offered at that age)
- 99708NJ0120021: $0 premium for ages 19-64 (1 rating area(s)) -> stored as NULL (not offered at that age)

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| rate_id | 100 |
| standard_component_id | 100 |
| issuer_id | 100 |
| rating_area | 100 |
| age | 100 |
| age_label | 100 |
| monthly_premium | 88 |
| tobacco_premium | 8 |
| rate_effective | 100 |
| rate_expiration | 100 |
| source_url | 100 |
| last_verified | 100 |
