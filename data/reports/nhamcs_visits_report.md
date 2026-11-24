# Validation report: nhamcs_visits
*Run 2026-11-24*

**Result:** PASSED — 9774 rows, 0 errors, 3 warnings

## Counts
- NHAMCS 2022 ED: 16,025 visits read
- Triage level (IMMEDR): blank 364, unknown 3,788, no triage reported 587, immediate 139, emergent 1,595, urgent 5,340, semi-urgent 2,826, nonurgent 307, ED doesn't triage 1,079
- Kept 10,207 visits with a triage level 1-5
- Dropped 433 visits whose first reason isn't a symptom/injury group: treatment/refill/follow-up 190, exam/screening 95, test results 85, administrative 31, uncodable 26, blank/other 6
- Admitted to hospital by urgency class: emergency 34.0%, routine 2.1%, urgent 13.3%

## Errors (block loading)
- none

## Warnings (review)
- pain_score missing for 2,845 visits (29%); the model must handle a missing pain score (the questionnaire may also skip it)
- reason group diabetes_blood_sugar: only 22 visits; urgency estimates will be noisy (combine 2019-2022 files if needed)
- Triage nurses also used vital signs and an exam; the model only sees reason, age and pain, so report that as a known limit. NHAMCS 2022 is national, not NJ-specific

## Summary
Visits by urgency (sample count, weighted national estimate):
- emergency: 1,655 visits, ~16.5 million
- urgent: 5,163 visits, ~49.9 million
- routine: 2,956 visits, ~31.1 million

| reason group | visits | % emergency | % urgent | % routine |
| --- | --- | --- | --- | --- |
| joint_limb_pain | 955 | 6 | 46 | 49 |
| abdominal_pain | 892 | 8 | 82 | 10 |
| cough_cold_flu | 875 | 6 | 39 | 54 |
| injury_other | 776 | 14 | 39 | 47 |
| digestive_upset | 644 | 9 | 67 | 24 |
| breathing_difficulty | 540 | 37 | 54 | 10 |
| mental_health | 530 | 49 | 37 | 14 |
| chest_pain | 521 | 38 | 57 | 5 |
| fever_infection | 400 | 8 | 50 | 42 |
| neuro_dizziness_seizure | 395 | 31 | 58 | 11 |
| back_neck_pain | 381 | 6 | 49 | 45 |
| head_injury | 320 | 15 | 44 | 40 |
| urinary_kidney | 298 | 12 | 71 | 17 |
| other_general | 289 | 14 | 55 | 30 |
| headache | 287 | 9 | 63 | 28 |
| weakness_fainting | 280 | 25 | 68 | 7 |
| skin | 262 | 5 | 40 | 55 |
| pregnancy_womens_health | 253 | 9 | 72 | 19 |
| heart_circulation | 218 | 40 | 50 | 10 |
| eye | 136 | 18 | 28 | 54 |
| substance_overdose | 122 | 35 | 54 | 11 |
| ear | 122 | 2 | 20 | 77 |
| bites_stings | 91 | 7 | 35 | 58 |
| dental_mouth | 75 | 4 | 31 | 65 |
| collapse_unresponsive | 49 | 69 | 29 | 2 |
| allergic_reaction | 41 | 32 | 54 | 15 |
| diabetes_blood_sugar | 22 | 27 | 59 | 14 |

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| visit_id | 100 |
| age | 100 |
| age_group | 100 |
| sex | 100 |
| pain_score | 71 |
| arrived_by_ambulance | 98 |
| rfv1_code | 100 |
| reason_group | 100 |
| reason_label | 100 |
| rfv2_group | 66 |
| rfv3_group | 43 |
| triage_level | 100 |
| urgency | 100 |
| injury_related | 32 |
| admitted | 100 |
| left_without_seen | 100 |
| died_in_ed | 100 |
| patwt | 100 |
| cstratm | 100 |
| cpsum | 100 |
| source | 100 |
| source_url | 100 |
