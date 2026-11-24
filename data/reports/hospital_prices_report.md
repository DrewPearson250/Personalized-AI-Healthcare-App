# Validation report: hospital_prices
*Run 2026-11-24*

**Result:** PASSED — 8026 rows, 0 errors, 6 warnings

## Counts
- 310038: 2,024 rows for the 30 common services
- 310039: 3,382 rows for the 30 common services
- 310070: 14,308 rows for the 30 common services
- 310108: 3,630 rows for the 30 common services
- 313300: 513 rows for the 30 common services
- 15831 repeated rows dropped (same code, setting, billing class, modifiers, payer, plan and the same prices)

## Errors (block loading)
- none

## Warnings (review)
- 310010 University Medical Center Of Princeton At Plainsboro: no price file (see fetch_price_transparency.py)
- 314011 University Behavioral Health Care: no price file (see fetch_price_transparency.py)
- 4159 rows share code/setting/payer/plan but list different prices (different chargemaster items); all kept, show the range
- 310070: no rows for 4 services: 59400, 59510, 81001, 93000
- 313300: no rows for 14 services: 59400, 59409, 59510, 59514, 71046, 72148, 76805, 77067, 93000, 99281, 99282, 99283, 99284, 99285
- Cash prices are the hospital's listed self-pay rate before Charity Care; physician fees are usually billed separately

## Cash prices
Lowest listed cash price per service ($):

| code | service | 310038 | 310039 | 310070 | 310108 | 313300 |
| --- | --- | --- | --- | --- | --- | --- |
| 36415 | Blood draw | 10 | 9 | 15 | 9 | 29 |
| 59400 | Vaginal delivery with prenatal and postpartum care | 5,741 |  |  |  |  |
| 59409 | Vaginal delivery only | 5,741 | 3,522 | 2,100 | 3,522 |  |
| 59510 | Cesarean delivery with prenatal and postpartum care | 5,741 |  |  |  |  |
| 59514 | Cesarean delivery only | 5,741 |  | 1,490 |  |  |
| 70450 | CT head/brain without contrast | 445 | 118 | 1,068 | 118 | 640 |
| 71046 | Chest X-ray, 2 views | 109 | 98 | 194 | 98 |  |
| 72148 | MRI lower back without contrast | 609 | 268 | 1,304 | 268 |  |
| 73030 | Shoulder X-ray |  | 98 | 242 | 98 | 117 |
| 73610 | Ankle X-ray |  | 98 | 38 | 98 | 126 |
| 74177 | CT abdomen and pelvis with contrast | 769 | 396 | 1,350 | 396 | 2,084 |
| 76700 | Abdominal ultrasound | 233 | 118 | 816 | 118 | 363 |
| 76805 | Pregnancy ultrasound | 199 | 118 | 626 | 118 |  |
| 77067 | Screening mammogram | 135 | 169 | 198 | 169 |  |
| 80053 | Comprehensive metabolic panel (blood test) | 12 | 11 | 122 | 11 | 32 |
| 80061 | Cholesterol (lipid) panel | 15 | 13 | 8 | 13 | 65 |
| 81001 | Urinalysis | 3 | 3 |  | 3 | 24 |
| 83036 | Hemoglobin A1c (diabetes test) | 11 | 10 | 3 | 10 | 67 |
| 85025 | Complete blood count (CBC) | 9 | 8 | 204 | 8 | 25 |
| 90471 | Vaccine administration | 60 | 79 | 57 | 79 | 39 |
| 93000 | Electrocardiogram (EKG) | 33 |  |  |  |  |
| 99202 | Office visit, new patient (15-29 min) | 83 |  | 32 |  | 256 |
| 99203 | Office visit, new patient (30-44 min) | 123 |  | 49 |  | 300 |
| 99213 | Office visit, established patient (20-29 min) | 109 |  | 78 |  | 224 |
| 99214 | Office visit, established patient (30-39 min) | 120 |  | 86 |  | 304 |
| 99281 | ER visit, level 1 (minor) | 224 | 98 | 280 | 98 |  |
| 99282 | ER visit, level 2 | 459 | 175 | 345 | 175 |  |
| 99283 | ER visit, level 3 (moderate) | 641 | 307 | 394 | 307 |  |
| 99284 | ER visit, level 4 (high) | 668 | 472 | 620 | 472 |  |
| 99285 | ER visit, level 5 (severe) | 1,102 | 679 | 908 | 679 |  |

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| price_id | 100 |
| facility_id | 100 |
| code | 100 |
| service | 100 |
| service_group | 100 |
| description_raw | 100 |
| setting | 100 |
| billing_class | 72 |
| modifiers | 1 |
| gross_charge | 93 |
| discounted_cash | 88 |
| min_negotiated | 96 |
| max_negotiated | 96 |
| payer_name | 100 |
| plan_name | 100 |
| brand | 83 |
| negotiated_dollar | 95 |
| negotiated_percentage | 58 |
| methodology | 100 |
| file_last_updated | 100 |
| source_url | 100 |
| last_verified | 100 |
