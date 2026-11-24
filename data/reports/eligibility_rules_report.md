# Validation report: eligibility_rules
*Run 2026-11-24*

**Result:** PASSED — 0 errors, 0 warnings

## Checks
- poverty table steps by $5,680 per person: ok
- NJ FamilyCare children: 355% FPL, household 4 = $9,763/month (page says $9,763)
- NJ FamilyCare adults, 1 person: 138% FPL, household 1 = $1,836/month (page says $1,836)
- NJ FamilyCare adults, couple: 138% FPL, household 2 = $2,489/month (page says $2,489)
- NJ FamilyCare pregnant: 205% FPL, household 4 = $5,638/month (page says $5,638)
- charity_care bands contiguous: 6 bands
- silver_csr bands contiguous: 3 bands
- links.yaml: 11 entries

## Errors (block loading)
- none

## Warnings (review)
- none

## Worked examples
- $20,000/yr, household 1: 125% FPL -> adult NJ FamilyCare yes, children yes, Charity Care patient pays 0%
- $45,000/yr, household 4: 136% FPL -> adult NJ FamilyCare yes, children yes, Charity Care patient pays 0%
- $60,000/yr, household 3: 220% FPL -> adult NJ FamilyCare no, children yes, Charity Care patient pays 20%
