# MAMA-Link Synthetic Dataset Pack

This pack mirrors the data contracts used by the Microsoft FrontierWeekHack repository while adapting them to the MAMA-Link maternal-health scenario.

## Important safety note
All people, facilities, organizations, symptoms combinations, labels, and outcomes in this package are synthetic. This dataset is for software prototyping, Foundry agent testing, tracing, and evaluation only. It is not a clinical protocol, medical device dataset, or source of medical advice.

## Repository mapping

FrontierWeekHack pattern -> MAMA-Link file

- `factory/challenge-1-build/sensor_data.json` -> `maternal/challenge-1-build/maternal_data.json`
- Runtime-safe variant (no answer leakage) -> `maternal/challenge-1-build/maternal_data_runtime.json`
- `factory/challenge-3-evaluate/eval_portal.jsonl` -> `maternal/challenge-3-evaluate/eval_portal.jsonl`
- Ground-truth labels for deterministic metrics -> `maternal/challenge-3-evaluate/ground_truth_labels.json`
- `factory/challenge-4-deploy/evaluation_dataset.json` -> `maternal/challenge-4-deploy/evaluation_dataset.json`
- Additional tool datasets -> `maternal/data/facilities.json`, `support_resources.json`, `screening_rules.json`

## Status labels

- `normal`: no emergency red flag in the synthetic scenario; routine pathway
- `warning`: requires clinician review / referral support but is not labelled as the highest emergency class in this prototype
- `critical`: emergency escalation pathway

These labels are intentionally software-oriented and must not be treated as validated clinical triage categories.

## Recommended use

1. Use `maternal_data_runtime.json` as the data your agent/tool sees.
2. Keep `status`, expected outputs, and `ground_truth_labels.json` out of the model context during evaluation.
3. Use `eval_portal.jsonl` for Foundry portal evaluation.
4. Use `evaluation_dataset.json` for code-based evaluation / workflow tests.
5. Use `facilities.json` and `support_resources.json` through custom tools rather than embedding them in system prompts.
6. Version the rules and evaluation dataset together.

## Clinical grounding used to design synthetic scenarios

The test cases were shaped around public high-level maternal-health information from WHO and UNFPA, including:
- pre-eclampsia screening concepts and severe symptoms;
- haemorrhage, hypertensive disorders, infection and obstructed labour as major maternal risks;
- prolonged obstructed labour as a major cause of obstetric fistula;
- persistent urine/faecal leakage as a symptom requiring fistula assessment.

Before any real-world deployment, replace these simplified rules and labels with protocols reviewed and approved by qualified maternal-health clinicians and the relevant health authorities.
