# Validation report: services
*Run 2026-11-24*

**Result:** PASSED — 110 rows, 0 errors, 17 warnings

## Counts
- Hand-built services: 23 rows
- Food guide: 99 entries extracted
- Dropped 12 outside Middlesex County: Plainfield Action Services (Plainfield, not geocoded, not a Middlesex place); Pantry (Plainfield); SHILOH Soup Kitchen (Plainfield); Community Church of God (Plainfield); New Covenant Church of God (Plainfield); Greater Refuge Church of Christ (Plainfield); MUSLIM COMMUNITY SOUP KITCHEN (Plainfield); Salvation Army, Plainfield Corps (Plainfield); El Centro Hispanoamericano (Plainfield); S.H.E.E.L.D. (The Lord's Kitchen) (Plainfield); Metropolitan Community Service - Metropolitan SDA Church of Plainfield (Plainfield); Crescent Avenue Presbyterian Church (Plainfield)
- Dropped 0 over 15 miles

## Errors (block loading)
- none

## Warnings (review)
- address didn't geocode, kept without distance: St. Vincent DePaul Food Pantry (230 New Brunswick Ave., Perth Amboy)
- address didn't geocode, kept without distance: PRAHD - Puerto Rican Association for Human Development (98 1st Street, Perth Amboy)
- address didn't geocode, kept without distance: St. Lawrence Roman Catholic Church (109 Laurence Parkway, South Amboy)
- address didn't geocode, kept without distance: Muslim Center of Middlesex County (1000 Hoes Lane, Piscataway)
- address didn't geocode, kept without distance: South Brunswick Township Food Pantry (540 Ridge Rd, Social Services Office, Monmouth Junction)
- address didn't geocode, kept without distance: Grace For Dinner at Grace Presbyterian Church (57 Sand Hills Road, South Brunswick)
- address didn't geocode, kept without distance: Jewish Family Services of Middlesex County, Monroe (1600 Perrineville Road, Suite 52 (Concordia Shopping Center), Monroe)
- food-new-beginnings-church-of-the-nazarene-80-jefferson: address auto-split from a merged PDF entry, check
- food-guardian-angels-church-society-of-st-vincent-de-pa: address auto-split from a merged PDF entry, check
- food-legacy-church-inc-264-whitehead-ave: address auto-split from a merged PDF entry, check
- food-st-james-church-food-bank-174-grove-street: address auto-split from a merged PDF entry, check
- food-heaven-s-helpers-food-pantry-393-pearl-street: address auto-split from a merged PDF entry, check
- food-monroe-township-office-of-aging-12-halsey-reed-roa: address auto-split from a merged PDF entry, check
- food-south-brunswick-township-food-pantry-540-ridge-rd-: no phone number
- 87 food entries come from the Spring 2025 Rutgers guide: hours change often, re-check before launch
- verified = false for all 110 rows: a person must check each against its source_url (catalog rule: hand-built lists get a human check)
- Set aside (sites blocked automated reading, add by hand later; see current_stage.md): Middlesex County Board of Social Services, Woman Aware (local DV program), Coming Home of Middlesex, Central Jersey Legal Services

## Summary
- food: 88
- prescriptions: 4
- mental_health: 4
- transportation: 4
- benefits: 3
- other: 2
- domestic_violence: 1
- legal: 1
- immigrant: 1
- housing: 1
- utilities: 1
- statewide (no address): 12

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| service_id | 100 |
| name | 100 |
| organization | 100 |
| category | 100 |
| description | 100 |
| eligibility | 23 |
| address | 86 |
| city | 88 |
| zip | 83 |
| phone | 98 |
| hours | 77 |
| languages | 4 |
| cost | 95 |
| documents_needed | 35 |
| nearest_bus_stop | 78 |
| lat | 80 |
| lng | 80 |
| miles_to_nb | 80 |
| scope | 100 |
| embed_text | 100 |
| verified | 100 |
| notes | 5 |
| source_url | 100 |
| source_date | 79 |
| last_verified | 100 |
