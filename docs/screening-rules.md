# Screening rules 0.3-hackathon

This change adds two simulation rules to the original seven. Runtime decisions use symptoms and measurements, never case IDs or expected labels. Evaluation fixtures and their answers are unchanged.

Version 0.3 additionally adds R-010 reduced fetal movement, R-011 fatigue with reported pallor, R-012 flagged glucose screening history, R-013 inability to keep fluids, R-014 clear fluid leakage (warning pathways), and R-015 loss of consciousness (critical, already listed in the source data's emergency flags). These are synthetic workflow decisions requiring clinical review, not diagnostic criteria. The original three fixture labels remain for comparison; `risk_level` maps critical to emergency, high-urgency warning to high, other warning to medium, and no match to unassessed. Low is deliberately not inferred.

### Capability crosswalk

The evaluation labels use `maternal_assessment`, absent from the supplied facility vocabulary. For this simulation, a facility meets that generic requirement if it lists antenatal care, postpartum care, or emergency obstetric care. Original facility records are not changed. R-007 fever-only now requests this generic assessment; R-008 requires infection management plus emergency obstetric care. Clinical review of these assumptions is pending. Unknown capabilities never match. All selected facilities must have simulated available status and be in the case's state.

| Rule | Prototype condition (all listed conditions required) | Output | Required facility capabilities |
| --- | --- | --- | --- |
| R-008 | Postpartum, measured temperature at least 38 C, foul-smelling discharge and severe weakness | critical | emergency_obstetric_care, maternal_infection_management |
| R-009 | Reported severe breathlessness | critical | emergency_obstetric_care |

R-008 takes precedence over the existing warning-level fever rule. R-009 does not require chest pain or a vital-sign measurement to trigger. Neither rule diagnoses a condition. Both flow into support matching and consent-gated simulated referral; no messages are sent.

## Basis and limits

The PRD covers maternal infection warning signs and emergency escalation. The runtime dataset's emergency flag list already includes severe breathlessness. [CDC urgent maternal warning signs](https://www.cdc.gov/hearher/maternal-warning-signs/index.html) identifies fever, trouble breathing, and bad-smelling discharge as warning signs requiring immediate medical care. This supports escalation concerns, but does **not** validate our exact compound rule, facility mapping or dataset labels.

R-008's conjunction is deliberately a narrow software scenario, not an exhaustive clinical threshold. Absence of one component does not mean safety. The original fever-only warning classification remains for compatibility with the synthetic baseline, and is not advice to delay care. Other warning signs and missing inputs still need clinical review. All unmatched inputs remain unassessed.

These changes were informed by the known fixtures and therefore measure regression coverage, not independent validation. Clinician-approved protocols and an independent evaluation set are still required before any real use.
