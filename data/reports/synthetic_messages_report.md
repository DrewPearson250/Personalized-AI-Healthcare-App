# Validation report: synthetic_messages
*Run 2026-11-24*

**Result:** PASSED — 1380 rows, 0 errors, 6 warnings

## Counts
- train: 6 raw files, 1080 messages
- test: 2 raw files, 300 messages
- Test messages with a near-duplicate in train (Jaccard >= 0.7): 0

## Errors (block loading)
- none

## Warnings (review)
- very short message: 'broken tooth'
- very short message: 'migraine again'
- very short message: 'irregular periods'
- All messages are AI-generated, not from real users; the test set is too, so scores on it will likely overstate real-world performance. Say so when reporting results
- urgency labels are AI-assigned from message content; use them only for end-to-end evaluation, never to train the urgency model (that uses NHAMCS triage)
- Spot-check 50 messages by hand: fill ok/note in data/synthetic/spot_check.csv

## Summary
| reason group | train | test | train e/u/r |
| --- | --- | --- | --- |
| chest_pain | 40 | 11 | 13/15/12 |
| heart_circulation | 40 | 11 | 7/16/17 |
| breathing_difficulty | 40 | 11 | 12/17/11 |
| cough_cold_flu | 40 | 11 | 1/18/21 |
| fever_infection | 40 | 11 | 10/18/12 |
| abdominal_pain | 40 | 11 | 9/18/13 |
| digestive_upset | 40 | 11 | 2/16/22 |
| dental_mouth | 40 | 11 | 2/12/26 |
| headache | 40 | 11 | 8/13/19 |
| neuro_dizziness_seizure | 40 | 11 | 13/15/12 |
| weakness_fainting | 40 | 11 | 6/18/16 |
| mental_health | 40 | 12 | 8/13/19 |
| allergic_reaction | 40 | 11 | 11/16/13 |
| substance_overdose | 40 | 11 | 14/14/12 |
| eye | 40 | 11 | 7/14/19 |
| ear | 40 | 11 | 0/15/25 |
| urinary_kidney | 40 | 11 | 4/19/17 |
| pregnancy_womens_health | 40 | 11 | 5/13/22 |
| skin | 40 | 11 | 2/14/24 |
| back_neck_pain | 40 | 11 | 4/12/24 |
| joint_limb_pain | 40 | 11 | 1/15/24 |
| diabetes_blood_sugar | 40 | 11 | 7/14/19 |
| collapse_unresponsive | 40 | 11 | 30/10/0 |
| head_injury | 40 | 11 | 11/18/11 |
| bites_stings | 40 | 11 | 6/16/18 |
| injury_other | 40 | 12 | 9/19/12 |
| other_general | 40 | 12 | 0/13/27 |

Messages per prompt:
- test-caregiver: 55
- test-formal: 54
- test-question: 56
- test-runon: 27
- test-spanish: 54
- test-textspeak: 54
- train-misspelled: 189
- train-older: 189
- train-parent: 162
- train-rambling: 189
- train-short: 189
- train-spanglish: 162

Urgency overall: routine 591, urgent 523, emergency 266

## Coverage (% of rows filled)
| column | % |
| --- | --- |
| message_id | 100 |
| text | 100 |
| reason_group | 100 |
| urgency | 100 |
| prompt_id | 100 |
| split | 100 |
| n_words | 100 |
| generator | 100 |
| created | 100 |
