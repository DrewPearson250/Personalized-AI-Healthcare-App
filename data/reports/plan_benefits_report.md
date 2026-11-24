# Validation report: plan_benefits
*Run 2026-11-24*

**Result:** PASSED — 2854 rows, 0 errors, 0 warnings

## Counts
- Benefits: 12156 rows read
- Rows for standard plan variants sold in Middlesex: 2854 (CSR variants have the same covered services, only cost sharing differs)
- Medical plans covering 'Routine Dental Services (Adult)': 0 of 39
- Medical plans covering 'Routine Eye Exam (Adult)': 0 of 39
- Medical plans covering 'Dental Check-Up for Children': 6 of 39

## Errors (block loading)
- none

## Warnings (review)
- none

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| benefit_id | 100 |
| plan_id | 100 |
| benefit_name | 100 |
| is_covered | 100 |
| is_ehb | 100 |
| quantity_limit | 38 |
| limit_quantity | 13 |
| limit_unit | 13 |
| exclusions | 9 |
| explanation | 42 |
| subject_to_deductible | 0 |
| source_url | 100 |
| last_verified | 100 |
