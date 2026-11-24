# AI-generated messages: prompts

Written by Claude (claude-opus-5-5) in a Claude Code session on 2026-11-24, per the dataset
catalog ("AI-generated labeled messages"). Not written by real users.

Each message is a short first message a New Brunswick, NJ resident might type into the app's
free-text box. Labels:
- `reason_group`: one of the 27 groups in `config/reason_groups.yaml` (the group's label and
  description were the brief for each block of messages).
- `urgency`: emergency / urgent / routine, assigned by the writer from the message content
  (red flags -> emergency). These are AI-assigned labels for end-to-end evaluation only; the
  urgency model trains on real NHAMCS triage, not on these.
- `prompt_id`: the style prompt below.

Severity varies inside each group on purpose, so the group alone doesn't give away urgency.

## Training prompts (data/synthetic/raw/train_*.txt)

| prompt_id | Instruction |
|---|---|
| train-short | 3-12 words, like typing fast into a search box. |
| train-rambling | 2-4 sentences with backstory and worry, some irrelevant detail. |
| train-misspelled | Casual, lowercase, typos and phonetic spellings, little punctuation. |
| train-spanglish | Mix of Spanish and English in one message, as a bilingual speaker would write. |
| train-parent | A parent or guardian writing about their child (infant to teen), mention the age. |
| train-older | An older adult (60+) writing about themselves, may mention age, meds or conditions. |

## Test prompts (data/synthetic/raw/test.txt), deliberately different

| prompt_id | Instruction |
|---|---|
| test-textspeak | Text-message style: abbreviations (u, rn, idk, smh), no capitals, emoji words. |
| test-caregiver | Someone writing about another adult (partner, parent, roommate, coworker). |
| test-formal | Polite, complete sentences, like an email to a clinic. |
| test-question | Framed as a question ("is it normal that...", "should I..."). |
| test-spanish | Mostly or fully Spanish. |
| test-runon | One long run-on sentence with no punctuation. |

## Spot check

`scripts/build_synthetic.py` draws a fixed random sample of 50 for a human to check labels
(`data/synthetic/spot_check.csv`, fill the `ok` and `note` columns). Because the test set is
also AI-generated, scores on it will likely overstate real-world performance: say so whenever
results are reported, and swap in real messages once the app has users.
