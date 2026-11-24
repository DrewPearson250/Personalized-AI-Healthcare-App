# Validation report: symptom_text
*Run 2026-11-24*

**Result:** PASSED — 1060 rows, 0 errors, 2 warnings

## Counts
- Read 1,065 rows (853 train, 212 test), 22 diagnoses
- Dropped 4 exact duplicate texts within a split
- Dropped 1 test texts that also appear in train (leakage)
- Source: https://huggingface.co/datasets/gretelai/symptom_to_diagnosis (Apache 2.0)

## Errors (block loading)
- none

## Warnings (review)
- 14 of 27 reason groups have no text here (AI-generated messages must cover them): bites_stings, chest_pain, collapse_unresponsive, dental_mouth, ear, eye, head_injury, injury_other, mental_health, neuro_dizziness_seizure, other_general, pregnancy_womens_health, substance_overdose, weakness_fainting
- Texts are written in a patient voice but by a model (Gretel), short and tidy; real messages will be messier (typos, Spanish-English mix)

## Summary
| reason group | train | test | diagnoses |
| --- | --- | --- | --- |
| abdominal_pain | 37 | 10 | peptic ulcer disease |
| allergic_reaction | 80 | 18 | allergy, drug reaction |
| back_neck_pain | 39 | 10 | cervical spondylosis |
| breathing_difficulty | 76 | 20 | bronchial asthma, pneumonia |
| cough_cold_flu | 39 | 10 | common cold |
| diabetes_blood_sugar | 40 | 10 | diabetes |
| digestive_upset | 70 | 16 | gastroesophageal reflux disease, jaundice |
| fever_infection | 118 | 29 | dengue, malaria, typhoid |
| headache | 32 | 10 | migraine |
| heart_circulation | 40 | 10 | hypertension |
| joint_limb_pain | 80 | 20 | arthritis, varicose veins |
| skin | 159 | 39 | chicken pox, fungal infection, impetigo, psoriasis |
| urinary_kidney | 39 | 9 | urinary tract infection |

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| text_id | 100 |
| text | 100 |
| diagnosis | 100 |
| split | 100 |
| reason_group | 100 |
| n_words | 100 |
